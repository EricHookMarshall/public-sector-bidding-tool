#!/usr/bin/env python3
"""
Shared SQLite layer for the Public Sector Bidding API PoC.

One local file (bids.db), one common-record table, one idempotent upsert.
Every connector (Find a Tender, Contracts Finder, ...) maps its source's raw
response into the COMMON_FIELDS shape below and calls upsert_opportunity().

Schema follows support/public_sector_bid_apis.md (the richer ~18-field shape),
not the older 12-field sketch in CLAUDE.md.

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
import sqlite3
import json
import os
import datetime

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


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn):
    cols = ",\n        ".join(f"{f} TEXT" for f in COMMON_FIELDS)
    qual_cols = ",\n            ".join(f"{f} TEXT" for f in QUALIFICATION_FIELDS)
    plan_cols = ",\n            ".join(f"{f} TEXT" for f in BID_PLAN_FIELDS)
    manage_cols = ",\n            ".join(f"{f} TEXT" for f in BID_MANAGE_FIELDS)
    conn.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {cols},
        UNIQUE(source, ocid)
        );

        -- Per-source freshness log: when each source was last checked.
        CREATE TABLE IF NOT EXISTS source_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source          TEXT NOT NULL,
            source_endpoint TEXT,
            checked_at      TEXT NOT NULL,
            scanned         INTEGER,
            kept            INTEGER
        );

        -- Stage 2 (Triage): one FOR001 qualification per opportunity. UNIQUE on
        -- opportunity_id so a re-triage updates in place rather than duplicating.
        CREATE TABLE IF NOT EXISTS qualifications (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            created_at     TEXT,
            updated_at     TEXT,
            {qual_cols},
            UNIQUE(opportunity_id),
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
        );

        -- The bid spine — born when a qualification decides "Go".
        CREATE TABLE IF NOT EXISTS bids (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            qualification_id INTEGER,
            bid_name       TEXT,
            stage          TEXT,
            status         TEXT,
            created_at     TEXT,
            updated_at     TEXT,
            UNIQUE(opportunity_id),
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id),
            FOREIGN KEY(qualification_id) REFERENCES qualifications(id)
        );

        -- Stage 3 (Plan): one FOR002 bid plan per bid. UNIQUE on bid_id so
        -- re-planning updates in place rather than duplicating.
        CREATE TABLE IF NOT EXISTS bid_plans (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            bid_id     INTEGER NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            {plan_cols},
            UNIQUE(bid_id),
            FOREIGN KEY(bid_id) REFERENCES bids(id)
        );

        -- Stage 5 (Manage): one FOR003 CQLOG + pre-flight record per bid. UNIQUE
        -- on bid_id so re-managing updates in place rather than duplicating.
        CREATE TABLE IF NOT EXISTS bid_manage (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            bid_id     INTEGER NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            {manage_cols},
            UNIQUE(bid_id),
            FOREIGN KEY(bid_id) REFERENCES bids(id)
        );
        """
    )
    # Lightweight migration: `lifecycle` is a persisted flag (open / closed /
    # unknown / stale) maintained by refresh_clean.py. It lives OUTSIDE
    # COMMON_FIELDS so connectors never touch it — only the cleanup pass writes
    # it. "stale" = a stored row that the source no longer returns (withdrawn /
    # dropped off the feed) — the one lifecycle signal the API can't derive live
    # from deadline_date alone.
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(opportunities)")}
    if "lifecycle" not in existing:
        conn.execute("ALTER TABLE opportunities ADD COLUMN lifecycle TEXT")
    # Triage-enrichment columns (see ENRICHMENT_FIELDS) — added the same way:
    # nullable, connector-untouched, filled when an opportunity is triaged.
    for f in ENRICHMENT_FIELDS:
        if f not in existing:
            conn.execute(f"ALTER TABLE opportunities ADD COLUMN {f} TEXT")
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
_JSON_FIELDS = QUALIFICATION_JSON_FIELDS | BID_PLAN_JSON_FIELDS | BID_MANAGE_JSON_FIELDS


def _row_dict(row):
    """sqlite3.Row → plain dict (or None), decoding JSON stage fields
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


def upsert_qualification(conn, opp_id, fields):
    """Insert or update the FOR001 qualification for one opportunity.

    Keyed on opportunity_id (one qualification per opportunity — re-triaging
    updates in place). `fields` is a dict; only keys in QUALIFICATION_FIELDS are
    written, so this can't smuggle in connector/source columns. JSON-valued
    fields (delivery_team, win_qualification_rag) may be passed as dict/list and
    are encoded here. Returns the qualification row id.
    """
    rec = {f: fields[f] for f in QUALIFICATION_FIELDS if f in fields}
    for f in QUALIFICATION_JSON_FIELDS:
        if isinstance(rec.get(f), (dict, list)):
            rec[f] = json.dumps(rec[f], ensure_ascii=False)

    existing = conn.execute(
        "SELECT id FROM qualifications WHERE opportunity_id = ?", (opp_id,)
    ).fetchone()
    now = now_iso()

    if existing:
        if rec:
            assignments = ", ".join(f"{c} = ?" for c in rec)
            conn.execute(
                f"UPDATE qualifications SET {assignments}, updated_at = ? WHERE opportunity_id = ?",
                [rec[c] for c in rec] + [now, opp_id],
            )
        else:
            conn.execute(
                "UPDATE qualifications SET updated_at = ? WHERE opportunity_id = ?",
                (now, opp_id),
            )
        qid = existing["id"]
    else:
        cols = ["opportunity_id", "created_at", "updated_at", *rec.keys()]
        placeholders = ", ".join("?" for _ in cols)
        conn.execute(
            f"INSERT INTO qualifications ({', '.join(cols)}) VALUES ({placeholders})",
            [opp_id, now, now, *rec.values()],
        )
        qid = conn.execute(
            "SELECT id FROM qualifications WHERE opportunity_id = ?", (opp_id,)
        ).fetchone()["id"]
    conn.commit()
    return qid


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
    in BID_PLAN_FIELDS are written, so this can't smuggle in other columns. The
    JSON `phases` field may be passed as a list and is encoded here. Returns the
    bid_plan row id.
    """
    rec = {f: fields[f] for f in BID_PLAN_FIELDS if f in fields}
    for f in BID_PLAN_JSON_FIELDS:
        if isinstance(rec.get(f), (dict, list)):
            rec[f] = json.dumps(rec[f], ensure_ascii=False)

    existing = conn.execute(
        "SELECT id FROM bid_plans WHERE bid_id = ?", (bid_id,)
    ).fetchone()
    now = now_iso()

    if existing:
        if rec:
            assignments = ", ".join(f"{c} = ?" for c in rec)
            conn.execute(
                f"UPDATE bid_plans SET {assignments}, updated_at = ? WHERE bid_id = ?",
                [rec[c] for c in rec] + [now, bid_id],
            )
        else:
            conn.execute(
                "UPDATE bid_plans SET updated_at = ? WHERE bid_id = ?", (now, bid_id)
            )
        pid = existing["id"]
    else:
        cols = ["bid_id", "created_at", "updated_at", *rec.keys()]
        placeholders = ", ".join("?" for _ in cols)
        conn.execute(
            f"INSERT INTO bid_plans ({', '.join(cols)}) VALUES ({placeholders})",
            [bid_id, now, now, *rec.values()],
        )
        pid = conn.execute(
            "SELECT id FROM bid_plans WHERE bid_id = ?", (bid_id,)
        ).fetchone()["id"]
    conn.commit()
    return pid


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
    keys in BID_MANAGE_FIELDS are written, so this can't smuggle in other columns.
    The JSON `clarifications`/`preflight` fields may be passed as lists and are
    encoded here. Returns the bid_manage row id.
    """
    rec = {f: fields[f] for f in BID_MANAGE_FIELDS if f in fields}
    for f in BID_MANAGE_JSON_FIELDS:
        if isinstance(rec.get(f), (dict, list)):
            rec[f] = json.dumps(rec[f], ensure_ascii=False)

    existing = conn.execute(
        "SELECT id FROM bid_manage WHERE bid_id = ?", (bid_id,)
    ).fetchone()
    now = now_iso()

    if existing:
        if rec:
            assignments = ", ".join(f"{c} = ?" for c in rec)
            conn.execute(
                f"UPDATE bid_manage SET {assignments}, updated_at = ? WHERE bid_id = ?",
                [rec[c] for c in rec] + [now, bid_id],
            )
        else:
            conn.execute(
                "UPDATE bid_manage SET updated_at = ? WHERE bid_id = ?", (now, bid_id)
            )
        mid = existing["id"]
    else:
        cols = ["bid_id", "created_at", "updated_at", *rec.keys()]
        placeholders = ", ".join("?" for _ in cols)
        conn.execute(
            f"INSERT INTO bid_manage ({', '.join(cols)}) VALUES ({placeholders})",
            [bid_id, now, now, *rec.values()],
        )
        mid = conn.execute(
            "SELECT id FROM bid_manage WHERE bid_id = ?", (bid_id,)
        ).fetchone()["id"]
    conn.commit()
    return mid


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
        ORDER BY (o.deadline_date IS NULL), o.deadline_date ASC
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
        ORDER BY (o.deadline_date IS NULL), o.deadline_date ASC
        """
    ).fetchall()
    return [dict(r) for r in rows]


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
    print(f"qualifications: {quals}")
    print(f"bids: {bids}")
    print(f"bid_plans: {plans}")
    print(f"bid_manage: {manage}")
