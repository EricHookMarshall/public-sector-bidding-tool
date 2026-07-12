#!/usr/bin/env python3
"""
JSON API for the Public Sector Bidding PoC.

Reads the shared bids.db store (db.py — SQLite locally, SQL Server via DB_URL)
and exposes it to the React UI. No HTML here — this is a pure JSON API; the
Vite/React app in web/ renders it.

Endpoints (representative — the full set spans all six journey stages; see the
@app routes below): the Search stage reads

  GET /api/meta                  filter options (sources, statuses, countries,
                                 regions, currencies, value bounds) + freshness.
  GET /api/opportunities         filtered/searched list (raw_json omitted).
  GET /api/opportunities/{id}    one full record (raw_json parsed back to JSON).

Run:  uvicorn api:app --reload --port 8000
      (or: python3 api.py)
"""
import csv
import datetime
import io
import json
import logging
import math
import os
import re
from contextlib import asynccontextmanager

log = logging.getLogger("api")


def _load_dotenv():
    """Load src/.env into os.environ if present (no dependency). Real keys
    live here, not in git — .env is git-ignored. Existing env vars win, so an
    explicit `export` still overrides the file."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()

from fastapi import Body, Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator

import bidplan as P
import clarification as M
import compliance as CMP
import compliance_store as CSTORE
import config as app_config
import complete_ai
import cpv_catalog
import db
import library as LIB
import outcome as L
import qualification as Q
import response as R
import regions
import sources
import triage_ai
from auth import auth_status, require_auth, require_roles
from llm import LLMUnavailable, get_provider

@asynccontextmanager
async def lifespan(app):
    """Create/back-fill the schema ONCE at startup rather than per request. On
    sqlite the old per-request init_db was cheap; against Azure SQL it was a set
    of extra network round-trips (create_all + an inspector query) on every call."""
    conn = db.connect()
    try:
        db.init_db(conn)
        _bootstrap_compliance_register(conn)
    finally:
        conn.close()
    yield


def get_conn():
    """Per-request DB connection as a FastAPI dependency. The try/finally is the
    point: handlers that raise (404/409/…) mid-request no longer leak the
    connection — which is invisible locally (sqlite + GC forgive it) but exhausts
    the pool against Azure SQL. The schema is created at startup (lifespan), so
    this no longer runs init_db on the hot path."""
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


# Azure-migration Phase C: every /api/* route is guarded by the Entra ID auth
# dependency (auth.py). Declared app-wide here so no route can forget it; routes
# that want the caller's identity re-declare `Depends(require_auth)` (cached
# per-request). LOCAL_AUTH_BYPASS=1 makes this a no-op for offline/PoC dev.
app = FastAPI(
    title="Public Sector Bidding API",
    version="0.1.0",
    dependencies=[Depends(require_auth)],
    lifespan=lifespan,
)

# CORS. Local PoC: the Vite dev server (5173) calls this API (8000). In Azure the
# SWA is a separate origin, so the allowed list is env-driven (CORS_ALLOWED_ORIGINS,
# comma-separated) and falls back to localhost for dev. Authorization header must
# pass through for the Bearer token — covered by allow_headers=["*"].
_DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
_cors_env = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
_allowed_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] or _DEFAULT_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Fields returned in list view (everything except the heavy raw payload).
LIST_FIELDS = [f for f in db.COMMON_FIELDS if f != "raw_json"]


def _json_safe(obj):
    """Replace non-finite floats (inf/nan) with None — some source payloads
    carry values like inf, which the JSON encoder rejects."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


def _derive_open(deadline_date):
    """open / closed / unknown, derived from the bid deadline vs. now (UTC).
    Thin alias over db.derive_lifecycle — the shared source refresh_clean writes
    the persisted flag from, so the live API and the stored flag can't disagree."""
    return db.derive_lifecycle(deadline_date)


def _row_to_dict(row, include_raw=False):
    rec = dict(row)
    # Numeric coercion for value fields so the UI can sort/range-filter.
    for f in ("value_min", "value_max"):
        if rec.get(f) not in (None, ""):
            try:
                rec[f] = float(rec[f])
            except (TypeError, ValueError):
                rec[f] = None
    rec["bid_status"] = _derive_open(rec.get("deadline_date"))
    # Human-readable region name for codes like "UKM50" (None-safe; passes
    # through place names unchanged). Lets the UI show "what UKM50 means vs UK".
    rec["region_label"] = regions.label(rec.get("region"))
    if include_raw and rec.get("raw_json"):
        try:
            rec["raw_json"] = _json_safe(json.loads(rec["raw_json"]))
        except (TypeError, ValueError):
            pass
    return rec


def _require_opp(conn, opp_id):
    """Fetch an opportunity row or raise 404 — the existence guard the stage
    endpoints repeat. Callers that only need the guard can ignore the return."""
    row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="opportunity not found")
    return row


def _require_bid(conn, bid_id):
    """Fetch a bid row or raise 404 — the bid-existence counterpart of _require_opp."""
    row = conn.execute("SELECT * FROM bids WHERE id = ?", (bid_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="bid not found")
    return row


@app.get("/api/meta")
def meta(conn=Depends(get_conn)):
    """Distinct filter values + value bounds + per-source freshness."""

    def distinct(col):
        # SAFETY: `col` is interpolated into the SQL, so it MUST be an internal
        # literal (see the call sites below) — never a request-derived value.
        # Every caller passes a hard-coded column name; do not relax that.
        rows = conn.execute(
            f"SELECT DISTINCT {col} AS v FROM opportunities "
            f"WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col}"
        ).fetchall()
        return [r["v"] for r in rows]

    bounds = conn.execute(
        "SELECT MIN(CAST(value_min AS REAL)) AS lo, MAX(CAST(value_max AS REAL)) AS hi "
        "FROM opportunities WHERE value_max IS NOT NULL AND value_max != ''"
    ).fetchone()

    runs = conn.execute(
        "SELECT source, source_endpoint, MAX(checked_at) AS checked_at, "
        "scanned, kept FROM source_runs GROUP BY source ORDER BY source"
    ).fetchall()

    total, by_source = db.counts(conn)

    # Materialise everything that touches a _Row into plain dicts/values here —
    # the get_conn dependency closes the connection after we return, and Row
    # access after close raises "Cannot operate on a closed database".
    payload = {
        "fields": LIST_FIELDS,
        "total": total,
        "by_source": [{"source": s, "count": n} for s, n in by_source],
        "sources": distinct("source"),
        "statuses": distinct("status"),
        "countries": distinct("country"),
        "regions": distinct("region"),
        "currencies": distinct("currency"),
        "notice_types": distinct("notice_type"),
        "lifecycles": distinct("lifecycle"),
        "value_bounds": {"min": bounds["lo"], "max": bounds["hi"]},
        "source_runs": [dict(r) for r in runs],
        # Options that drive the UI's live-search form (toggleable sources,
        # stages, default CPV scope) + the team's persisted starting defaults
        # (S3) so the form opens pre-tuned + a glossary for the region codes.
        "search_options": {**sources.options(), "defaults": _search_defaults(conn)},
        "cpv_catalog": cpv_catalog.catalog(),
        "region_labels": regions.labels_for(distinct("region")),
        # Non-secret auth posture (Phase C) — lets ops/the SPA confirm whether
        # Entra sign-in is expected or the bypass shim is active.
        "auth": auth_status(),
    }
    return payload


def _query_opportunities(conn, *, q, source, status, bid_status, lifecycle,
                         country, region, currency, notice_type,
                         min_value, max_value, sort, order):
    """Shared filter/search query used by both the list view and CSV export, so
    'export' always matches exactly what the user is looking at."""
    where, params = [], []
    if q:
        like = f"%{q}%"
        where.append(
            "(title LIKE ? OR buyer_name LIKE ? OR description LIKE ? OR cpv_codes LIKE ?)"
        )
        params += [like, like, like, like]
    for col, val in [
        ("source", source), ("status", status), ("country", country),
        ("region", region), ("currency", currency), ("notice_type", notice_type),
        ("lifecycle", lifecycle),
    ]:
        if val:
            where.append(f"{col} = ?")
            params.append(val)
    if min_value is not None:
        where.append("CAST(value_max AS REAL) >= ?")
        params.append(min_value)
    if max_value is not None:
        where.append("CAST(value_min AS REAL) <= ?")
        params.append(max_value)

    sort_col = sort if sort in db.COMMON_FIELDS else "deadline_date"
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    sql = (
        f"SELECT id, {', '.join(LIST_FIELDS)}, lifecycle FROM opportunities{clause} "
        f"ORDER BY {sort_col} {'DESC' if order == 'desc' else 'ASC'}"
    )
    rows = conn.execute(sql, params).fetchall()
    results = [_row_to_dict(r) for r in rows]
    # Derived bid_status is computed post-query, so filter it here.
    if bid_status:
        results = [r for r in results if r["bid_status"] == bid_status]
    return results


# Query params shared by /api/opportunities and /api/export, declared once.
def _list_params(
    q: str | None = Query(None, description="keyword search (title/buyer/description/cpv)"),
    source: str | None = None,
    status: str | None = None,
    bid_status: str | None = Query(None, description="open / closed / unknown (derived)"),
    lifecycle: str | None = Query(None, description="open / closed / unknown / stale (persisted by refresh_clean.py)"),
    country: str | None = None,
    region: str | None = None,
    currency: str | None = None,
    notice_type: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    sort: str = Query("deadline_date", description="any list field"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
):
    return dict(
        q=q, source=source, status=status, bid_status=bid_status, lifecycle=lifecycle,
        country=country, region=region, currency=currency, notice_type=notice_type,
        min_value=min_value, max_value=max_value, sort=sort, order=order,
    )


@app.get("/api/opportunities")
def list_opportunities(params: dict = Depends(_list_params), conn=Depends(get_conn)):
    results = _query_opportunities(conn, **params)
    return {"count": len(results), "results": results}


# Cell prefixes a spreadsheet may interpret as a formula. Upstream notice text is
# attacker-influenceable, so a value like `=HYPERLINK(...)` must not be exported
# raw — Excel/Sheets would execute it on open. We neutralise by prefixing a `'`.
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value):
    """Neutralise spreadsheet formula injection in a CSV cell. Non-strings pass
    through; a string starting with a formula-trigger character is prefixed with a
    single quote so the spreadsheet treats it as literal text."""
    if isinstance(value, str) and value.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


# Fields written to the CSV export, in a readable order (raw_json excluded).
EXPORT_FIELDS = [
    "id", "source", "title", "buyer_name", "status", "bid_status", "lifecycle",
    "notice_type", "cpv_codes", "region", "region_label", "country",
    "value_min", "value_max", "currency", "published_date", "deadline_date",
    "ocid", "notice_id", "url", "description", "last_seen_at",
]


@app.get("/api/export")
def export_csv(params: dict = Depends(_list_params), conn=Depends(get_conn)):
    """Download the current (filtered) result set as CSV — same query as the
    list view, so the export mirrors exactly what's on screen."""
    results = _query_opportunities(conn, **params)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for r in results:
        writer.writerow({k: _csv_safe(r.get(k, "")) for k in EXPORT_FIELDS})
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="opportunities.csv"'},
    )


# Guard rails on the live-search request: each source runs a synchronous external
# fetch, so unbounded days / CPV lists / free-form dates are both a workload and an
# injection risk. Cap the window, the list size, and validate the shape here (→ 422)
# rather than letting a huge or malformed request reach the connectors.
_MAX_SEARCH_DAYS = 365
_MAX_CPV_CODES = 50


class SearchRequest(BaseModel):
    sources: list[str]                       # registry keys to run (sources.SOURCES)
    cpv_codes: list[str] | None = None       # None → connector default scope
    stage: str = "tender"
    open_only: bool = True
    # rolling window if no explicit dates — bounded to a sane range
    days: int = Field(120, ge=1, le=_MAX_SEARCH_DAYS)
    published_from: str | None = None        # ISO date/datetime; overrides `days`
    published_to: str | None = None

    @field_validator("stage")
    @classmethod
    def _known_stage(cls, v):
        if v not in sources.STAGES:
            raise ValueError(f"unknown stage: {v!r} (expected one of {sources.STAGES})")
        return v

    @field_validator("cpv_codes")
    @classmethod
    def _bounded_cpv(cls, v):
        if v is None:
            return v
        if len(v) > _MAX_CPV_CODES:
            raise ValueError(f"too many cpv_codes (max {_MAX_CPV_CODES})")
        for c in v:
            if not c.isdigit() or len(c) > 10:
                raise ValueError(f"invalid cpv code: {c!r} (expected up to 10 digits)")
        return v

    @field_validator("published_from", "published_to")
    @classmethod
    def _iso_date(cls, v):
        if v in (None, ""):
            return v
        try:
            datetime.datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"invalid ISO date/datetime: {v!r}") from e
        return v


@app.post("/api/search")
def search(req: SearchRequest):
    """Run a live search: fan out to the selected connectors with the given
    CPV / stage / date params, upsert what they find into bids.db, and report a
    per-source summary. This is what makes the UI's search controls actually
    drive the upstream fetch (not just filter stored rows).

    Each source runs in isolation — one source erroring (e.g. CF rate-limited)
    is reported as an error for that source but doesn't abort the others.
    """
    unknown = [k for k in req.sources if k not in sources.SOURCES]
    if unknown:
        raise HTTPException(status_code=400, detail=f"unknown source(s): {', '.join(unknown)}")
    if not req.sources:
        raise HTTPException(status_code=400, detail="select at least one source")

    runs = []
    for key in req.sources:
        entry = sources.SOURCES[key]
        try:
            res = entry["run"](
                days=req.days,
                cpv_codes=req.cpv_codes or None,
                stage=req.stage,
                open_only=req.open_only,
                published_from=req.published_from,
                published_to=req.published_to,
                use_db=True,
            )
            runs.append({
                "key": key, "source": entry["name"], "ok": True,
                "scanned": res["scanned"], "kept": res["kept"],
                "inserted": res["inserted"], "updated": res["updated"],
            })
        except Exception:  # noqa: BLE001 — surface any source failure, keep going
            # Log the full exception context server-side (type, message, traceback,
            # which could carry upstream URLs/paths/request data) but return only a
            # stable, generic message to the client so nothing internal leaks.
            log.exception("live search failed for source %s", key)
            runs.append({
                "key": key, "source": entry["name"], "ok": False,
                "error": "source fetch failed",
            })

    total_kept = sum(r.get("kept", 0) for r in runs if r["ok"])
    return {"runs": runs, "total_kept": total_kept}


# ---- Stage 2: Triage / FOR001 qualification -------------------------------

# Opportunity → qualification pre-fill: the fields FWF re-keys from a notice into
# FOR001 when it first triages. We seed them so the triager edits rather than
# retypes. (source column on the opportunity → qualification field.)
_QUAL_SEED_FROM_OPP = {
    "client_name": "buyer_name",
    "summary": "title",
    "scope_summary": "scope_summary",       # enrichment, if triaged already
    "estimated_value": "value_max",
    "clarification_deadline": "clarification_deadline",
    "submission_deadline": "deadline_date",
    "framework": "opportunity_type",
}


def _seed_qualification(opp):
    """A blank FOR001 pre-filled from the opportunity — never persisted until
    the user saves. `opp` is the _row_to_dict of the opportunity."""
    seed = {f: None for f in db.QUALIFICATION_FIELDS}
    for qual_field, opp_field in _QUAL_SEED_FROM_OPP.items():
        val = opp.get(opp_field)
        seed[qual_field] = str(val) if val not in (None, "") else None
    # The FOR001 fixed role set, zero-count, ready for the triager to fill.
    seed["delivery_team"] = [{"role": r, "count": 0, "comments": ""} for r in Q.DELIVERY_ROLES]
    seed["win_qualification_rag"] = {}
    return seed


def _day_rates(conn):
    """The team's configured bid day rates (from app_settings), merged over the
    FOR001 defaults. Drives every 'cost to chase' calculation."""
    return Q.resolve_day_rates(db.get_setting(conn, "day_rates"))


def _team_capacity(conn):
    """The team's bid-writing capacity (person-days over the horizon) from
    app_settings, or the FOR002 default if unset/invalid."""
    stored = db.get_setting(conn, "team_capacity_days")
    try:
        v = float(stored)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    return P.DEFAULT_TEAM_CAPACITY_DAYS


def _team_roster(conn):
    """The team roster (people who own bids/phases/clarifications) from
    app_settings — a cleaned list of names, or [] if unset/invalid. Fed to the
    owner dropdowns on Plan and Manage so a novice picks a real person, not a
    free-typed role."""
    stored = db.get_setting(conn, "team_roster")
    if not isinstance(stored, list):
        return []
    seen, people = set(), []
    for name in stored:
        if not isinstance(name, str):
            continue
        clean = name.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            people.append(clean)
    return people


# Live-search defaults (app_settings) — the team's pre-tuned starting point for
# the "Run a live search" form, so a novice isn't handed the raw code defaults.
_SEARCH_DAYS_MIN, _SEARCH_DAYS_MAX = 1, 365
_CPV_RE = re.compile(r"\d{2,8}")


def _search_defaults_code():
    """The built-in live-search defaults (all sources, the reference CPV scope,
    live tender stage, open-only, a 120-day window) — the fallback baseline."""
    return {
        "sources": list(sources.SOURCES),
        "cpv_codes": list(sources.DEFAULT_CPV),
        "stage": sources.STAGES[0],
        "open_only": True,
        "days": 120,
    }


def _search_defaults(conn):
    """The team's persisted live-search defaults merged over the code baseline.
    Every stored value is re-validated against the current source/stage registry
    so a stale or hand-corrupted setting can't wedge the search form — an invalid
    field silently falls back rather than blocking the search."""
    base = _search_defaults_code()
    stored = db.get_setting(conn, "search_defaults")
    if not isinstance(stored, dict):
        return base

    src = [k for k in stored.get("sources", []) if k in sources.SOURCES]
    if src:
        base["sources"] = src
    cpv = [c for c in stored.get("cpv_codes", [])
           if isinstance(c, str) and _CPV_RE.fullmatch(c)]
    if cpv:
        base["cpv_codes"] = cpv
    if stored.get("stage") in sources.STAGES:
        base["stage"] = stored["stage"]
    if isinstance(stored.get("open_only"), bool):
        base["open_only"] = stored["open_only"]
    try:
        d = int(stored.get("days"))
        if _SEARCH_DAYS_MIN <= d <= _SEARCH_DAYS_MAX:
            base["days"] = d
    except (TypeError, ValueError):
        pass
    return base


# AI prompt settings (app_settings) — the editable context the drafts run with.
_AI_PROMPT_KEYS = ("ai_profile", "ai_triage_guidance", "ai_complete_guidance",
                   "ai_triage_template")


def _ai_prompts(conn):
    """The stored AI prompt overrides (raw values; blanks mean 'use the default').
    The draft functions apply the profile default themselves via resolve_profile."""
    return {k: (db.get_setting(conn, k) or "") for k in _AI_PROMPT_KEYS}


def _qualification_payload(conn, opp_id):
    """Assemble the Triage view for one opportunity: the qualification (saved or
    seeded), whether it's been saved, the live bid economics, and any spun-off
    bid. Shared by the GET and the post-save response so both return one shape."""
    opp = _row_to_dict(_require_opp(conn, opp_id))

    qual = db.get_qualification(conn, opp_id)
    saved = qual is not None
    if not saved:
        qual = _seed_qualification(opp)

    return {
        "opportunity": {
            "id": opp_id, "title": opp.get("title"), "buyer_name": opp.get("buyer_name"),
            "source": opp.get("source"), "deadline_date": opp.get("deadline_date"),
            "clarification_deadline": opp.get("clarification_deadline"),
            "value_max": opp.get("value_max"), "currency": opp.get("currency"),
            "url": opp.get("url"),
        },
        "qualification": qual,
        "saved": saved,
        "economics": Q.compute_bid_economics(qual.get("complexity"), _day_rates(conn)),
        "bid": db.get_bid_for_opportunity(conn, opp_id),
    }


@app.get("/api/triage/board")
def triage_board(conn=Depends(get_conn)):
    """The opportunities pulled into Triage, each with its state — enriched so a
    card can show where it stands: untriaged, decided (Go / No go / needs-review),
    and whether it's a live bid. Ordered by submission deadline (soonest first),
    plus a funnel summary.

    Membership is an explicit pull: Search is the full universe, and an opp only
    lands here once the user picks it (triage_selections) — OR once it's already
    been worked (has a qualification or a bid), so this gate never hides an
    existing decision."""
    opps = _query_opportunities(
        conn, q=None, source=None, status=None, bid_status=None, lifecycle=None,
        country=None, region=None, currency=None, notice_type=None,
        min_value=None, max_value=None, sort="deadline_date", order="asc")
    states, bid_stage = db.list_triage_states(conn)
    selected = db.selected_opportunity_ids(conn)
    dismissed = db.dismissed_opportunity_ids(conn)

    def state_key(triaged, decision, has_bid):
        # Mutually exclusive; must match the frontend's triageState precedence
        # (bid-live wins over the raw Go decision) so the funnel counts equal
        # what each filter chip actually shows.
        if has_bid:
            return "bids"
        if decision == "Go":
            return "go"
        if decision == "No go":
            return "no_go"
        if triaged:
            return "review"
        return "untriaged"

    items = []
    for o in opps:
        st = states.get(o["id"])
        triaged = st is not None
        decision = (st or {}).get("decision", "")
        has_bid = o["id"] in bid_stage
        # The pull gate: show only opps the user selected into Triage, plus any
        # already worked (qualification saved or bid promoted) so decisions never
        # vanish. Everything else stays in Search until explicitly picked.
        if o["id"] not in selected and not triaged and not has_bid:
            continue
        items.append({
            **o,
            "triaged": triaged,
            "decision": decision,
            "complexity": (st or {}).get("complexity", ""),
            "rag_label": (st or {}).get("rag_label", ""),
            "rag_rating": (st or {}).get("rag_rating"),
            "bid_stage": bid_stage.get(o["id"]),
            "dismissed": o["id"] in dismissed,
            "state": state_key(triaged, decision, has_bid),
        })

    # Funnel counts are over ACTIVE (non-dismissed) items — that's what the state
    # chips filter — with a separate dismissed count for the "Dismissed" chip.
    summary = {"total": 0, "untriaged": 0, "review": 0,
               "go": 0, "no_go": 0, "bids": 0, "dismissed": 0}
    for i in items:
        if i["dismissed"]:
            summary["dismissed"] += 1
        else:
            summary["total"] += 1
            summary[i["state"]] += 1
    return {"items": items, "summary": summary}


class TriageSelectUpdate(BaseModel):
    selected: bool


@app.put("/api/opportunities/{opp_id}/triage-select")
def set_triage_select(opp_id: int, body: TriageSelectUpdate, conn=Depends(get_conn)):
    """Pull an opportunity into the Triage board (the "Triage this →" handoff from
    Search), or remove it. Selection only controls Triage membership — the opp
    stays in Search and the DB either way. 404 if the opportunity doesn't exist."""
    _require_opp(conn, opp_id)
    state = db.set_triage_selected(conn, opp_id, body.selected)
    return {"opportunity_id": opp_id, "selected": state}


class TriageDismissUpdate(BaseModel):
    dismissed: bool


@app.put("/api/opportunities/{opp_id}/triage-dismiss")
def set_triage_dismiss(opp_id: int, body: TriageDismissUpdate, conn=Depends(get_conn)):
    """Reversibly dismiss an opportunity from the Triage board, or restore it.
    Dismissal only hides it from Triage — it stays in Search and the DB. 404 if
    the opportunity doesn't exist."""
    _require_opp(conn, opp_id)
    state = db.set_triage_dismissed(conn, opp_id, body.dismissed)
    return {"opportunity_id": opp_id, "dismissed": state}


@app.get("/api/triage/reference")
def triage_reference(conn=Depends(get_conn)):
    """FOR001 vocabulary (complexity levels, day-rate table, pricing models,
    delivery roles, RAG criteria, economics-by-complexity) for the Triage form.
    Economics reflect the team's configured day rates (Settings)."""
    return Q.reference(_day_rates(conn))


@app.get("/api/opportunities/{opp_id}/qualification")
def get_qualification(opp_id: int, conn=Depends(get_conn)):
    return _qualification_payload(conn, opp_id)


# ---- Settings: LLM config ---------------------------------------------------

@app.get("/api/auth/me")
def auth_me(identity=Depends(require_auth)):
    """The signed-in caller's identity, for the SPA to render role-aware UI (e.g.
    hide the Admin-only Settings gear). Non-secret — role + display name + email,
    all already inside the validated token (or the bypass shim). The API still
    enforces every gate server-side; this only drives presentation."""
    return {
        "role": identity.role,
        "display_name": identity.display_name,
        "email": identity.email,
        "via": identity.via,
    }


@app.get("/api/config")
def get_config():
    """Current LLM settings for the Settings screen. Never returns the API key —
    only whether it's set + its last 4 chars."""
    return app_config.current()


class ConfigUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None   # write-only; blank/omitted leaves the stored key untouched


@app.put("/api/config", dependencies=[Depends(require_roles("Admin"))])
def put_config(body: ConfigUpdate):
    """Persist LLM settings to the git-ignored src/.env (and live env). Validates
    provider/model against the known options so the screen can't set unbuilt ones."""
    updates = {}
    if body.provider:
        if body.provider not in app_config.AVAILABLE_PROVIDERS:
            raise HTTPException(status_code=400, detail=f"provider '{body.provider}' is not available yet")
        updates["LLM_PROVIDER"] = body.provider
    if body.model:
        if body.model not in app_config.MODEL_IDS:
            raise HTTPException(status_code=400, detail=f"unknown model '{body.model}'")
        updates["ANTHROPIC_MODEL"] = body.model
    if body.api_key and body.api_key.strip():
        updates["ANTHROPIC_API_KEY"] = body.api_key.strip()
    try:
        app_config.upsert_env(updates)
    except app_config.ConfigReadOnly as e:
        # Azure: config is platform-managed, not writable here — 409, not a 500.
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        # e.g. a control character in a value — reject as bad input, not a 500.
        raise HTTPException(status_code=400, detail=str(e))
    return app_config.current()


@app.post("/api/config/test", dependencies=[Depends(require_roles("Admin"))])
def test_config():
    """Do a cheap live round-trip with the current settings to verify the key +
    model actually work. 503 with the reason if not."""
    try:
        result = get_provider().ping()
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"ok": True, **result}


def _day_rates_payload(conn):
    """The Settings shape for bid day rates: the role list, the resolved rates
    (defaults merged with any override), and the FOR001 default for reference."""
    return {
        "roles": Q.DAY_RATE_ROLES,
        "rates": _day_rates(conn),
        "default_rate": Q.DAY_RATE,
        "note": "Applies to each qualification's 'cost to chase' when it's next "
                "saved; existing bids keep the cost snapshotted at their last save.",
    }


@app.get("/api/settings/day-rates")
def get_day_rates(conn=Depends(get_conn)):
    """The team's bid-writing day rates (per FOR001 role) for the Settings screen."""
    return _day_rates_payload(conn)


class DayRatesUpdate(BaseModel):
    rates: dict[str, float]   # {role: £/day}; unknown roles ignored, non-positive rejected


@app.put("/api/settings/day-rates", dependencies=[Depends(require_roles("Admin"))])
def put_day_rates(body: DayRatesUpdate, conn=Depends(get_conn)):
    """Persist per-role day rates to app_settings (bids.db). Validates every rate is
    a positive number and every role is a known FOR001 role, so the store can't hold
    a value that would poison the economics later."""
    clean = {}
    for role, rate in (body.rates or {}).items():
        if role not in Q.DAY_RATE_ROLES:
            raise HTTPException(status_code=400, detail=f"unknown role '{role}'")
        if not isinstance(rate, (int, float)) or rate <= 0:
            raise HTTPException(status_code=400, detail=f"day rate for '{role}' must be a positive number")
        clean[role] = float(rate)
    db.set_setting(conn, "day_rates", clean)
    return _day_rates_payload(conn)


def _team_capacity_payload(conn):
    """The Settings shape for team capacity: the current value + the FOR002 default."""
    return {
        "capacity_days": _team_capacity(conn),
        "default": P.DEFAULT_TEAM_CAPACITY_DAYS,
        "note": "Total bid-writing person-days the team can commit over the planning "
                "horizon. The Plan board measures committed effort against this and "
                "warns when the team is over-committed.",
    }


@app.get("/api/settings/team-capacity")
def get_team_capacity(conn=Depends(get_conn)):
    """The team's configured bid-writing capacity for the Settings screen."""
    return _team_capacity_payload(conn)


class TeamCapacityUpdate(BaseModel):
    capacity_days: float


@app.put("/api/settings/team-capacity", dependencies=[Depends(require_roles("Admin"))])
def put_team_capacity(body: TeamCapacityUpdate, conn=Depends(get_conn)):
    """Persist the team's capacity to app_settings (bids.db). Must be positive."""
    if body.capacity_days <= 0:
        raise HTTPException(status_code=400, detail="capacity must be a positive number of days")
    db.set_setting(conn, "team_capacity_days", body.capacity_days)
    return _team_capacity_payload(conn)


# Team roster — the people who own bids, phases and clarifications. Kept small
# and generous: a list of names, no roles or emails (a PoC, single-team tool).
_ROSTER_MAX_PEOPLE = 100
_ROSTER_MAX_NAME_LEN = 80


def _team_roster_payload(conn):
    """The Settings shape for the team roster: the current people list + a note."""
    return {
        "people": _team_roster(conn),
        "note": "The people who own bids, plan phases and clarifications. These "
                "names fill the owner dropdowns on Plan and Manage, so a missed "
                "clarification always has a named owner to chase.",
    }


@app.get("/api/settings/team-roster")
def get_team_roster(conn=Depends(get_conn)):
    """The team roster (people) for the Settings screen."""
    return _team_roster_payload(conn)


class TeamRosterUpdate(BaseModel):
    people: list[str]


@app.put("/api/settings/team-roster", dependencies=[Depends(require_roles("Admin"))])
def put_team_roster(body: TeamRosterUpdate, conn=Depends(get_conn)):
    """Persist the team roster to app_settings (bids.db). Names are trimmed,
    blanks dropped and duplicates removed (case-insensitive); order is kept."""
    seen, people = set(), []
    for raw in body.people:
        clean = raw.strip()
        if len(clean) > _ROSTER_MAX_NAME_LEN:
            raise HTTPException(status_code=400, detail=f"a name exceeds {_ROSTER_MAX_NAME_LEN} characters")
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            people.append(clean)
    if len(people) > _ROSTER_MAX_PEOPLE:
        raise HTTPException(status_code=400, detail=f"the roster is capped at {_ROSTER_MAX_PEOPLE} people")
    db.set_setting(conn, "team_roster", people)
    return _team_roster_payload(conn)


def _search_defaults_payload(conn):
    """The Settings shape for live-search defaults: the effective defaults, the
    code baseline (for a Reset), and the option lists the card renders from."""
    return {
        "defaults": _search_defaults(conn),
        "code_defaults": _search_defaults_code(),
        "sources": [{"key": k, "name": v["name"], "note": v.get("note", "")}
                    for k, v in sources.SOURCES.items()],
        "stages": list(sources.STAGES),
        "cpv_catalog": cpv_catalog.catalog(),
        "days_range": {"min": _SEARCH_DAYS_MIN, "max": _SEARCH_DAYS_MAX},
        "note": "The starting point for the 'Run a live search' form on Search. "
                "Set the CPV scope, sources, stage and window your team searches "
                "most, so a novice runs the right search without tuning it first.",
    }


@app.get("/api/settings/search-defaults")
def get_search_defaults(conn=Depends(get_conn)):
    """The team's live-search defaults for the Settings screen."""
    return _search_defaults_payload(conn)


class SearchDefaultsUpdate(BaseModel):
    # All optional — send only what changed; omitted fields keep their value.
    sources: list[str] | None = None
    cpv_codes: list[str] | None = None
    stage: str | None = None
    open_only: bool | None = None
    days: int | None = None


@app.put("/api/settings/search-defaults", dependencies=[Depends(require_roles("Admin"))])
def put_search_defaults(body: SearchDefaultsUpdate, conn=Depends(get_conn)):
    """Persist live-search defaults to app_settings (bids.db). Overlays the given
    fields on the current defaults; unlike the read-time resolver this validates
    strictly (bad input → 400) so the user gets feedback, then stores the full
    resolved object so it's self-contained."""
    resolved = _search_defaults(conn)

    if body.sources is not None:
        unknown = [k for k in body.sources if k not in sources.SOURCES]
        if unknown:
            raise HTTPException(status_code=400, detail=f"unknown source(s): {', '.join(unknown)}")
        if not body.sources:
            raise HTTPException(status_code=400, detail="select at least one source")
        # de-dupe, keep order
        resolved["sources"] = list(dict.fromkeys(body.sources))

    if body.cpv_codes is not None:
        bad = [c for c in body.cpv_codes if not _CPV_RE.fullmatch(str(c))]
        if bad:
            raise HTTPException(status_code=400, detail=f"CPV codes must be 2–8 digits: {', '.join(map(str, bad))}")
        if not body.cpv_codes:
            raise HTTPException(status_code=400, detail="keep at least one CPV code in scope")
        resolved["cpv_codes"] = list(dict.fromkeys(str(c) for c in body.cpv_codes))

    if body.stage is not None:
        if body.stage not in sources.STAGES:
            raise HTTPException(status_code=400, detail=f"unknown stage: {body.stage}")
        resolved["stage"] = body.stage

    if body.open_only is not None:
        resolved["open_only"] = body.open_only

    if body.days is not None:
        if not (_SEARCH_DAYS_MIN <= body.days <= _SEARCH_DAYS_MAX):
            raise HTTPException(
                400, f"days must be between {_SEARCH_DAYS_MIN} and {_SEARCH_DAYS_MAX}")
        resolved["days"] = body.days

    db.set_setting(conn, "search_defaults", resolved)
    return _search_defaults_payload(conn)


def _ai_prompts_payload(conn):
    """The Settings shape for AI prompts: the stored overrides plus the built-in
    default profile, so the screen can show/reset to it. Guidance fields default
    to empty (no extra instructions)."""
    stored = _ai_prompts(conn)
    return {
        "profile": stored["ai_profile"],
        "profile_default": triage_ai.DEFAULT_FWF_PROFILE,
        "triage_guidance": stored["ai_triage_guidance"],
        "complete_guidance": stored["ai_complete_guidance"],
        # The full Triage extraction template (advanced) + what it renders with.
        "triage_template": stored["ai_triage_template"],
        "triage_template_default": triage_ai.DEFAULT_TRIAGE_TEMPLATE,
        "triage_template_tokens": triage_ai.TRIAGE_TEMPLATE_TOKENS,
        "note": "The profile is the AI's context for Triage and Complete drafts. "
                "Guidance is optional house-style, appended to each draft prompt. "
                "The data (opportunity, question, library) is always supplied by the app.",
    }


@app.get("/api/settings/ai-prompts")
def get_ai_prompts(conn=Depends(get_conn)):
    """The editable AI prompt context (profile + per-stage guidance) for Settings."""
    return _ai_prompts_payload(conn)


_AI_PROMPT_MAXLEN = 8000


class AiPromptsUpdate(BaseModel):
    # All optional — send only what changed. Blank profile/template fall back to
    # their built-in defaults.
    profile: str | None = None
    triage_guidance: str | None = None
    complete_guidance: str | None = None
    triage_template: str | None = None


@app.put("/api/settings/ai-prompts", dependencies=[Depends(require_roles("Admin"))])
def put_ai_prompts(body: AiPromptsUpdate, conn=Depends(get_conn)):
    """Persist AI prompt overrides to app_settings (bids.db). Length-capped; the
    values are prose (no templating), so no other validation is needed — a blank
    profile simply resolves back to the built-in default at draft time."""
    # A non-blank template must keep the load-bearing data token(s), else the draft
    # would run with no opportunity to extract from. A blank clears it → default.
    if body.triage_template is not None and body.triage_template.strip():
        missing = triage_ai.missing_triage_tokens(body.triage_template)
        if missing:
            raise HTTPException(
                400, f"extraction template is missing required token(s): {', '.join(missing)}")

    mapping = {
        "ai_profile": body.profile,
        "ai_triage_guidance": body.triage_guidance,
        "ai_complete_guidance": body.complete_guidance,
        "ai_triage_template": body.triage_template,
    }
    for key, val in mapping.items():
        if val is None:
            continue  # omitted → leave the stored value untouched
        if len(val) > _AI_PROMPT_MAXLEN:
            raise HTTPException(status_code=400, detail=f"{key} exceeds {_AI_PROMPT_MAXLEN} characters")
        db.set_setting(conn, key, val.strip())
    return _ai_prompts_payload(conn)


@app.post("/api/opportunities/{opp_id}/qualification/ai-draft")
def ai_draft_qualification(opp_id: int, conn=Depends(get_conn)):
    """AI-draft the FOR001 qualification from the opportunity notice (Stage-2
    pre-fill). Returns a *draft* + the AI's rationale — never saved; the UI puts
    it in the form for human review. 503 (not a crash) if no LLM is configured,
    so the manual Triage flow keeps working."""
    # materialise the Row (region_label etc.) before the LLM call
    opp = _row_to_dict(_require_opp(conn, opp_id))
    prompts = _ai_prompts(conn)
    try:
        draft, meta = triage_ai.draft_qualification(
            opp, profile=prompts["ai_profile"], guidance=prompts["ai_triage_guidance"],
            template=prompts["ai_triage_template"])
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=f"AI drafting unavailable: {e}")
    return {"draft": draft, "meta": meta}


@app.put("/api/opportunities/{opp_id}/qualification")
def save_qualification(opp_id: int, body: dict = Body(default_factory=dict), conn=Depends(get_conn)):
    """Save (create or update) the FOR001 qualification for an opportunity.

    Derived fields are recomputed server-side from the authoritative rig, never
    trusted from the client: `estimated_bid_effort_days`/`estimated_bid_cost`
    from `complexity`, and `rag_summary_rating`/`rag_summary_label` from
    `win_qualification_rag`. A `decision == "Go"` promotes the opportunity into a
    Bid (the spine); the response mirrors GET so the UI can re-render in place.
    """
    _require_opp(conn, opp_id)

    fields = {k: v for k, v in body.items() if k in db.QUALIFICATION_FIELDS}

    # Recompute derived fields against whatever the effective complexity / RAG is
    # after this save (payload value if present, else the stored one).
    existing = db.get_qualification(conn, opp_id) or {}
    complexity = fields.get("complexity", existing.get("complexity"))
    # Snapshot the cost against the day rates in force now (see db.py QUALIFICATION_FIELDS).
    econ = Q.compute_bid_economics(complexity, _day_rates(conn))
    fields["estimated_bid_effort_days"] = econ["effort_days"]
    fields["estimated_bid_cost"] = econ["cost"]

    rag = fields.get("win_qualification_rag", existing.get("win_qualification_rag"))
    rating, label = Q.rag_summary(rag)
    fields["rag_summary_rating"] = rating
    fields["rag_summary_label"] = label

    qid = db.upsert_qualification(conn, opp_id, fields)

    # A Go decision spins up the bid spine that later stages attach to.
    decision = fields.get("decision", existing.get("decision"))
    if decision == "Go":
        # Only the title is needed here, and the opportunity's existence was already
        # verified above — so fetch just that one column rather than the whole row.
        opp_title = conn.execute(
            "SELECT title FROM opportunities WHERE id = ?", (opp_id,)).fetchone()[0]
        bid_name = fields.get("client_name") or existing.get("client_name") or opp_title
        db.create_bid_from_qualification(conn, opp_id, qid, bid_name)

    return _qualification_payload(conn, opp_id)


# ---- Stage 3: Plan / FOR002 bid plan --------------------------------------

def _num(v):
    """Coerce a stored TEXT number back to float (SQLite keeps numbers as text in
    our TEXT columns), or None if blank/unparseable."""
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _board_item(row):
    """One board card from a raw joined bid row (db.list_bids_for_board). Adds the
    derived fields the board reads: pipeline stage (defaulted for an un-planned
    bid), the single authoritative clarification deadline, and days-to-deadline."""
    # Clarification deadline: the opportunity enrichment is authoritative; fall
    # back to the one captured on the FOR001 qualification. Distinct from the
    # submission deadline on purpose — losing track of it is the founding failure.
    clar = row.get("opp_clarification_deadline") or row.get("qual_clarification_deadline")
    value = _num(row.get("estimated_value")) or _num(row.get("value_max"))
    return {
        "bid_id": row["bid_id"],
        "opportunity_id": row["opportunity_id"],
        "title": row.get("title") or row.get("bid_name"),
        "buyer_name": row.get("buyer_name"),
        "url": row.get("url"),
        "currency": row.get("currency") or "GBP",
        # A bid with no saved plan sits in the first column until planned.
        "pipeline_stage": row.get("pipeline_stage") or P.PIPELINE_STAGES[0],
        "owner": row.get("owner") or "",
        "target_submission": row.get("target_submission") or "",
        "submission_deadline": row.get("submission_deadline"),
        "clarification_deadline": clar,
        "days_to_submission": P.days_until(row.get("submission_deadline")),
        "days_to_clarification": P.days_until(clar),
        "effort_days": _num(row.get("effort_days")) or 0,
        "cost": _num(row.get("cost")) or 0,
        "value": value,
        "complexity": row.get("complexity"),
    }


@app.get("/api/plan/reference")
def plan_reference(conn=Depends(get_conn)):
    """FOR002 vocabulary (pipeline stages, phase list, owner roles, statuses,
    default capacity) for the Plan board + timeline. The default capacity reflects
    the team's configured Settings value so the board seeds from it."""
    ref = P.reference()
    ref["default_capacity_days"] = _team_capacity(conn)
    ref["roster"] = _team_roster(conn)
    return ref


@app.get("/api/plan/board")
def plan_board(capacity_days: float | None = Query(None,
                                            description="team bid-writing capacity over the horizon; "
                                                        "omitted → the configured Settings value"),
               conn=Depends(get_conn)):
    """The cross-bid Plan board: every live bid with its pipeline position, owner,
    deadlines (days remaining) and 'cost to chase', grouped into pipeline columns,
    plus the team-capacity summary and the computed deadline/owner alerts. This is
    the highest-value view — it answers the missed-deadline failure directly."""
    cap = capacity_days if capacity_days is not None else _team_capacity(conn)
    rows = db.list_bids_for_board(conn)

    items = [_board_item(r) for r in rows]
    columns = [
        {"stage": s, "cards": [it for it in items if it["pipeline_stage"] == s]}
        for s in P.PIPELINE_STAGES
    ]
    return {
        "count": len(items),
        "columns": columns,
        "capacity": P.capacity_summary(items, cap),
        "alerts": P.alerts(items, cap),
    }


def _plan_payload(conn, bid_id):
    """Assemble the Plan detail for one bid: the plan (saved or seeded blank),
    whether it's saved, and the bid/opportunity context the timeline shows."""
    bid = dict(_require_bid(conn, bid_id))
    opp = _row_to_dict(conn.execute(
        "SELECT * FROM opportunities WHERE id = ?", (bid["opportunity_id"],)).fetchone())
    qual = db.get_qualification(conn, bid["opportunity_id"]) or {}

    plan = db.get_bid_plan(conn, bid_id)
    saved = plan is not None
    if not saved:
        plan = {f: None for f in db.BID_PLAN_FIELDS}
        plan["pipeline_stage"] = P.PIPELINE_STAGES[0]
        plan["phases"] = P.default_phases()
    elif not plan.get("phases"):
        plan["phases"] = P.default_phases()

    clar = opp.get("clarification_deadline") or qual.get("clarification_deadline")
    return {
        "bid": {"id": bid_id, "bid_name": bid.get("bid_name"),
                "stage": bid.get("stage"), "status": bid.get("status")},
        "opportunity": {
            "id": opp.get("id"), "title": opp.get("title"),
            "buyer_name": opp.get("buyer_name"), "url": opp.get("url"),
            "submission_deadline": opp.get("deadline_date"),
            "clarification_deadline": clar,
            "value": _num(qual.get("estimated_value")) or _num(opp.get("value_max")),
            "currency": opp.get("currency") or "GBP",
        },
        "economics": {
            "effort_days": _num(qual.get("estimated_bid_effort_days")) or 0,
            "cost": _num(qual.get("estimated_bid_cost")) or 0,
            "complexity": qual.get("complexity"),
        },
        "plan": plan,
        "saved": saved,
    }


@app.get("/api/bids/{bid_id}/plan")
def get_bid_plan(bid_id: int, conn=Depends(get_conn)):
    return _plan_payload(conn, bid_id)


@app.put("/api/bids/{bid_id}/plan")
def save_bid_plan(bid_id: int, body: dict = Body(default_factory=dict), conn=Depends(get_conn)):
    """Save (create or update) the FOR002 bid plan for a bid: pipeline position,
    owner, dates, and the phase timeline. Only BID_PLAN_FIELDS are written; the
    response mirrors GET so the UI can re-render in place."""
    _require_bid(conn, bid_id)

    fields = {k: v for k, v in body.items() if k in db.BID_PLAN_FIELDS}
    db.upsert_bid_plan(conn, bid_id, fields)
    return _plan_payload(conn, bid_id)


# ---- Stage 5: Manage / FOR003 CQLOG + pre-flight gate ---------------------

def _manage_summary(row):
    """One Manage board card from a raw joined bid row (db.list_bids_for_manage).
    Resolves the FOR003 register + pre-flight into the derived fields the board
    reads: open-clarification count, the nearest live clarification deadline, and
    whether the pre-flight gate is clear. The clarification deadline is the
    founding-failure signal — losing track of it is why this tool exists."""
    clars = [M.clarification_view(c) for c in (row.get("clarifications") or [])]
    resolved_pf = M.resolve_preflight(row.get("preflight"), row.get("clarifications"))
    pf = M.preflight_summary(resolved_pf)

    pending = [c for c in clars if c["pending"]]
    # Soonest live clarification deadline (skip the ones with no date set).
    dated = [c for c in pending if c["days_to_deadline"] is not None]
    nearest = min(dated, key=lambda c: c["days_to_deadline"], default=None)
    return {
        "bid_id": row["bid_id"],
        "opportunity_id": row["opportunity_id"],
        "title": row.get("title") or row.get("bid_name"),
        "buyer_name": row.get("buyer_name"),
        "url": row.get("url"),
        "submission_deadline": row.get("submission_deadline"),
        "days_to_submission": P.days_until(row.get("submission_deadline")),
        "clarifications_total": len(clars),
        "clarifications_open": len(pending),
        "next_clarification_deadline": nearest["buyer_deadline"] if nearest else None,
        "days_to_next_clarification": nearest["days_to_deadline"] if nearest else None,
        "preflight": pf,
        "submitted": (row.get("submitted") or "") == "yes",
        # Kept for the alerts pass (they read the per-clarification views + pf).
        "clarifications": clars,
    }


@app.get("/api/manage/reference")
def manage_reference(conn=Depends(get_conn)):
    """FOR003 vocabulary (clarification statuses, the pre-flight checklist
    template, imminent-days) plus the team roster for the owner dropdowns."""
    return {**M.reference(), "roster": _team_roster(conn)}


@app.get("/api/manage/board")
def manage_board(conn=Depends(get_conn)):
    """The cross-bid Manage board: every live bid with its clarification register
    summary and pre-flight readiness, plus the computed clarification-deadline /
    owner / gate alerts (most-urgent first). This answers the missed-clarification
    failure directly — the register whose loss killed the G-Cloud 15 bid."""
    rows = db.list_bids_for_manage(conn)

    items = [_manage_summary(r) for r in rows]
    alerts = M.alerts(items)
    # The per-clarification views were only needed to compute the alerts; drop
    # them from the board payload (the detail view fetches the full register).
    for it in items:
        it.pop("clarifications", None)
    return {"count": len(items), "bids": items, "alerts": alerts}


def _manage_payload(conn, bid_id):
    """Assemble the Manage detail for one bid: the FOR003 register (seeded empty),
    the resolved pre-flight checklist + gate summary, and the bid/opportunity
    context the register shows."""
    bid = dict(_require_bid(conn, bid_id))
    opp = _row_to_dict(conn.execute(
        "SELECT * FROM opportunities WHERE id = ?", (bid["opportunity_id"],)).fetchone())
    qual = db.get_qualification(conn, bid["opportunity_id"]) or {}

    manage = db.get_bid_manage(conn, bid_id)
    saved = manage is not None
    if not saved:
        manage = {f: None for f in db.BID_MANAGE_FIELDS}
    clars = manage.get("clarifications") or []
    preflight_stored = manage.get("preflight") or M.default_preflight()

    resolved_pf = M.resolve_preflight(preflight_stored, clars)
    pf_summary = M.preflight_summary(resolved_pf)
    clar_views = [M.clarification_view(c) for c in clars]

    # The authoritative clarification deadline captured upstream (enrichment wins,
    # else the FOR001 value) — shown as the register's reference cut-off.
    opp_clar = opp.get("clarification_deadline") or qual.get("clarification_deadline")
    return {
        "bid": {"id": bid_id, "bid_name": bid.get("bid_name"),
                "stage": bid.get("stage"), "status": bid.get("status")},
        "opportunity": {
            "id": opp.get("id"), "title": opp.get("title"),
            "buyer_name": opp.get("buyer_name"), "url": opp.get("url"),
            "submission_deadline": opp.get("deadline_date"),
            "clarification_deadline": opp_clar,
            "currency": opp.get("currency") or "GBP",
        },
        "clarifications": clar_views,
        "preflight": resolved_pf,
        "preflight_summary": pf_summary,
        "submitted": (manage.get("submitted") or "") == "yes",
        "submitted_at": manage.get("submitted_at"),
        "notes": manage.get("notes") or "",
        "saved": saved,
    }


@app.get("/api/bids/{bid_id}/manage")
def get_bid_manage(bid_id: int, conn=Depends(get_conn)):
    return _manage_payload(conn, bid_id)


@app.put("/api/bids/{bid_id}/manage")
def save_bid_manage(bid_id: int, body: dict = Body(default_factory=dict), conn=Depends(get_conn)):
    """Save (create or update) the FOR003 manage record for a bid: the
    clarification register, the pre-flight checklist, notes, and the submitted
    flag. Only BID_MANAGE_FIELDS are written. A `submitted == "yes"` is only
    honoured when the pre-flight gate is actually clear — the tool won't let a
    blocked bid be marked submitted (the whole point of the gate). The response
    mirrors GET so the UI can re-render in place."""
    _require_bid(conn, bid_id)

    fields = {k: v for k, v in body.items() if k in db.BID_MANAGE_FIELDS}

    # Normalise the register: keep only known clarification fields per row, so the
    # client can't smuggle extra columns into the JSON blob.
    if isinstance(fields.get("clarifications"), list):
        template = M.default_clarification()
        fields["clarifications"] = [
            {k: c.get(k, template[k]) for k in template}
            for c in fields["clarifications"] if isinstance(c, dict)
        ]
    if isinstance(fields.get("preflight"), list):
        fields["preflight"] = [
            {"key": c.get("key"), "status": c.get("status", ""),
             "note": c.get("note", ""), "expiry_date": c.get("expiry_date", "")}
            for c in fields["preflight"]
            if isinstance(c, dict) and c.get("key") in M.PREFLIGHT_KEYS
        ]

    # The submit gate: honour "yes" only if pre-flight actually clears. Recompute
    # against the effective register/checklist, never trust the client's word.
    if fields.get("submitted") == "yes":
        clars = fields.get("clarifications")
        pf = fields.get("preflight")
        if clars is None or pf is None:
            existing = db.get_bid_manage(conn, bid_id) or {}
            if clars is None:
                clars = existing.get("clarifications") or []
            if pf is None:
                pf = existing.get("preflight") or M.default_preflight()
        summary = M.preflight_summary(M.resolve_preflight(pf, clars))
        if not summary["ready"]:
            raise HTTPException(
                status_code=409,
                detail=f"pre-flight gate blocked: {summary['blocking_count']} item(s) "
                       f"outstanding — resolve them before marking submitted")
        fields["submitted_at"] = db.now_iso()

    db.upsert_bid_manage(conn, bid_id, fields)
    return _manage_payload(conn, bid_id)


# ---- Stage 4: Complete / FOR006 response matrix + library pre-fill --------

def _complete_summary(row):
    """One Complete board card from a raw joined bid row (db.list_bids_for_complete).
    Resolves the FOR006 matrix (or an empty one) into the completion summary the
    board reads: how many questions, how many approved, and any over word limit."""
    items = [R.response_view(it) for it in (row.get("items") or [])]
    summary = R.matrix_summary(items)
    return {
        "bid_id": row["bid_id"],
        "opportunity_id": row["opportunity_id"],
        "title": row.get("title") or row.get("bid_name"),
        "buyer_name": row.get("buyer_name"),
        "url": row.get("url"),
        "submission_deadline": row.get("submission_deadline"),
        "days_to_submission": P.days_until(row.get("submission_deadline")),
        "started": bool(row.get("items")),
        "summary": summary,
    }


@app.get("/api/complete/reference")
def complete_reference():
    """FOR006 vocabulary (response statuses, question types) + the library
    vocabulary (categories, expiry window) for the Complete matrix + library."""
    # imminent_days: the shared "urgent" window (same source Plan/Manage read) so
    # Complete's deadline badges agree on what counts as urgent.
    return {**R.reference(), "library": LIB.reference(), "imminent_days": P.IMMINENT_DAYS}


@app.get("/api/complete/board")
def complete_board(conn=Depends(get_conn)):
    """The cross-bid Complete board: every live bid with its FOR006 matrix
    completion (answered / approved / over-word-limit), plus the shared library
    provider status. Answers 'which bids still have drafting to do' at a glance."""
    rows = db.list_bids_for_complete(conn)

    provider = LIB.get_provider()
    return {
        "count": len(rows),
        "bids": [_complete_summary(r) for r in rows],
        "library": provider.status(),
    }


@app.get("/api/library")
def library_browse(category: str | None = None, q: str | None = None):
    """Browse the shared bid library through the provider seam (LocalMirror now).
    Optional `category` / `q` filter. Also returns the evidence ledger (items with
    an expiry, soonest first) and the provider status — so the UI can show an honest
    'library not connected' state instead of faking content when the export is absent."""
    provider = LIB.get_provider()
    status = provider.status()
    items = provider.items() if status["available"] else []

    filtered = items
    if category:
        filtered = [it for it in filtered if it.get("category") == category]
    if q:
        filtered = LIB.search(filtered, q, limit=50)

    return {
        "provider": status,
        "count": len(filtered),
        "items": filtered,
        "evidence": LIB.evidence(items),
    }


def _seed_matrix():
    """A fresh FOR006 matrix from the real master template (via the library
    provider), each row response-view-normalised. Used when a bid has no saved
    matrix yet — so opening a bid shows FWF's real question structure."""
    return [R.response_view({**R.default_response_item(), **q}) for q in LIB.master_template()]


def _responses_payload(conn, bid_id):
    """Assemble the Complete detail for one bid: the FOR006 matrix (seeded from the
    master template if unsaved), the completion summary, the evidence ledger, and
    the bid/opportunity context the workspace shows."""
    bid = dict(_require_bid(conn, bid_id))
    opp = _row_to_dict(conn.execute(
        "SELECT * FROM opportunities WHERE id = ?", (bid["opportunity_id"],)).fetchone())

    stored = db.get_bid_responses(conn, bid_id)
    saved = stored is not None and bool(stored.get("items"))
    items = [R.response_view(it) for it in stored["items"]] if saved else _seed_matrix()

    provider = LIB.get_provider()
    lib_status = provider.status()
    all_items = provider.items() if lib_status["available"] else []
    return {
        "bid": {"id": bid_id, "bid_name": bid.get("bid_name"),
                "stage": bid.get("stage"), "status": bid.get("status")},
        "opportunity": {
            "id": opp.get("id"), "title": opp.get("title"),
            "buyer_name": opp.get("buyer_name"), "url": opp.get("url"),
            "submission_deadline": opp.get("deadline_date"),
            "value": _num(opp.get("value_max")),
            "currency": opp.get("currency") or "GBP",
        },
        "items": items,
        "summary": R.matrix_summary(items),
        "library": lib_status,
        "evidence": LIB.evidence(all_items),
        "notes": (stored or {}).get("notes") or "",
        "saved": saved,
    }


@app.get("/api/bids/{bid_id}/responses")
def get_bid_responses(bid_id: int, conn=Depends(get_conn)):
    return _responses_payload(conn, bid_id)


@app.put("/api/bids/{bid_id}/responses")
def save_bid_responses(bid_id: int, body: dict = Body(default_factory=dict), conn=Depends(get_conn)):
    """Save (create or update) the FOR006 response matrix for a bid. Only known
    ResponseItem fields per row are kept (the client can't smuggle extra columns),
    `actual_words` is recomputed server-side from the answer text (the compliance
    number can't drift from the text), and the status is validated. The response
    mirrors GET so the UI can re-render in place."""
    _require_bid(conn, bid_id)

    fields = {}
    if isinstance(body.get("items"), list):
        template = R.default_response_item()
        cleaned = []
        for raw in body["items"]:
            if not isinstance(raw, dict):
                continue
            item = {k: raw.get(k, template[k]) for k in template}
            if item.get("status") not in R.RESPONSE_STATUSES:
                item["status"] = "To do"
            item["actual_words"] = R.word_count(item.get("supplier_response"))
            cleaned.append(item)
        fields["items"] = cleaned
    if "notes" in body:
        fields["notes"] = body["notes"]

    db.upsert_bid_responses(conn, bid_id, fields)
    return _responses_payload(conn, bid_id)


@app.post("/api/bids/{bid_id}/responses/{item_index}/ai-draft")
def ai_draft_response(bid_id: int, item_index: int, conn=Depends(get_conn)):
    """AI-draft one FOR006 answer, retrieval-grounded in the real library. The
    question is identified by its row index in the matrix (question_ref repeats
    across lots, so it isn't unique) — the client's matrix order matches the
    server's (both come from the saved matrix, else the master template). Returns a
    *draft* + the library matches it drew on — never saved; the UI puts it in the
    matrix for human review. 503 (not a crash) if no LLM is configured, so the
    manual matrix keeps working."""
    _require_bid(conn, bid_id)

    stored = db.get_bid_responses(conn, bid_id)
    items = stored["items"] if (stored and stored.get("items")) else LIB.master_template()

    if not 0 <= item_index < len(items):
        raise HTTPException(status_code=404, detail=f"question index {item_index} out of range")
    question = items[item_index]

    provider = LIB.get_provider()
    matches = LIB.search(provider.items(), question.get("question_text", ""),
                         question.get("tags", ""), limit=5) if provider.available() else []
    prompts = _ai_prompts(conn)
    try:
        draft, meta = complete_ai.draft_response(
            question, matches, profile=prompts["ai_profile"],
            guidance=prompts["ai_complete_guidance"])
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=f"AI drafting unavailable: {e}")
    return {"item_index": item_index, "question_ref": question.get("question_ref"),
            "draft": draft, "matches": matches, "meta": meta}


# ---- Stage 6: Learn / B07 Outcome + Lessons Learned -----------------------

def _learn_item(row):
    """One Learn board card from a raw joined bid row (db.list_bids_for_learn).
    Resolves the stored outcome (or a blank default) into the outcome view + the
    board fields: result, score %, submitted flag, and library-suggestion count.
    Whether an outcome was actually saved is tracked so the win-rate only counts
    real records, not un-recorded bids sitting at the default Awaiting."""
    saved = row.get("result") is not None or bool(row.get("lessons"))
    stored = {f: row.get(f) for f in db.BID_OUTCOME_FIELDS if row.get(f) is not None}
    outcome = {**L.default_outcome(), **stored}
    view = L.outcome_view(outcome)
    return {
        "bid_id": row["bid_id"],
        "opportunity_id": row["opportunity_id"],
        "title": row.get("title") or row.get("bid_name"),
        "buyer_name": row.get("buyer_name"),
        "url": row.get("url"),
        "submission_deadline": row.get("submission_deadline"),
        "submitted": (row.get("submitted") or "") == "yes",
        "result": view["result"],
        "result_tone": view["result_tone"],
        "is_decided": view["is_decided"],
        "score_pct": view["score_pct"],
        "score_received": view.get("score_received") or "",
        "winner": view.get("winner") or "",
        "suggestions_count": len(view["suggestions"]),
        "library_approved": (view.get("library_approved") or "") == "yes",
        "saved": saved,
    }


@app.get("/api/learn/reference")
def learn_reference():
    """B07 vocabulary (results, lesson categories, library actions) for the
    Learn outcome form."""
    return L.reference()


@app.get("/api/learn/board")
def learn_board(conn=Depends(get_conn)):
    """The cross-bid Learn board: every bid with its recorded outcome (result,
    score, library-suggestion count), the win-rate summary tracked bid-by-bid, and
    the loop-closing alerts (submitted-but-unrecorded / unapproved suggestions).
    This closes the journey loop — outcomes here feed the Stage-4 library."""
    rows = db.list_bids_for_learn(conn)

    items = [_learn_item(r) for r in rows]
    return {
        "count": len(items),
        "bids": items,
        "winrate": L.winrate_summary(items),
        "alerts": L.alerts(items),
    }


def _outcome_payload(conn, bid_id):
    """Assemble the Learn detail for one bid: the outcome (seeded blank if never
    recorded), its derived view (score %, suggestions), and the bid/opportunity
    context the form shows."""
    bid = dict(_require_bid(conn, bid_id))
    opp = _row_to_dict(conn.execute(
        "SELECT * FROM opportunities WHERE id = ?", (bid["opportunity_id"],)).fetchone())
    manage = db.get_bid_manage(conn, bid_id) or {}

    stored = db.get_bid_outcome(conn, bid_id)
    saved = stored is not None
    outcome = {**L.default_outcome(), **{k: v for k, v in (stored or {}).items()
                                         if k in db.BID_OUTCOME_FIELDS and v is not None}}
    view = L.outcome_view(outcome)
    return {
        "bid": {"id": bid_id, "bid_name": bid.get("bid_name"),
                "stage": bid.get("stage"), "status": bid.get("status")},
        "opportunity": {
            "id": opp.get("id"), "title": opp.get("title"),
            "buyer_name": opp.get("buyer_name"), "url": opp.get("url"),
            "submission_deadline": opp.get("deadline_date"),
            "value": _num(opp.get("value_max")),
            "currency": opp.get("currency") or "GBP",
        },
        "submitted": (manage.get("submitted") or "") == "yes",
        "outcome": view,
        "suggestions": view["suggestions"],
        "score_pct": view["score_pct"],
        "saved": saved,
    }


@app.get("/api/bids/{bid_id}/outcome")
def get_bid_outcome(bid_id: int, conn=Depends(get_conn)):
    return _outcome_payload(conn, bid_id)


@app.put("/api/bids/{bid_id}/outcome")
def save_bid_outcome(bid_id: int, body: dict = Body(default_factory=dict), conn=Depends(get_conn)):
    """Save (create or update) the B07 outcome for a bid: result, score, feedback,
    the Lessons Learned rows, and the library-approval sign-off. Only
    BID_OUTCOME_FIELDS are written; the `result` is validated against the known
    vocabulary and the lessons are normalised to the known shape (so the client
    can't smuggle extra columns into the JSON blob). The response mirrors GET so
    the UI can re-render in place."""
    _require_bid(conn, bid_id)

    fields = {k: v for k, v in body.items() if k in db.BID_OUTCOME_FIELDS}

    if "result" in fields and fields["result"] and fields["result"] not in L.RESULTS:
        raise HTTPException(status_code=400, detail=f"unknown result '{fields['result']}'")

    # Normalise the lessons: keep only known fields per row, and only a valid
    # library action, so the JSON blob can't carry arbitrary keys.
    if isinstance(fields.get("lessons"), list):
        fields["lessons"] = [
            {"category": lsn.get("category", ""), "note": lsn.get("note", ""),
             "action": lsn.get("action") if lsn.get("action") in L.LIBRARY_ACTIONS else ""}
            for lsn in fields["lessons"] if isinstance(lsn, dict)
        ]

    db.upsert_bid_outcome(conn, bid_id, fields)
    return _outcome_payload(conn, bid_id)


# ---- Compliance & Renewals (C-series) --------------------------------------
# The app-owned compliance-asset register (compliance.py / compliance_store.py):
# an ORG-LEVEL view of every credential/policy/framework + its renewal status,
# lifting the "expired cert at bid time" failure out of per-bid burial. Assets are
# uploaded here (bytes → gitignored store) or registered as references; expiry is
# derived live so a lapse is impossible to miss.


def _require_compliance_asset(conn, asset_id):
    """Fetch a compliance asset or raise 404."""
    asset = db.get_compliance_asset(conn, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="compliance asset not found")
    return asset


def _validate_iso_or_blank(value):
    """A blank or valid ISO (YYYY-MM-DD) date, else 422 — so a typo can't land a
    junk expiry that silently never alerts."""
    v = (value or "").strip()
    if not v:
        return ""
    try:
        datetime.date.fromisoformat(v)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"expiry_date must be ISO YYYY-MM-DD, got '{v}'")
    return v


def _compliance_asset_payload(conn, asset_id):
    """One asset with derived expiry + whether its file is actually in the store."""
    asset = CMP.derive_expiry(db.get_compliance_asset(conn, asset_id))
    asset["has_file"] = CSTORE.get_store().exists(asset.get("stored_path"))
    return asset


def _bootstrap_compliance_register(conn):
    """One-time bootstrap: on a fresh DB, seed the compliance register from the bid
    library (incl. any already-expired credential) so the org view isn't empty on
    day one. No-op once the register has rows, or when the library isn't present —
    never fakes data (CLAUDE.md hard rule)."""
    try:
        if db.list_compliance_assets(conn):
            return
        prov = LIB.get_provider()
        if not prov.available():
            return
        n = db.seed_compliance_assets(conn, CMP.seed_assets_from_library(prov.items()))
        if n:
            log.info("compliance register seeded from bid library: %d asset(s)", n)
    except Exception:  # bootstrap must never block startup
        log.warning("compliance seed-from-library skipped", exc_info=True)


@app.get("/api/compliance/reference")
def compliance_reference():
    """Vocabulary for the Compliance view (categories + the expiring-soon window)."""
    return CMP.reference()


@app.get("/api/compliance/board")
def compliance_board(conn=Depends(get_conn)):
    """The org-level Compliance & Renewals register: every asset with derived
    expiry status, sorted soonest-to-lapse first, plus status counts for the
    banner. `library_available` tells the UI whether an import is offerable."""
    assets = db.list_compliance_assets(conn)
    rows = CMP.board(assets)
    store = CSTORE.get_store()
    for a in rows:
        a["has_file"] = store.exists(a.get("stored_path"))
    return {
        "count": len(rows),
        "assets": rows,
        "summary": CMP.summary(rows),
        "reference": CMP.reference(),
        "library_available": LIB.get_provider().available(),
    }


@app.post("/api/compliance/assets")
async def create_compliance_asset(
    name: str = Form(...),
    category: str = Form("Company Credentials"),
    expiry_date: str = Form(""),
    review_frequency: str = Form(""),
    owner: str = Form(""),
    notes: str = Form(""),
    file: UploadFile | None = File(None),
    conn=Depends(get_conn),
):
    """Register (or upload) one compliance asset. multipart/form-data: the metadata
    fields, plus an optional `file` whose bytes go to the store (source=upload) —
    without a file it's a reference (source=reference). Expiry is derived on read."""
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    fields = {
        "name": name,
        "category": (category or "").strip() or "Company Credentials",
        "expiry_date": _validate_iso_or_blank(expiry_date),
        "review_frequency": (review_frequency or "").strip(),
        "owner": (owner or "").strip(),
        "notes": (notes or "").strip(),
        "source": "reference",
        "file_name": "", "stored_path": "", "content_type": "", "size_bytes": "",
    }
    if file is not None and file.filename:
        if not CSTORE.safe_ext(file.filename):
            raise HTTPException(status_code=422,
                                detail=f"unsupported file type (allowed: {', '.join(sorted(CSTORE.ALLOWED_EXTENSIONS))})")
        data = await file.read()
        if len(data) > CSTORE.MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413,
                                detail=f"file exceeds the {CSTORE.MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit")
        stored = CSTORE.get_store().save(data, file.filename)
        fields.update({
            "source": "upload",
            "file_name": os.path.basename(file.filename),
            "stored_path": stored,
            "content_type": file.content_type or "",
            "size_bytes": str(len(data)),
        })
    asset_id = db.insert_compliance_asset(conn, fields)
    return _compliance_asset_payload(conn, asset_id)


class ComplianceAssetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    expiry_date: str | None = None
    review_frequency: str | None = None
    owner: str | None = None
    notes: str | None = None


@app.put("/api/compliance/assets/{asset_id}")
def update_compliance_asset(asset_id: int, body: ComplianceAssetUpdate, conn=Depends(get_conn)):
    """Update an asset's metadata (name/category/expiry/owner/notes/review). Only
    these fields; the stored file is left untouched (re-upload to replace it). The
    response mirrors GET so the UI can re-render in place."""
    _require_compliance_asset(conn, asset_id)
    fields = body.model_dump(exclude_none=True)
    if "expiry_date" in fields:
        fields["expiry_date"] = _validate_iso_or_blank(fields["expiry_date"])
    if "name" in fields and not fields["name"].strip():
        raise HTTPException(status_code=422, detail="name cannot be blank")
    db.update_compliance_asset(conn, asset_id, fields)
    return _compliance_asset_payload(conn, asset_id)


@app.delete("/api/compliance/assets/{asset_id}")
def delete_compliance_asset(asset_id: int, conn=Depends(get_conn)):
    """Delete an asset and remove its stored file (if any). 404 if it doesn't exist."""
    stored_path = db.delete_compliance_asset(conn, asset_id)
    if stored_path is None:
        raise HTTPException(status_code=404, detail="compliance asset not found")
    if stored_path:
        CSTORE.get_store().delete(stored_path)
    return {"deleted": asset_id}


@app.get("/api/compliance/assets/{asset_id}/file")
def download_compliance_asset(asset_id: int, conn=Depends(get_conn)):
    """Download the stored file for an asset. Always served as an attachment with a
    generic content-type, so a stored HTML/SVG can never render/execute in the app
    origin. 404 if the asset has no stored file."""
    asset = _require_compliance_asset(conn, asset_id)
    stored = asset.get("stored_path") or ""
    store = CSTORE.get_store()
    if not stored or not store.exists(stored):
        raise HTTPException(status_code=404, detail="no file stored for this asset")
    data = store.open(stored)
    # Strip CR/LF/quotes so the filename can't break out of the header.
    filename = re.sub(r'[\r\n"]', "", asset.get("file_name") or f"asset-{asset_id}")[:200]
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/compliance/import-from-library")
def import_compliance_from_library(conn=Depends(get_conn)):
    """Seed the register from the bid library's credential items (idempotent — only
    populates an empty register). 409 if the library isn't available rather than
    faking data."""
    prov = LIB.get_provider()
    if not prov.available():
        raise HTTPException(status_code=409,
                            detail=f"bid library not available: {prov.unavailable_reason()}")
    n = db.seed_compliance_assets(conn, CMP.seed_assets_from_library(prov.items()))
    return {"imported": n}


@app.get("/api/opportunities/{opp_id}")
def get_opportunity(opp_id: int, conn=Depends(get_conn)):
    return _row_to_dict(_require_opp(conn, opp_id), include_raw=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
