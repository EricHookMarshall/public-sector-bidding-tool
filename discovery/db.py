#!/usr/bin/env python3
"""
Shared SQLite layer for the Public Sector Bidding API PoC.

One local file (bids.db), one common-record table, one idempotent upsert.
Every connector (Find a Tender, Contracts Finder, ...) maps its source's raw
response into the COMMON_FIELDS shape below and calls upsert_opportunity().

Schema follows support/public_sector_bid_apis.md (the richer ~18-field shape),
not the older 12-field sketch in CLAUDE.md.

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


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn):
    cols = ",\n        ".join(f"{f} TEXT" for f in COMMON_FIELDS)
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
