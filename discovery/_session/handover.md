# Handover — hot state

> **Read first when resuming.** The one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> `_session/progress.md`; reach it on demand, it does not auto-load.

## Status

`2026-06-29` — **UI fully rebuilt with live-search, export, CPV dropdown, region labels, and description on cards.** The PoC now does everything originally asked for. Stack unchanged (FastAPI + React/Vite); architecture extended: the API was read-only and is now read+write (POST /api/search triggers live connector runs).

What happened this session:

- **Connector refactor:** `find_tender_filter.py` and `contracts_finder_filter.py` both gained a parameterised `run(days, cpv_codes, stage, open_only, published_from, published_to, use_db)` replacing hardcoded constants. CLI `main()` still works unchanged. `ft.build_prefixes()` and `ft.to_api_datetime()` extracted so CF can share them.
- **`sources.py`** — source registry: `{"find_a_tender": ..., "contracts_finder": ...}`, each with a `run` callable. Adding a third source is `write a connector + one line here`.
- **`regions.py`** — NUTS/ITL code glossary (`UKM50 → "Aberdeen City and Aberdeenshire"`), prefix-fallback for unlisted codes, `labels_for()` for the UI glossary. 63-code coverage across UK ITL1/2/3.
- **`cpv_catalog.py`** — curated 63-code IT/software/digital CPV catalogue (`code → description`), grouped by CPV division (72/48/30/32/50). Exposed via `/api/meta` → `cpv_catalog`.
- **`api.py` additions:** `POST /api/search` (fan-out live fetch, per-source summary, errors isolated per source), `GET /api/export` (CSV download, same query as list view), `region_label` field on every row, `region_labels` glossary + `search_options` + `cpv_catalog` in `/api/meta`. Shared `_query_opportunities()` helper so list + export never diverge. FastAPI `Depends()` for shared query params.
- **UI (App.jsx + styles.css):** "Run a live search" collapsible panel — source checkboxes, stage dropdown + open-only toggle, date-window toggle (last-N-days ↔ from/to), CPV chip editor with the catalogue dropdown + free-text entry + reset/clear, live per-source results summary. Description snippet on every card. Region shown as human label (`📍 Glasgow City`) with code in tooltip. `⤓ Export CSV` button on results header. Region filter dropdown shows `UKM50 — Aberdeen City…`. `region_label` in detail modal.
- **Bug fix this session:** `cpv_catalog` is a top-level field of `/api/meta` but was referenced as `opts.cpv_catalog` (under `search_options`) → crash on panel render. Fixed to `meta?.cpv_catalog`.

**Verification (real runs, this session):**

- `python3 -c "import api, sources, regions, cpv_catalog…"` → all imports OK.
- `regions.label("UKM50")` → "Aberdeen City and Aberdeenshire"; `regions.label("UK")` → "United Kingdom"; `regions.label("London")` → "London" (passthrough). ✓
- `POST /api/search` with `find_a_tender`, `days=14`, `stage=tender` → `scanned: 94, kept: 5, ok: true`. ✓
- `POST /api/search` with `find_a_tender`, `days=30`, `stage=planning`, `open_only=false` → `inserted: 7` new rows (planning-stage notices, genuinely different from tender-stage). ✓
- `GET /api/export?source=Contracts+Finder` → CSV, header correct (22 fields incl. `region_label`), 2 real CF rows. ✓
- `/api/meta` → `cpv_catalog: 63 entries`, `region_labels: {UK: …, UKM50: …, …}`, `search_options.stages: [tender, planning, award]`. ✓
- Vite production build: `✓ 28 modules transformed` — no errors. ✓
- DB: 14 rows → 21 after live searches (FTS 19, CF 2).

## Active task

**None blocking.** Everything the user asked for is built and working. Next items are optional polish / maintenance:

- **`.gitignore`** — add `bids.db`, `web/node_modules/` (the repo already exists; a `.gitignore` should be committed).
- **Session docs commit** — `CLAUDE.md` and `_session/` are the main docs; no commit made this session.
- **CPV badge on result cards** — `cpv_codes` is shown in card-meta but small; a labelled CPV chip (using `cpv_catalog`) would be richer.
- **Third API source** — `sources.py` registry makes it a small add (write a `run()` connector + one line).
- **Cross-source dedupe** — same notice on FTS and CF; low priority given value-band split.

## Open decisions

1. **Cross-source dedupe:** `(source, ocid)` dedupes within a source. Cross-source matching still unsettled — low priority.
2. **`.gitignore`:** `bids.db` and `web/node_modules/` should be gitignored now that the repo exists.

Settled: full ~18-field schema; `(source, ocid)` upsert key; two sources live (FTS + CF); FastAPI + React/Vite stack; flag-don't-delete cleanup via `refresh_clean.py`; live search via `POST /api/search`; CPV dropdown + region labels; export CSV.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [_session/todo.md](todo.md).
2. Confirm DB state: `python3 db.py` (should show `Find a Tender: 19`, `Contracts Finder: 2` → total 21 after planning-stage search this session).
3. Spin up the stack: `uvicorn api:app --reload --port 8000` + `cd web && npm run dev` → `http://localhost:5173`.
4. (Optional) Re-flag without network: `python3 refresh_clean.py --no-fetch`.

## Resume prompt

Paste this as the first message in a new session:

```text
Continuing work on the Public Sector Bidding API Platform PoC.

Read these on resume:
1. CLAUDE.md               (project spine — what we're building, stack, constraints, hard rules)
2. _session/handover.md    (hot state — current status, next step, open decisions)
3. _session/todo.md        (active queue)

Pull deeper context on demand: support/brief.md (full brief), cpv_codes.md (relevance scope),
find_tender_filter.py + contracts_finder_filter.py + db.py (connectors + DB layer),
sources.py (source registry), regions.py (NUTS/ITL glossary), cpv_catalog.py (CPV descriptions),
refresh_clean.py (refresh + lifecycle-flag cleanup), api.py (FastAPI JSON API),
web/src/App.jsx + web/src/api.js (React UI), web/src/styles.css,
_session/progress.md (cold dated history), support/public_sector_bid_apis.md.

The full PoC is built and working. No blocking work remains. At session end, REPLACE the
hot-state file, append a dated entry to _session/progress.md, and update _session/todo.md.
Don't commit/push unless asked.
```

## End-of-session checklist

When wrapping up:

1. **Kill any running services** (`pkill -f "uvicorn api:app"`, `pkill -f "vite"`).
2. **Replace** the Status line and Active task above with the new current state — don't append.
3. Append a dated entry to `_session/progress.md` (cold history): work done, decisions, open questions.
4. Update the `_session/todo.md` active queue (tick/re-order; completed items belong in `progress.md`).
