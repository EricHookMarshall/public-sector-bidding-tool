# Web UI — Public Sector Bidding Opportunities

React + Vite frontend for the PoC. Talks to the FastAPI JSON API (`api.py`) which
reads `bids.db`. The UI gives full-field filtering, keyword search, a per-record
source indicator, open/closed/unknown status badges, and a detail view (incl. the
raw source payload).

## Run (two terminals)

**1. API** (from the project root):

```bash
pip install -r requirements.txt        # first time only
uvicorn api:app --reload --port 8000    # or: python3 api.py
```

**2. UI** (from `web/`):

```bash
npm install        # first time only
npm run dev        # → http://localhost:5173
```

The Vite dev server proxies `/api/*` to the API on port 8000 (see `vite.config.js`),
so open **http://localhost:5173** and the UI loads live data. Make sure `bids.db`
has rows first (`python3 find_tender_filter.py`, then `python3 db.py` to confirm).

## Endpoints (served by `api.py`)

- `GET /api/meta` — filter options (sources, statuses, countries, regions,
  currencies, notice types), value bounds, and per-source freshness.
- `GET /api/opportunities` — filtered/searched list. Query params: `q`, `source`,
  `bid_status` (open/closed/unknown), `country`, `region`, `currency`,
  `notice_type`, `min_value`, `max_value`, `sort`, `order`.
- `GET /api/opportunities/{id}` — one full record, including parsed `raw_json`.
