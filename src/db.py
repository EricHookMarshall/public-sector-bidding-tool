#!/usr/bin/env python3
"""
Shared data layer for the Public Sector Bidding API PoC.

Dual-mode via SQLAlchemy Core (see the shim below `now_iso`): SQLite locally by
default, Azure SQL / SQL Server when DB_URL is set — same code, same call sites.

One common-record table, one idempotent upsert.
Every connector (Find a Tender, Contracts Finder, ...) maps its source's raw
response into the COMMON_FIELDS shape below and calls upsert_opportunity().

Schema follows support/public_sector_bid_apis.md (the richer ~18-field shape).

Two column groups live on the `opportunities` table:
  - COMMON_FIELDS   — source data every connector normalises into (the fetch path).
  - ENRICHMENT_FIELDS — triage additions (FOR004-derived), filled when an
    opportunity is promoted toward a bid/no-bid decision. Connector-untouched;
    written only via update_enrichment(). See docs/design/data-model.md.

Dedupe / freshness:
  - Upsert is keyed on (source, ocid) — re-running a connector UPDATES the
    existing row rather than inserting a duplicate. ocid is the stable OCDS
    contracting-process id; connectors must always populate it (fall back to the
    notice id if a source omits it).
  - record_source_run() stamps when each source was last checked (hard rule:
    refresh runs must record per-source last-checked time).
"""
import json
import os
import datetime
from collections.abc import Mapping

from sqlalchemy import (
    create_engine, inspect,
    MetaData, Table, Column, Integer, Unicode, UnicodeText,
    UniqueConstraint, ForeignKey,
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bids.db")

# Common record shape — every connector normalises into exactly these fields.
# (source, ocid) is the dedupe/upsert key.
COMMON_FIELDS = [
    "source",            # human-readable source name, e.g. "Find a Tender"
    "source_endpoint",   # API endpoint the record came from (provenance)
    "ocid",              # OCDS contracting-process id (dedupe key within a source)
    "notice_id",         # individual notice/release id
    "title",
    "buyer_name",
    "description",
    "cpv_codes",         # comma-separated CPV ids
    "region",
    "country",
    "value_min",
    "value_max",
    "currency",
    "published_date",
    "deadline_date",     # closing date for bids
    "notice_type",
    "status",            # active / open / closed / planned / ...
    "url",
    "raw_json",          # raw source payload, kept for re-mapping / debugging
    "last_seen_at",      # ISO timestamp this record was last seen in a fetch
]

# Triage-enrichment fields — added when an opportunity is looked at properly and
# carried forward into the bid/no-bid decision (Stage 2). These are NOT populated
# by connectors: like `lifecycle`, they live outside COMMON_FIELDS so the fetch
# path never touches them. They are reverse-engineered from FWF's real
# `FOR004 Bid Opportunity Overview` (see docs/design/data-model.md) — the fields
# FWF records to promote a raw notice into a considered opportunity. All nullable;
# written via update_enrichment(), not upsert_opportunity().
ENRICHMENT_FIELDS = [
    "sector",                 # e.g. "Housing / Registered Provider", "Central Gov"
    "opportunity_type",       # PPN / PQQ / SQ / ITT / DPS / Framework / Further Competition / Direct Award
    "procurement_portal",     # e.g. "MyTenders", "Jaggaer", "In-Tend"
    "portal_ref",             # buyer/portal reference, e.g. "FTS Ref 2025/S 000-036416"
    "clarification_deadline", # DISTINCT from deadline_date — the missed-clarification failure this tool exists to prevent
    "scope_summary",          # human summary of what's actually being bought
    "client_objectives",      # what the buyer is trying to achieve
    "evaluation_criteria",    # quality/price split, weightings, what's scored
    "known_competitors",      # incumbents / likely bidders
]

# --- Stage 2 (Triage) ------------------------------------------------------
# The bid/no-bid gate, reverse-engineered from FWF's real FOR001 Bid
# Qualification Questionnaire. Two tables:
#   qualifications — one FOR001 record per opportunity (the work-in-progress
#                    triage form; a decision may still be pending).
#   bids           — the spine (data-model.md "one record, six stages"). A Bid
#                    is born when a Qualification decision is "Go"; every later
#                    stage attaches to it. `stage` is what the app stepper reads.
# Both are kept OUTSIDE the connector/upsert path — only the Triage write path
# (upsert_qualification / create_bid_from_qualification) touches them.

# FOR001 "Qualification" sheet, field-for-field. All TEXT (text-tolerant per the
# PoC — data-model.md "start tolerant, tighten later"). Two fields hold repeating
# groups as JSON text: `delivery_team` ([{role, count, comments}], the FOR001
# fixed role set) and `win_qualification_rag` ({criterion_key: 1|2|3}). The
# economics (`estimated_bid_effort_days`, `estimated_bid_cost`) are computed from
# `complexity` via qualification.py and persisted here, so Planning can read the
# "cost to chase" directly and the number is snapshotted against the day-rate
# table in force when the call was made. See qualification.py for the vocab.
QUALIFICATION_FIELDS = [
    "client_name",
    "summary",
    "sales_owner",
    "framework",
    "project_requirement_sentence",
    "scope_summary",
    "platforms",
    "estimated_value",
    "estimated_start_date",
    "estimated_duration",
    "pricing_model",              # Fixed / T&M / Risk Reward
    "pricing_weighting",
    "lots_breakdown",
    "team_location",
    "partner_required",
    "delivery_team",             # JSON: [{role, count, comments}]
    "response_open_date",
    "clarification_deadline",    # FOR001 keeps this DISTINCT from submission_deadline
    "submission_deadline",
    "presentation_date",
    "complexity",                # Low / Low-Med / Medium / Med-High / High
    "estimated_bid_effort_days", # computed from complexity (persisted snapshot)
    "estimated_bid_cost",        # computed from complexity (persisted snapshot)
    "winning_strategy",
    "delivery_risks",
    "win_qualification_rag",     # JSON: {criterion_key: 1|2|3}
    "rag_summary_rating",        # 1|2|3 (rounded avg of the criteria)
    "rag_summary_label",         # Low / Med / High (risk-facing: high score = low risk)
    "decision",                  # Go / No go / "" (undecided)
    "qualify_out_reason",
    "caveats",
]

# JSON-valued qualification columns — encoded on write, decoded on read.
QUALIFICATION_JSON_FIELDS = {"delivery_team", "win_qualification_rag"}

# The bid spine. Minimal now (Triage's job is to create it and set stage);
# Plan/Complete/Manage/Learn hang their own tables off bid_id later.
BID_FIELDS = [
    "opportunity_id",
    "qualification_id",
    "bid_name",
    "stage",     # Search / Triage / Plan / Complete / Manage / Learn
    "status",    # active / withdrawn / submitted / closed
    "created_at",
    "updated_at",
]

# --- Stage 3 (Plan) --------------------------------------------------------
# The FOR002 BidPlan — one record per bid, hung off bid_id. Two parts (see
# docs/design/data-model.md §3 and bidplan.py):
#   (a) pipeline position — where the bid sits on the board + its owner.
#   (b) FOR002 phase timeline — the fixed ordered phase list (JSON), giving a
#       real critical path/calendar.
# Kept OUTSIDE the connector path, like qualifications: only the Plan write path
# (upsert_bid_plan) touches it. All TEXT, text-tolerant per the PoC. `phases`
# holds the repeating group [{phase, owner, start_date, completion_date, status,
# comments}] as JSON text.
BID_PLAN_FIELDS = [
    "pipeline_stage",     # Qualifying / Kick-off / Drafting / In review / Submitted / Closed
    "owner",              # bid owner (a FOR002 owner role or a person)
    "start_date",         # planned bid-work start
    "target_submission",  # internal target (may be earlier than the hard deadline_date)
    "phases",             # JSON: the FOR002 timeline [{phase, owner, ...}]
    "notes",
]

# JSON-valued bid-plan columns — encoded on write, decoded on read.
BID_PLAN_JSON_FIELDS = {"phases"}

# --- Stage 5 (Manage) ------------------------------------------------------
# The FOR003 CQLOG + pre-flight gate — one record per bid, hung off bid_id. Two
# repeating groups, held as JSON like bid_plans.phases (see clarification.py and
# docs/design/data-model.md §5/§5b):
#   clarifications — the FOR003 register [{question_number, question, owner,
#                    backup_owner, buyer_deadline, deadline_note, status, ...}].
#                    Losing track of one of these is the founding failure.
#   preflight      — the submission checklist [{key, status, note, expiry_date}],
#                    resolved against clarification.PREFLIGHT_ITEMS on read.
# `submitted`/`submitted_at` record the final human submit action (the buyer's
# portal submission stays a human act — the tool never auto-submits). Kept
# OUTSIDE the connector path, like qualifications/bid_plans: only the Manage
# write path (upsert_bid_manage) touches it. All TEXT, text-tolerant per the PoC.
BID_MANAGE_FIELDS = [
    "clarifications",   # JSON: the FOR003 register [{question_number, ...}]
    "preflight",        # JSON: the pre-flight checklist [{key, status, ...}]
    "submitted",        # "yes" once the final submit gate is cleared, else ""
    "submitted_at",     # ISO timestamp of the submit action
    "notes",
]

# JSON-valued manage columns — encoded on write, decoded on read.
BID_MANAGE_JSON_FIELDS = {"clarifications", "preflight"}

# --- Stage 6 (Learn) -------------------------------------------------------
# The B07 Outcome — one record per bid, hung off bid_id. From FWF's pipeline
# `Review` sheet (Won / Not Won) + the Lessons Learned Log (see outcome.py and
# docs/design/data-model.md §6). `lessons` is the one repeating group, held as
# JSON like bid_plans.phases: [{category, note, action}], where `action` (promote
# / refresh / retire) is the loop-closing suggestion back into the Stage-4
# library. `library_approved` records the human sign-off on those suggestions —
# the tool proposes; a person confirms (the Stage-6 scope: nothing is marked
# reusable without a person). Kept OUTSIDE the connector path, like the other
# stage tables: only the Learn write path (upsert_bid_outcome) touches it. All
# TEXT, text-tolerant per the PoC.
BID_OUTCOME_FIELDS = [
    "result",           # Awaiting / Won / Not Won / Withdrawn
    "score_received",   # e.g. "88" or "88/100"
    "max_score",        # optional denominator if score_received is bare
    "winner",           # who won, if Not Won (competitor intelligence)
    "award_date",
    "debrief_date",
    "feedback",         # buyer / evaluator feedback text
    "lessons",          # JSON: the Lessons Learned rows [{category, note, action}]
    "library_approved", # "yes" once the human signs off the suggested library updates
    "notes",
]

# JSON-valued outcome columns — encoded on write, decoded on read.
BID_OUTCOME_JSON_FIELDS = {"lessons"}

# --- Stage 4 (Complete) ----------------------------------------------------
# The FOR006 tender-response matrix — one record per bid, hung off bid_id. From
# FWF's `FOR006 Tender Response Master` (see response.py and data-model.md §4):
# the compliance matrix, one row per tender question. Held as JSON like
# bid_plans.phases: `items` = the matrix [{question_ref, question_text,
# word_count_limit, supplier_response, status, ...}]. The reusable content it
# draws from (LibraryItem) is NOT per-bid — it's read live through the library
# provider seam (library.py / LocalMirror), not stored here. Kept OUTSIDE the
# connector path, like the other stage tables: only the Complete write path
# (upsert_bid_responses) touches it. All TEXT, text-tolerant per the PoC.
BID_RESPONSE_FIELDS = [
    "items",   # JSON: the FOR006 matrix [{question_ref, supplier_response, status, ...}]
    "notes",
]

# JSON-valued response columns — encoded on write, decoded on read.
BID_RESPONSE_JSON_FIELDS = {"items"}


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def derive_lifecycle(deadline, now=None):
    """open / closed / unknown, from a bid deadline vs. `now` (UTC).

    The single source of truth for this: api.py derives it live per row, while
    refresh_clean writes it to the persisted flag over a whole batch — they must
    agree, so both call this. `now` defaults to the current UTC instant; a naive
    deadline is read as UTC. Anything unparseable / missing → "unknown"."""
    if not deadline:
        return "unknown"
    try:
        end = datetime.datetime.fromisoformat(deadline)
    except ValueError:
        return "unknown"
    if end.tzinfo is None:
        end = end.replace(tzinfo=datetime.timezone.utc)
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    return "open" if end >= now else "closed"


# --- Dual-mode engine + connection shim (Phase B) --------------------------
# The app is written against a tiny slice of the sqlite3 Connection API:
#   conn.execute("... ?", params).fetchone()/.fetchall()  (dict-like rows) + conn.commit()
# To run that UNCHANGED against either SQLite (local) or Azure SQL / SQL Server
# (cloud), connect() returns a thin adapter over a SQLAlchemy Core connection.
# Both the sqlite3 and pyodbc drivers use qmark ('?') paramstyle, so
# exec_driver_sql passes the existing SQL straight through to whichever dialect
# is active — no per-call-site rewrite. The schema DDL is the one genuinely
# dialect-divergent part (AUTOINCREMENT vs IDENTITY, TEXT vs NVARCHAR(MAX)); it
# is declared once as SQLAlchemy metadata below and emitted per-dialect by
# create_all(), replacing the old hand-written executescript.
#
# Backend selection: the DB_URL env var wins (the mssql+pyodbc URL for the local
# SQL Server container / Azure SQL in cloud); otherwise the local sqlite file,
# preserving the original PoC behaviour exactly.

metadata = MetaData()

# Columns that participate in a UNIQUE/index key. SQL Server rejects NVARCHAR(MAX)
# as a key column, so these get a bounded length; SQLite ignores the bound and
# still stores TEXT, so behaviour is unchanged locally. 400 keeps the composite
# (source, ocid) key well inside SQL Server's index-key byte limit.
_KEYED = {"source", "ocid"}


def _text_cols(fields):
    """One column per field name: bounded Unicode for key columns (NVARCHAR(400)
    on SQL Server), UnicodeText otherwise (NVARCHAR(MAX)); both TEXT on SQLite.
    Keeps the schema DRY from the same field lists the code uses."""
    return [Column(f, Unicode(400) if f in _KEYED else UnicodeText) for f in fields]


opportunities = Table(
    "opportunities", metadata,
    Column("id", Integer, primary_key=True),
    *_text_cols(COMMON_FIELDS),
    Column("lifecycle", UnicodeText),        # cleanup-pass flag; outside COMMON_FIELDS
    *_text_cols(ENRICHMENT_FIELDS),          # triage additions; connector-untouched
    UniqueConstraint("source", "ocid"),
)

source_runs = Table(
    "source_runs", metadata,
    Column("id", Integer, primary_key=True),
    Column("source", UnicodeText, nullable=False),
    Column("source_endpoint", UnicodeText),
    Column("checked_at", UnicodeText, nullable=False),
    Column("scanned", Integer),
    Column("kept", Integer),
)

qualifications = Table(
    "qualifications", metadata,
    Column("id", Integer, primary_key=True),
    Column("opportunity_id", Integer, ForeignKey("opportunities.id"), nullable=False),
    Column("created_at", UnicodeText),
    Column("updated_at", UnicodeText),
    *_text_cols(QUALIFICATION_FIELDS),
    UniqueConstraint("opportunity_id"),
)

bids = Table(
    "bids", metadata,
    Column("id", Integer, primary_key=True),
    Column("opportunity_id", Integer, ForeignKey("opportunities.id"), nullable=False),
    Column("qualification_id", Integer, ForeignKey("qualifications.id")),
    Column("bid_name", UnicodeText),
    Column("stage", UnicodeText),
    Column("status", UnicodeText),
    Column("created_at", UnicodeText),
    Column("updated_at", UnicodeText),
    UniqueConstraint("opportunity_id"),
)


def _bid_child(name, fields):
    """A per-bid stage table (plan/manage/outcome/responses): id + bid_id FK +
    timestamps + the stage's own fields, UNIQUE on bid_id (one row per bid)."""
    return Table(
        name, metadata,
        Column("id", Integer, primary_key=True),
        Column("bid_id", Integer, ForeignKey("bids.id"), nullable=False),
        Column("created_at", UnicodeText),
        Column("updated_at", UnicodeText),
        *_text_cols(fields),
        UniqueConstraint("bid_id"),
    )


bid_plans = _bid_child("bid_plans", BID_PLAN_FIELDS)
bid_manage = _bid_child("bid_manage", BID_MANAGE_FIELDS)
bid_outcomes = _bid_child("bid_outcomes", BID_OUTCOME_FIELDS)
bid_responses = _bid_child("bid_responses", BID_RESPONSE_FIELDS)

# App-domain settings (not secrets): a tiny key→JSON store that travels with the
# data. Distinct from src/.env config.py — that's LLM provider/key, git-ignored and
# read-only on Azure; these are tunable business numbers (bid day rates today) that
# must stay editable everywhere and belong with bids.db, not a dotfile.
app_settings = Table(
    "app_settings", metadata,
    Column("key", Unicode(200), primary_key=True),
    Column("value", UnicodeText),           # JSON-encoded
    Column("updated_at", UnicodeText),
)

# Triage selections — the "pull" gate for the Triage board. Search is the full
# universe of stored opportunities; an opp only reaches Triage once the user
# explicitly picks it ("Triage this →"). Kept OUT of the opportunities table for
# the same reason as dismissals: Search stays untouched and the shared record
# shape doesn't change. A row present = selected into Triage; delete it to remove.
# (Opps already worked — with a qualification or bid — are treated as in-triage
# regardless, so this gate never hides existing decisions.)
triage_selections = Table(
    "triage_selections", metadata,
    Column("opportunity_id", Integer, ForeignKey("opportunities.id"), primary_key=True),
    Column("selected_at", UnicodeText),
)

# Triage dismissals — a reversible "not pursuing this" flag, kept OUT of the
# opportunities table on purpose: Search stays untouched (a dismissal only hides
# the opp from the Triage board) and the shared record shape doesn't change. A
# row present = dismissed; delete it to restore.
triage_dismissals = Table(
    "triage_dismissals", metadata,
    Column("opportunity_id", Integer, ForeignKey("opportunities.id"), primary_key=True),
    Column("dismissed_at", UnicodeText),
)


class _Row(Mapping):
    """Dict-like view over a SQLAlchemy Row that mirrors sqlite3.Row: supports
    both row["col"] and row[0], plus .keys() and dict(row) — so every existing
    call site (and _row_dict) works untouched."""
    __slots__ = ("_m", "_vals")

    def __init__(self, sa_row):
        self._m = sa_row._mapping
        self._vals = None

    def __getitem__(self, key):
        if isinstance(key, int):
            if self._vals is None:
                self._vals = list(self._m.values())
            return self._vals[key]
        return self._m[key]

    def keys(self):
        return list(self._m.keys())

    def __iter__(self):
        return iter(self._m)

    def __len__(self):
        return len(self._m)


class _Result:
    """Wraps a SQLAlchemy CursorResult so .fetchone()/.fetchall()/iteration yield
    _Row objects (or None), matching the sqlite3 cursor surface the code uses."""

    def __init__(self, res):
        self._res = res

    def fetchone(self):
        row = self._res.fetchone()
        return _Row(row) if row is not None else None

    def fetchall(self):
        return [_Row(r) for r in self._res.fetchall()]

    def __iter__(self):
        for r in self._res:
            yield _Row(r)

    @property
    def rowcount(self):
        return self._res.rowcount


class _Conn:
    """The sqlite3.Connection slice the app relies on (execute / commit / close),
    backed by a SQLAlchemy Core connection."""

    def __init__(self, sa_conn):
        self._c = sa_conn

    @property
    def dialect(self):
        return self._c.dialect.name

    def execute(self, sql, params=()):
        if params:
            res = self._c.exec_driver_sql(sql, tuple(params))
        else:
            res = self._c.exec_driver_sql(sql)
        return _Result(res)

    def commit(self):
        self._c.commit()

    def close(self):
        self._c.close()


_ENGINES = {}


def _engine(db_path=DB_PATH):
    """Cached SQLAlchemy Engine for the active backend. DB_URL env overrides the
    default local sqlite file — that override is how the local SQL Server
    container / Azure SQL backend is selected."""
    url = os.environ.get("DB_URL") or f"sqlite:///{db_path}"
    if url not in _ENGINES:
        # pool_pre_ping: Azure SQL drops idle pooled connections at the gateway;
        # without a liveness check a stale one surfaces as a mid-request 500 that
        # never reproduces locally. Harmless (a cheap SELECT 1) for sqlite.
        _ENGINES[url] = create_engine(url, future=True, pool_pre_ping=True)
    return _ENGINES[url]


def _text_ddl(dialect):
    """The per-dialect column type for the ALTER-based back-fill migration."""
    return "NVARCHAR(MAX)" if dialect == "mssql" else "TEXT"


def connect(db_path=DB_PATH):
    """Open a connection to the active backend (sqlite by default; Azure SQL /
    SQL Server when DB_URL is set). Returns the _Conn adapter, so callers keep
    using conn.execute(...).fetchone()/.commit() exactly as before."""
    conn = _Conn(_engine(db_path).connect())
    if conn.dialect == "sqlite":
        conn.execute("PRAGMA journal_mode=WAL")  # SQLite-only durability setting
    return conn


def init_db(conn):
    """Create every table if absent (idempotent), emitting the right DDL for the
    active dialect via SQLAlchemy metadata, then back-fill any columns a
    pre-existing DB predates. Replaces the old SQLite-only executescript."""
    metadata.create_all(conn._c.engine, checkfirst=True)
    # Back-fill the opportunities columns that live OUTSIDE COMMON_FIELDS —
    # `lifecycle` (the cleanup-pass flag maintained by refresh_clean.py: open /
    # closed / unknown / stale, where "stale" = a stored row the source no longer
    # returns) and the triage-enrichment fields. Fresh DBs already have them from
    # create_all; this only fires on a DB created before they existed. Uses the
    # dialect-neutral inspector in place of the old PRAGMA table_info.
    existing = {c["name"] for c in inspect(conn._c).get_columns("opportunities")}
    coltype = _text_ddl(conn.dialect)
    # T-SQL is `ALTER TABLE t ADD col type` (no COLUMN keyword); SQLite wants
    # `ADD COLUMN`. Fresh DBs never hit this (create_all emits full tables), so a
    # dialect slip here would only surface late, migrating a pre-existing DB.
    add_kw = "ADD COLUMN" if conn.dialect == "sqlite" else "ADD"
    for col in ["lifecycle", *ENRICHMENT_FIELDS]:
        if col not in existing:
            conn.execute(f"ALTER TABLE opportunities {add_kw} {col} {coltype}")
    conn.commit()


def upsert_opportunity(conn, record):
    """Insert or update one opportunity, keyed on (source, ocid).

    `record` is a dict with any subset of COMMON_FIELDS; missing fields store
    NULL. `raw_json` may be a dict/list (it will be json-encoded) or a string.
    Returns "inserted" or "updated".
    """
    rec = dict(record)
    if isinstance(rec.get("raw_json"), (dict, list)):
        rec["raw_json"] = json.dumps(rec["raw_json"], ensure_ascii=False)
    rec.setdefault("last_seen_at", now_iso())

    if not rec.get("source") or not rec.get("ocid"):
        raise ValueError("upsert_opportunity requires both 'source' and 'ocid'")

    cur = conn.execute(
        "SELECT 1 FROM opportunities WHERE source = ? AND ocid = ?",
        (rec["source"], rec["ocid"]),
    )
    exists = cur.fetchone() is not None

    cols = [f for f in COMMON_FIELDS if f in rec]
    placeholders = ", ".join("?" for _ in cols)
    values = [rec[f] for f in cols]

    if exists:
        # Update everything except the key columns.
        set_cols = [c for c in cols if c not in ("source", "ocid")]
        assignments = ", ".join(f"{c} = ?" for c in set_cols)
        conn.execute(
            f"UPDATE opportunities SET {assignments} WHERE source = ? AND ocid = ?",
            [rec[c] for c in set_cols] + [rec["source"], rec["ocid"]],
        )
        return "updated"
    else:
        conn.execute(
            f"INSERT INTO opportunities ({', '.join(cols)}) VALUES ({placeholders})",
            values,
        )
        return "inserted"


def update_enrichment(conn, opp_id, fields):
    """Set triage-enrichment fields on one opportunity, by row id.

    `fields` is a dict; only keys in ENRICHMENT_FIELDS are written (everything
    else is ignored, so this can't be used to smuggle in connector/source data).
    This is the Stage 2 (Triage) write path — the connector upsert path never
    touches these columns. Returns the number of fields written.
    """
    cols = [f for f in ENRICHMENT_FIELDS if f in fields]
    if not cols:
        return 0
    assignments = ", ".join(f"{c} = ?" for c in cols)
    conn.execute(
        f"UPDATE opportunities SET {assignments} WHERE id = ?",
        [fields[c] for c in cols] + [opp_id],
    )
    conn.commit()
    return len(cols)


# JSON-valued columns across all stage tables — decoded on read by _row_dict.
_JSON_FIELDS = (QUALIFICATION_JSON_FIELDS | BID_PLAN_JSON_FIELDS
                | BID_MANAGE_JSON_FIELDS | BID_OUTCOME_JSON_FIELDS
                | BID_RESPONSE_JSON_FIELDS)


def _row_dict(row):
    """DB Row → plain dict (or None), decoding JSON stage fields
    (qualification delivery_team/RAG, bid-plan phases)."""
    if row is None:
        return None
    rec = {k: row[k] for k in row.keys()}
    for f in _JSON_FIELDS:
        if isinstance(rec.get(f), str) and rec[f]:
            try:
                rec[f] = json.loads(rec[f])
            except ValueError:
                pass  # leave the raw string if it isn't valid JSON
    return rec


def get_qualification(conn, opp_id):
    """The FOR001 qualification for one opportunity, or None if not triaged yet.
    JSON fields (delivery_team, win_qualification_rag) come back decoded."""
    row = conn.execute(
        "SELECT * FROM qualifications WHERE opportunity_id = ?", (opp_id,)
    ).fetchone()
    return _row_dict(row)


def _upsert_one(conn, table, key_col, key_val, fields, allowed_fields, json_fields):
    """Insert or update one row in a stage table keyed by a single column.

    The five stage upserts (qualification, plan, manage, responses, outcome) are
    identical bar the table, key column, and field allow-lists — this is the
    shared body. Only keys in `allowed_fields` are written, so a caller can't
    smuggle in other columns; JSON-valued fields (`json_fields`) passed as
    dict/list are encoded here. Re-upserting the same key updates in place and
    bumps updated_at (blank `fields` still touches updated_at). `table`/`key_col`
    are internal constants, never user input. Returns the row id.
    """
    rec = {f: fields[f] for f in allowed_fields if f in fields}
    for f in json_fields:
        if isinstance(rec.get(f), (dict, list)):
            rec[f] = json.dumps(rec[f], ensure_ascii=False)

    existing = conn.execute(
        f"SELECT id FROM {table} WHERE {key_col} = ?", (key_val,)
    ).fetchone()
    now = now_iso()

    if existing:
        if rec:
            assignments = ", ".join(f"{c} = ?" for c in rec)
            conn.execute(
                f"UPDATE {table} SET {assignments}, updated_at = ? WHERE {key_col} = ?",
                [rec[c] for c in rec] + [now, key_val],
            )
        else:
            conn.execute(
                f"UPDATE {table} SET updated_at = ? WHERE {key_col} = ?", (now, key_val)
            )
        row_id = existing["id"]
    else:
        cols = [key_col, "created_at", "updated_at", *rec.keys()]
        placeholders = ", ".join("?" for _ in cols)
        conn.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
            [key_val, now, now, *rec.values()],
        )
        row_id = conn.execute(
            f"SELECT id FROM {table} WHERE {key_col} = ?", (key_val,)
        ).fetchone()["id"]
    conn.commit()
    return row_id


def upsert_qualification(conn, opp_id, fields):
    """Insert or update the FOR001 qualification for one opportunity.

    Keyed on opportunity_id (one qualification per opportunity — re-triaging
    updates in place). Only keys in QUALIFICATION_FIELDS are written, so this
    can't smuggle in connector/source columns. JSON-valued fields (delivery_team,
    win_qualification_rag) may be passed as dict/list. Returns the qualification
    row id.
    """
    return _upsert_one(conn, "qualifications", "opportunity_id", opp_id, fields,
                       QUALIFICATION_FIELDS, QUALIFICATION_JSON_FIELDS)


def get_bid_for_opportunity(conn, opp_id):
    """The bid spun off an opportunity's Go decision, or None."""
    row = conn.execute(
        "SELECT * FROM bids WHERE opportunity_id = ?", (opp_id,)
    ).fetchone()
    return _row_dict(row)


def create_bid_from_qualification(conn, opp_id, qualification_id, bid_name, stage="Triage"):
    """Promote an opportunity into a Bid (the spine) — called when a
    qualification decides Go. Idempotent: if a bid already exists for this
    opportunity, its stage/qualification link is refreshed rather than
    duplicated (UNIQUE(opportunity_id) also guards it). Returns the bid id.
    """
    now = now_iso()
    existing = conn.execute(
        "SELECT id FROM bids WHERE opportunity_id = ?", (opp_id,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE bids SET qualification_id = ?, bid_name = ?, stage = ?, updated_at = ? "
            "WHERE opportunity_id = ?",
            (qualification_id, bid_name, stage, now, opp_id),
        )
        bid_id = existing["id"]
    else:
        conn.execute(
            "INSERT INTO bids (opportunity_id, qualification_id, bid_name, stage, status, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, 'active', ?, ?)",
            (opp_id, qualification_id, bid_name, stage, now, now),
        )
        bid_id = conn.execute(
            "SELECT id FROM bids WHERE opportunity_id = ?", (opp_id,)
        ).fetchone()["id"]
    conn.commit()
    return bid_id


def get_bid_plan(conn, bid_id):
    """The FOR002 bid plan for one bid, or None if not planned yet. JSON `phases`
    comes back decoded."""
    row = conn.execute(
        "SELECT * FROM bid_plans WHERE bid_id = ?", (bid_id,)
    ).fetchone()
    return _row_dict(row)


def upsert_bid_plan(conn, bid_id, fields):
    """Insert or update the FOR002 bid plan for one bid.

    Keyed on bid_id (one plan per bid — re-planning updates in place). Only keys
    in BID_PLAN_FIELDS are written. The JSON `phases` field may be passed as a
    list. Returns the bid_plan row id.
    """
    return _upsert_one(conn, "bid_plans", "bid_id", bid_id, fields,
                       BID_PLAN_FIELDS, BID_PLAN_JSON_FIELDS)


def get_bid_manage(conn, bid_id):
    """The FOR003 manage record (clarifications + pre-flight) for one bid, or None
    if not managed yet. JSON `clarifications`/`preflight` come back decoded."""
    row = conn.execute(
        "SELECT * FROM bid_manage WHERE bid_id = ?", (bid_id,)
    ).fetchone()
    return _row_dict(row)


def upsert_bid_manage(conn, bid_id, fields):
    """Insert or update the FOR003 manage record for one bid.

    Keyed on bid_id (one register per bid — re-managing updates in place). Only
    keys in BID_MANAGE_FIELDS are written. The JSON `clarifications`/`preflight`
    fields may be passed as lists. Returns the bid_manage row id.
    """
    return _upsert_one(conn, "bid_manage", "bid_id", bid_id, fields,
                       BID_MANAGE_FIELDS, BID_MANAGE_JSON_FIELDS)


def list_bids_for_manage(conn):
    """Every bid joined with the fields the Manage board needs — from the
    opportunity (title, buyer, submission deadline) and the manage record (the
    FOR003 register + pre-flight + submitted flag). Raw values only; api.py
    resolves the register and computes the derived deadlines/alerts. Ordered by
    submission deadline (soonest first) so the board reads urgency-first."""
    rows = conn.execute(
        """
        SELECT
            b.id               AS bid_id,
            b.opportunity_id   AS opportunity_id,
            b.bid_name         AS bid_name,
            b.status           AS bid_status,
            o.title            AS title,
            o.buyer_name       AS buyer_name,
            o.deadline_date    AS submission_deadline,
            o.url              AS url,
            m.clarifications   AS clarifications,
            m.preflight        AS preflight,
            m.submitted        AS submitted
        FROM bids b
        JOIN opportunities o ON o.id = b.opportunity_id
        LEFT JOIN bid_manage m ON m.bid_id = b.id
        ORDER BY CASE WHEN o.deadline_date IS NULL THEN 1 ELSE 0 END, o.deadline_date ASC
        """
    ).fetchall()
    return [_row_dict(r) for r in rows]


def get_bid_responses(conn, bid_id):
    """The FOR006 response matrix for one bid, or None if not started. JSON `items`
    comes back decoded."""
    row = conn.execute(
        "SELECT * FROM bid_responses WHERE bid_id = ?", (bid_id,)
    ).fetchone()
    return _row_dict(row)


def upsert_bid_responses(conn, bid_id, fields):
    """Insert or update the FOR006 response matrix for one bid.

    Keyed on bid_id (one matrix per bid — re-working updates in place). Only keys
    in BID_RESPONSE_FIELDS are written. The JSON `items` field may be passed as a
    list. Returns the bid_responses row id.
    """
    return _upsert_one(conn, "bid_responses", "bid_id", bid_id, fields,
                       BID_RESPONSE_FIELDS, BID_RESPONSE_JSON_FIELDS)


def list_bids_for_complete(conn):
    """Every bid joined with the fields the Complete board needs — from the
    opportunity (title, buyer, submission deadline) and the response record (the
    FOR006 matrix). Raw values only; api.py resolves the matrix + completion
    summary. Ordered by submission deadline (soonest first) so the board reads
    urgency-first."""
    rows = conn.execute(
        """
        SELECT
            b.id             AS bid_id,
            b.opportunity_id AS opportunity_id,
            b.bid_name       AS bid_name,
            b.status         AS bid_status,
            o.title          AS title,
            o.buyer_name     AS buyer_name,
            o.deadline_date  AS submission_deadline,
            o.url            AS url,
            r.items          AS items
        FROM bids b
        JOIN opportunities o ON o.id = b.opportunity_id
        LEFT JOIN bid_responses r ON r.bid_id = b.id
        ORDER BY CASE WHEN o.deadline_date IS NULL THEN 1 ELSE 0 END, o.deadline_date ASC
        """
    ).fetchall()
    return [_row_dict(r) for r in rows]


def get_bid_outcome(conn, bid_id):
    """The B07 outcome record (result + lessons) for one bid, or None if no
    outcome recorded yet. JSON `lessons` comes back decoded."""
    row = conn.execute(
        "SELECT * FROM bid_outcomes WHERE bid_id = ?", (bid_id,)
    ).fetchone()
    return _row_dict(row)


def upsert_bid_outcome(conn, bid_id, fields):
    """Insert or update the B07 outcome record for one bid.

    Keyed on bid_id (one outcome per bid — re-recording updates in place). Only
    keys in BID_OUTCOME_FIELDS are written. The JSON `lessons` field may be passed
    as a list. Returns the bid_outcome row id.
    """
    return _upsert_one(conn, "bid_outcomes", "bid_id", bid_id, fields,
                       BID_OUTCOME_FIELDS, BID_OUTCOME_JSON_FIELDS)


def list_bids_for_learn(conn):
    """Every bid joined with the fields the Learn board needs — from the
    opportunity (title, buyer, submission deadline), the outcome record (result +
    lessons + score) and the manage record's `submitted` flag (so the board knows
    which bids are submitted-but-unrecorded — the loop-closing nudge). Raw values
    only; api.py resolves the outcome view + win-rate. Ordered by submission
    deadline (most recently closed first) so the freshest outcomes lead."""
    rows = conn.execute(
        """
        SELECT
            b.id               AS bid_id,
            b.opportunity_id   AS opportunity_id,
            b.bid_name         AS bid_name,
            b.status           AS bid_status,
            o.title            AS title,
            o.buyer_name       AS buyer_name,
            o.deadline_date    AS submission_deadline,
            o.url              AS url,
            m.submitted        AS submitted,
            x.result           AS result,
            x.score_received   AS score_received,
            x.max_score        AS max_score,
            x.winner           AS winner,
            x.award_date       AS award_date,
            x.debrief_date     AS debrief_date,
            x.feedback         AS feedback,
            x.lessons          AS lessons,
            x.library_approved AS library_approved
        FROM bids b
        JOIN opportunities o ON o.id = b.opportunity_id
        LEFT JOIN bid_manage m ON m.bid_id = b.id
        LEFT JOIN bid_outcomes x ON x.bid_id = b.id
        ORDER BY CASE WHEN o.deadline_date IS NULL THEN 1 ELSE 0 END, o.deadline_date DESC
        """
    ).fetchall()
    return [_row_dict(r) for r in rows]


def list_bids_for_board(conn):
    """Every bid joined with the fields the Plan board needs — from the
    opportunity (title, buyer, the two deadlines, value), the qualification (the
    'cost to chase' economics), and the bid plan (pipeline position, owner). Raw
    values only; api.py computes the derived days-to-deadline / capacity. Ordered
    by submission deadline (soonest first) so the board reads urgency-first."""
    rows = conn.execute(
        """
        SELECT
            b.id               AS bid_id,
            b.opportunity_id   AS opportunity_id,
            b.bid_name         AS bid_name,
            b.status           AS bid_status,
            o.title            AS title,
            o.buyer_name       AS buyer_name,
            o.deadline_date    AS submission_deadline,
            o.clarification_deadline AS opp_clarification_deadline,
            o.value_max        AS value_max,
            o.currency         AS currency,
            o.url              AS url,
            q.estimated_value  AS estimated_value,
            q.estimated_bid_effort_days AS effort_days,
            q.estimated_bid_cost        AS cost,
            q.clarification_deadline    AS qual_clarification_deadline,
            q.complexity       AS complexity,
            p.pipeline_stage   AS pipeline_stage,
            p.owner            AS owner,
            p.target_submission AS target_submission
        FROM bids b
        JOIN opportunities o ON o.id = b.opportunity_id
        LEFT JOIN qualifications q ON q.opportunity_id = b.opportunity_id
        LEFT JOIN bid_plans p ON p.bid_id = b.id
        ORDER BY CASE WHEN o.deadline_date IS NULL THEN 1 ELSE 0 END, o.deadline_date ASC
        """
    ).fetchall()
    # _row_dict (not bare dict) so any JSON stage column added to this board query
    # later is decoded consistently with the sibling list/get accessors.
    return [_row_dict(r) for r in rows]


def list_triage_states(conn):
    """Per-opportunity triage state for the Triage board: the qualification's
    decision / complexity / RAG (if the opportunity has been triaged at all) and
    whether it has been promoted into a bid. Returns two dicts keyed by
    opportunity_id: {states, bid_stage}. One small query each — the board joins
    them onto the opportunity list in api.py."""
    quals = conn.execute(
        "SELECT opportunity_id, decision, complexity, rag_summary_label, "
        "rag_summary_rating FROM qualifications"
    ).fetchall()
    bid_rows = conn.execute("SELECT opportunity_id, stage FROM bids").fetchall()

    states = {
        q["opportunity_id"]: {
            "decision": q["decision"] or "",
            "complexity": q["complexity"] or "",
            "rag_label": q["rag_summary_label"] or "",
            "rag_rating": q["rag_summary_rating"],
        }
        for q in quals
    }
    bid_stage = {b["opportunity_id"]: b["stage"] for b in bid_rows}
    return states, bid_stage


def selected_opportunity_ids(conn):
    """The set of opportunity ids explicitly pulled into the Triage board."""
    rows = conn.execute("SELECT opportunity_id FROM triage_selections").fetchall()
    return {r["opportunity_id"] for r in rows}


def set_triage_selected(conn, opp_id, selected):
    """Pull an opportunity into the Triage board (or remove it). Idempotent:
    selecting an already-selected opp (or removing an absent one) is a no-op.
    Returns the resulting selected state."""
    exists = conn.execute(
        "SELECT 1 FROM triage_selections WHERE opportunity_id = ?", (opp_id,)
    ).fetchone()
    if selected and not exists:
        conn.execute(
            "INSERT INTO triage_selections (opportunity_id, selected_at) VALUES (?, ?)",
            (opp_id, now_iso()),
        )
    elif not selected and exists:
        conn.execute(
            "DELETE FROM triage_selections WHERE opportunity_id = ?", (opp_id,)
        )
    conn.commit()
    return bool(selected)


def dismissed_opportunity_ids(conn):
    """The set of opportunity ids dismissed from the Triage board (reversible)."""
    rows = conn.execute("SELECT opportunity_id FROM triage_dismissals").fetchall()
    return {r["opportunity_id"] for r in rows}


def set_triage_dismissed(conn, opp_id, dismissed):
    """Reversibly dismiss (or restore) an opportunity on the Triage board. Idempotent:
    dismissing an already-dismissed opp (or restoring an active one) is a no-op.
    Returns the resulting dismissed state."""
    exists = conn.execute(
        "SELECT 1 FROM triage_dismissals WHERE opportunity_id = ?", (opp_id,)
    ).fetchone()
    if dismissed and not exists:
        conn.execute(
            "INSERT INTO triage_dismissals (opportunity_id, dismissed_at) VALUES (?, ?)",
            (opp_id, now_iso()),
        )
    elif not dismissed and exists:
        conn.execute(
            "DELETE FROM triage_dismissals WHERE opportunity_id = ?", (opp_id,)
        )
    conn.commit()
    return bool(dismissed)


def get_setting(conn, key, default=None):
    """Read an app_settings value (JSON-decoded), or `default` if unset/corrupt."""
    row = conn.execute(
        "SELECT value FROM app_settings WHERE key = ?", (key,)
    ).fetchone()
    if row is None or row["value"] in (None, ""):
        return default
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return default


def set_setting(conn, key, value):
    """Upsert an app_settings value (JSON-encoded). Returns the stored value."""
    payload = json.dumps(value, ensure_ascii=False)
    now = now_iso()
    exists = conn.execute(
        "SELECT 1 FROM app_settings WHERE key = ?", (key,)
    ).fetchone() is not None
    if exists:
        conn.execute(
            "UPDATE app_settings SET value = ?, updated_at = ? WHERE key = ?",
            (payload, now, key),
        )
    else:
        conn.execute(
            "INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, payload, now),
        )
    conn.commit()
    return value


def record_source_run(conn, source, source_endpoint, scanned, kept):
    """Stamp when a source was last checked and how much it yielded."""
    conn.execute(
        "INSERT INTO source_runs (source, source_endpoint, checked_at, scanned, kept) "
        "VALUES (?, ?, ?, ?, ?)",
        (source, source_endpoint, now_iso(), scanned, kept),
    )
    conn.commit()


def counts(conn):
    """Quick summary for sanity checks."""
    total = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    by_source = conn.execute(
        "SELECT source, COUNT(*) AS n FROM opportunities GROUP BY source ORDER BY n DESC"
    ).fetchall()
    return total, [(r["source"], r["n"]) for r in by_source]


if __name__ == "__main__":
    # `python3 db.py` — create the DB and print a summary.
    conn = connect()
    init_db(conn)
    total, by_source = counts(conn)
    print(f"DB ready at {DB_PATH}")
    print(f"opportunities: {total}")
    for s, n in by_source:
        print(f"  {s}: {n}")
    quals = conn.execute("SELECT COUNT(*) FROM qualifications").fetchone()[0]
    bids = conn.execute("SELECT COUNT(*) FROM bids").fetchone()[0]
    plans = conn.execute("SELECT COUNT(*) FROM bid_plans").fetchone()[0]
    manage = conn.execute("SELECT COUNT(*) FROM bid_manage").fetchone()[0]
    outcomes = conn.execute("SELECT COUNT(*) FROM bid_outcomes").fetchone()[0]
    responses = conn.execute("SELECT COUNT(*) FROM bid_responses").fetchone()[0]
    print(f"qualifications: {quals}")
    print(f"bids: {bids}")
    print(f"bid_plans: {plans}")
    print(f"bid_manage: {manage}")
    print(f"bid_responses: {responses}")
    print(f"bid_outcomes: {outcomes}")
