#!/usr/bin/env python3
"""
JSON API for the Public Sector Bidding PoC.

Reads the shared SQLite store (db.py / bids.db) and exposes it to the React UI.
No HTML here — this is a pure JSON API; the Vite/React app in web/ renders it.

Endpoints:
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
import math

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import cpv_catalog
import db
import regions
import sources

app = FastAPI(title="Public Sector Bidding API", version="0.1.0")

# Local PoC: the Vite dev server (5173) calls this API (8000). Allow it.
# POST is needed now that the UI can trigger live searches.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
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
    """open / closed / unknown, derived from the bid deadline vs. now (UTC)."""
    if not deadline_date:
        return "unknown"
    try:
        end = datetime.datetime.fromisoformat(deadline_date)
        if end.tzinfo is None:
            end = end.replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return "unknown"
    now = datetime.datetime.now(datetime.timezone.utc)
    return "open" if end >= now else "closed"


def _row_to_dict(row, include_raw=False):
    rec = {k: row[k] for k in row.keys()}
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


@app.get("/api/meta")
def meta():
    """Distinct filter values + value bounds + per-source freshness."""
    conn = db.connect()
    db.init_db(conn)

    def distinct(col):
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

    # Materialise everything that touches sqlite3.Row BEFORE closing the conn —
    # Row access after close raises "Cannot operate on a closed database".
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
        # stages, default CPV scope) + a glossary for the region codes present.
        "search_options": sources.options(),
        "cpv_catalog": cpv_catalog.catalog(),
        "region_labels": regions.labels_for(distinct("region")),
    }
    conn.close()
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
def list_opportunities(params: dict = Depends(_list_params)):
    conn = db.connect()
    db.init_db(conn)
    results = _query_opportunities(conn, **params)
    conn.close()
    return {"count": len(results), "results": results}


# Fields written to the CSV export, in a readable order (raw_json excluded).
EXPORT_FIELDS = [
    "id", "source", "title", "buyer_name", "status", "bid_status", "lifecycle",
    "notice_type", "cpv_codes", "region", "region_label", "country",
    "value_min", "value_max", "currency", "published_date", "deadline_date",
    "ocid", "notice_id", "url", "description", "last_seen_at",
]


@app.get("/api/export")
def export_csv(params: dict = Depends(_list_params)):
    """Download the current (filtered) result set as CSV — same query as the
    list view, so the export mirrors exactly what's on screen."""
    conn = db.connect()
    db.init_db(conn)
    results = _query_opportunities(conn, **params)
    conn.close()

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for r in results:
        writer.writerow({k: r.get(k, "") for k in EXPORT_FIELDS})
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="opportunities.csv"'},
    )


class SearchRequest(BaseModel):
    sources: list[str]                       # registry keys to run (sources.SOURCES)
    cpv_codes: list[str] | None = None       # None → connector default scope
    stage: str = "tender"
    open_only: bool = True
    days: int = 120                          # rolling window if no explicit dates
    published_from: str | None = None        # ISO date/datetime; overrides `days`
    published_to: str | None = None


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
        raise HTTPException(400, f"unknown source(s): {', '.join(unknown)}")
    if not req.sources:
        raise HTTPException(400, "select at least one source")

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
        except Exception as e:  # noqa: BLE001 — surface any source failure, keep going
            runs.append({
                "key": key, "source": entry["name"], "ok": False,
                "error": f"{type(e).__name__}: {e}",
            })

    total_kept = sum(r.get("kept", 0) for r in runs if r["ok"])
    return {"runs": runs, "total_kept": total_kept}


@app.get("/api/opportunities/{opp_id}")
def get_opportunity(opp_id: int):
    conn = db.connect()
    db.init_db(conn)
    row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="opportunity not found")
    payload = _row_to_dict(row, include_raw=True)  # read Row before closing
    conn.close()
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
