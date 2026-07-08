# CLAUDE.md

Project spine for the **Public Sector Bidding API Platform** — a local proof of concept that
collects, stores, filters, and displays public sector bidding opportunities pulled from multiple
procurement APIs. Full brief: [support/brief.md](support/brief.md).

## What we're building

A single-machine PoC that:

1. Connects to **multiple** public sector procurement APIs via lightweight connector scripts.
2. Normalises each source's differing response format into one common record shape.
3. Stores **only active, relevant, open** opportunities in a lightweight local database (SQLite).
4. Keeps the data fresh — refresh/cleanup scripts update changed records, archive closed ones, and
   avoid cross-source duplicates.
5. Displays opportunities in a simple web UI with full-field filtering, keyword search, a per-record
   source indicator, a detail view, and clear open/closed/inactive status.

The goal is to **validate the workflow and data model**, not to ship a scalable production system.

## Success criteria (what "done" means)

- Retrieves bidding data from **more than one** API source.
- Stores relevant active opportunities locally; ignores/removes closed, expired, or irrelevant ones.
- Displays opportunities in a UI with filtering across **all** stored fields.
- Shows the source API for each opportunity.
- Runs locally with no production infrastructure.

## Stack & architecture

- **Backend:** simple local application server (Python — matches the existing connector script).
- **Database:** SQLite (single local file).
- **Connectors:** one script per API source; fetch → normalise → upsert into SQLite.
- **Frontend:** lightweight web UI (dashboard/list, filters, search, detail view).
- **Runtime:** local dev environment only.

Pipeline shape: `connector (per source) → normalise → SQLite → server/API → web UI`.

## Common record shape

Normalise every source into the fields owned by [db.py](db.py) (`COMMON_FIELDS`). We adopted the
richer ~18-field schema from [support/public_sector_bid_apis.md](support/public_sector_bid_apis.md)
rather than the original 12-field sketch, so connectors capture value, provenance, and raw payload:

`source`, `source_endpoint`, `ocid`, `notice_id`, `title`, `buyer_name`, `description`, `cpv_codes`,
`region`, `country`, `value_min`, `value_max`, `currency`, `published_date`, `deadline_date`,
`notice_type`, `status`, `url`, `raw_json`, `last_seen_at`.

Storage lives in `bids.db` (SQLite, gitignore-worthy). The upsert/dedupe key is **`(source, ocid)`** —
re-running a connector updates existing rows instead of duplicating. `db.record_source_run()` logs
when each source was last checked (provenance/freshness). `raw_json` keeps the source payload for
re-mapping/debugging.

## Data sources

- **Find a Tender (UK)** — implemented in [find_tender_filter.py](find_tender_filter.py).
  Uses the official OCDS API (`stages=tender`), filters client-side by CPV code and to notices still
  open for bids (`tenderPeriod.endDate` in the future). This is the reference pattern for new
  connectors.
- **At least one more source** is required to satisfy success criteria — not yet built.

### Relevance filter (CPV codes)

Scope is currently IT/software opportunities, defined by the CPV codes in
[cpv_codes.md](cpv_codes.md) (e.g. `72000000` IT services and sub-codes). Connectors strip trailing
zeros to a prefix so a group code matches all its sub-codes. The `TARGET_CPV`, `STAGE`, and
`OPEN_ONLY` knobs in the connector are the values a future UI will drive.

## Hard rules / constraints

- **PoC only.** No cloud hosting, auth, multi-user permissions, payments, advanced analytics,
  automated bid writing, or enterprise monitoring (brief §"Out of Scope").
- **Keep the DB lean** — store only data useful for reviewing/acting on *open* opportunities. No
  long-term historical archive.
- **Always record provenance** — every stored opportunity must carry its `source_api`, and refresh
  runs must record when each source was last checked.
- **Normalise before storing** — never let a source's raw shape leak into the DB or UI.
- **Dedupe across sources** where possible; upsert (update existing) rather than duplicate.

## Session workflow

`_session/` holds the working-memory scaffold (currently template placeholders):

- [_session/handover.md](_session/handover.md) — hot state; read first on resume. Replace, don't append.
- [_session/todo.md](_session/todo.md) — active queue only.
- [_session/progress.md](_session/progress.md) — append-only dated history; load on demand.

At session end: replace the handover hot-state, append a dated entry to `progress.md`, update `todo.md`.
Don't commit/push unless asked.

## Running

```bash
python3 find_tender_filter.py [days_back]          # default 120; fetch → normalise → upsert into bids.db, also prints
python3 find_tender_filter.py [days_back] --no-db  # print only, no DB write
python3 db.py                                      # create/inspect bids.db (row counts by source)
```

Done so far: SQLite persistence layer ([db.py](db.py)) + Find a Tender connector now upserts into it.
Still to build: a **second source** (Contracts Finder — OCDS, near drop-in), a refresh/cleanup script,
and the web UI.
