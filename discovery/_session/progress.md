# Progress log

> Append-only. Most recent entries at the top. Each entry is a dated mini-pass retrospective: work done, decisions, open questions raised.
>
> Archival cadence: when this file passes ~800 lines, move the oldest dated entries to `_session/progress-archive.md` at end-of-session housekeeping. Hard ceiling ~1500 lines.

---

## 2026-07-09 — Discovery UI extended into the 6-stage journey shell

**Context.** Resumed the top-level project via `/resume-prompt`; the open decision was "data model
vs. app shell first" — user chose app shell. Per the approved architecture direction
(`docs/design/architecture.md`), the shell extends this discovery PoC rather than starting a new app.
First pass built a shell with Search live + generic scope-only placeholders for the other 5 stages;
user feedback ("not enough mock data for future stages to get a clear picture") drove a second pass
that ported the mockup's fully populated mock screens in too.

**Work done.**

- Added `web/src/journey.js`: single source of truth for the 6 stages (id, stepper metadata, build
  `state`, `maps`-to, full scope content), ported from `docs/design/journey-mockups.html`.
- Rewrote `web/src/App.jsx` from a Search-only page into the journey shell: sticky top bar, 6-stage
  stepper nav, hash-based routing (`#plan`, deep-linkable, back/forward works), ←/→ keyboard stepping,
  light/dark theme toggle, `VIEWS` map dispatching to per-stage components.
- Added `web/src/stages/`: `SearchStage.jsx` (old App.jsx logic, unchanged, lifted out),
  `MockStage.jsx` + `ScopeCard.jsx` (shared preview-screen chrome + scope card),
  `TriageStage.jsx` / `PlanStage.jsx` / `CompleteStage.jsx` / `ManageStage.jsx` / `LearnStage.jsx`
  (one populated mock screen per stage — qualification gates, pipeline board + capacity, compliance
  matrix + AI draft + evidence ledger, clarification register + pre-flight checklist, outcome +
  library updates — all with realistic UK-procurement-style data ported from the mockup).
  `StagePlaceholder.jsx` also exists from the first pass but is now unused/dead code.
- Rewrote `web/src/styles.css`: adopted the mockup's full design-token system (light + dark +
  `data-theme` override), added shell/stepper/scope/pager/mock-screen CSS; aliased legacy variable
  names (`--bg`, `--open`, etc.) so the original search CSS needed no changes.
- `web/index.html` title → "Bidpath — Public Sector Bidding".

**Verification (real runs).**

- `npm run build`: `✓ 31 modules transformed` (Search + shell + placeholders, first pass), then
  `✓ 38 modules transformed` (after adding the 5 mock stages) — both no errors.
- Backend + dev server both started for real: `python3 db.py` → 21 rows (FTS 19, CF 2);
  `uvicorn api:app --port 8000` up; `npm run dev` up; `curl :8000/api/meta` → `total: 21`;
  `curl :5173/api/opportunities` via Vite proxy → `count: 21`; page `<title>` confirmed via curl.
  Every new/changed module fetched from the dev server individually → HTTP 200, no Vite transform
  errors logged.
- Services stopped cleanly at session end; confirmed no leftover `uvicorn`/`vite` processes.
- **Not verified:** no browser tool available in this environment, so no actual click-through of the
  stepper/routing/theme-toggle was observed — only compile/transform/data-plumbing success. User was
  handed the running URL to check visually; that check has not yet happened as of this entry.

**Decisions.** Journey shell built as an extension of this discovery app (not a new codebase), per
the already-agreed architecture direction. Stage selection lives in the URL hash rather than adding a
router dependency. The 5 not-yet-built stages show fully populated, clearly-labelled preview screens
(not abstract scope text) so their intended shape is legible before they're wired to real data —
prompted directly by user feedback that scope cards alone didn't give "a clear picture."

**Open questions raised.** None new beyond what the top-level project already has open (shared data
model across the 6 stages — still not decided, and now the concrete blocker for wiring Triage/Plan/
etc. to real records instead of illustrative data).

**Next.** User to look at the running shell and flag anything wrong. `StagePlaceholder.jsx` is now
dead code — decide whether to delete or repurpose. Otherwise unchanged from before: `.gitignore`,
cross-source dedupe (both low priority).

## 2026-06-29 — UI rebuilt: live search, export, CPV dropdown, region labels, description on cards

**Context.** Resumed from refresh/cleanup session. Full pipeline working (FTS + CF → SQLite → FastAPI → React/Vite), DB had 14 rows. User asked for seven new features: add/remove CPV codes to searches, toggle sources, more result detail (description), adjust stages, region code definitions (UKM50 vs UK), export of results, date range controls.

**Work done.**

- Refactored `find_tender_filter.py` and `contracts_finder_filter.py`: both gained a parameterised `run(days, cpv_codes, stage, open_only, published_from, published_to, use_db)`. CLI `main()` unchanged. `ft.build_prefixes()` and `ft.to_api_datetime()` extracted for sharing.
- Built `sources.py` — connector registry (`find_a_tender`, `contracts_finder`), each with a `run` callable. New source = write connector + one registry line.
- Built `regions.py` — NUTS/ITL code glossary, 63-code UK coverage, prefix-fallback for unlisted codes (e.g. `UKM99 → "Southern Scotland (area UKM99)"`).
- Built `cpv_catalog.py` — 63-code IT/software/digital CPV catalogue grouped by CPV division (72/48/30/32/50). `catalog()` returns ordered list for the UI dropdown.
- Extended `api.py`: `POST /api/search` (live fan-out, per-source summary, isolated error handling), `GET /api/export` (CSV, mirrors current filters), `region_label` field on every row, `region_labels` + `search_options` + `cpv_catalog` in `/api/meta`, shared `_query_opportunities()` helper, `Depends()` for query params, CORS extended to `POST`.
- Rebuilt `web/src/App.jsx`: "Run a live search" collapsible panel (source checkboxes, stage + open-only toggle, last-N-days ↔ date-range toggle, CPV chip editor with catalogue dropdown + free-text + reset/clear, per-source results summary). Description snippet on every card. Region as human label with code in tooltip. `⤓ Export CSV` button. Region filter dropdown shows `UKM50 — Aberdeen City…`. `region_label` in detail modal.
- Updated `web/src/api.js`: `runSearch()` (POST), `exportUrl()` (CSV link).
- Updated `web/src/styles.css`: search panel, CPV chips/picker, export button, card description.
- **Bug fixed:** `cpv_catalog` is top-level in `/api/meta` but was read as `opts.cpv_catalog` (under `search_options`) → crash on panel render. Fixed to `meta?.cpv_catalog`.

**Verification (real runs).**

- All Python imports clean (api, sources, regions, cpv_catalog, connectors). ✓
- `regions.label("UKM50")` → Aberdeen City and Aberdeenshire; `"UK"` → United Kingdom; `"London"` passthrough. ✓
- `POST /api/search` tender, 14 days → FTS: scanned 94, kept 5, ok. ✓
- `POST /api/search` planning, 30 days, open_only=false → FTS: inserted 7 genuinely new rows. DB grew 14 → 21. ✓
- `GET /api/export?source=Contracts+Finder` → CSV, 22-column header, 2 correct CF rows. ✓
- `/api/meta` → `cpv_catalog: 63`, `region_labels: {UK: …, UKM50: …}`, `search_options.stages: [tender, planning, award]`. ✓
- Vite production build: `✓ 28 modules transformed`, no errors. ✓

**Decisions.** None new architectural decisions. The one structural choice was to use `POST /api/search` (not GET) for the live-fetch trigger because the body carries a variable-length CPV list. Export reuses `_query_opportunities()` exactly so export and list view can never diverge.

**Open questions raised.** None new. Cross-source dedupe and `.gitignore` remain the only deferred items.

**Next.** No blocking work. Optional: `.gitignore` (`bids.db`, `web/node_modules/`), CPV label badge on cards, third API source.

---

## 2026-06-29 — Refresh/cleanup script built (flag-don't-delete lifecycle)

**Context.** Resumed via `/resume-prompt`. Two sources live, `bids.db` = 14 rows (FTS 12, CF 2), full pipeline working. Active task: the refresh/cleanup script. Gating open decision #1 (hard-delete vs. flag closed rows) put to the user → **flag, don't delete**.

**Work done.**

- Built [refresh_clean.py](../refresh_clean.py). Two phases: (1) **refresh** — re-runs both connectors via `subprocess` (so they're reused exactly as-is; CF's own 1.5s page delay + 429 backoff apply, nothing duplicated); (2) **cleanup** — writes a persisted `lifecycle` flag on every row.
- `lifecycle` values: `open` (deadline future) / `closed` (deadline past) / `unknown` (no/invalid deadline) / `stale` (row's source refreshed this run but row not re-seen → dropped off the feed). `_open_closed()` mirrors `api._derive_open` so the persisted flag and the live API agree.
- **Staleness safety property:** staleness is judged *only* for sources that refreshed successfully (subprocess exit 0). A failed/rate-limited fetch never wrongly archives its rows. `--no-fetch` skips the network and re-flags only (trusts no source → no staleness).
- DB migration in [db.py](../db.py): `init_db()` now `ALTER TABLE`s a `lifecycle TEXT` column if missing. It lives **outside** `COMMON_FIELDS` so connectors never touch it — only the cleanup pass writes it.
- API ([api.py](../api.py)): `/api/meta` exposes `lifecycles`; `/api/opportunities` gains a `lifecycle` filter param and returns the field. UI ([web/src/App.jsx](../web/src/App.jsx)): Lifecycle dropdown filter + field in the detail view.

**Verification (real runs).**

- `python3 refresh_clean.py --no-fetch`: migration applied, all 14 rows flagged `open`. ✓
- `python3 refresh_clean.py` (full): both connectors re-ran (FTS 14 upserts→12 rows via shared-OCID collapse, CF 2; 0 inserted/all updated = idempotent), both sources trusted, all 14 re-seen → `open=14 closed=0 unknown=0 stale=0`. `source_runs` re-stamped (19:05 / 19:07). ✓
- Live API: `/api/meta` → `lifecycles=['open']`; `?lifecycle=open` → 14; `?lifecycle=stale` → 0. ✓
- **Branch unit-test** (in-memory DB, `rc.clean()` direct): open/closed/unknown/stale all correct, AND a non-refreshed source (CF) with old `last_seen_at` stayed `open` not `stale`. All 5 cases pass. ✓

**Decisions.**

- **Flag, don't delete** (open decision #1, settled by user). Rationale: brief favours lean/no-archive, but the API already derives open/closed live, so a non-destructive flag costs little, keeps provenance, and lets the UI show/hide closed+stale. Nothing removed; DB stays inspectable.
- Reuse connectors via **subprocess**, not a code refactor — zero risk to the two working connectors, true single-source reuse, and CF's self-throttling applies unchanged.
- `lifecycle` is the cleanup pass's signal; the genuinely *new* information it adds over the live API is **staleness** (a row the source stopped returning) — open/closed were already derivable.

**Open questions raised.** None new. Live data is all-open/fresh, so `closed`/`stale` are proven by unit-test rather than by production data (honest — no 120-day IT notices have lapsed yet).

**Next.** Cross-source dedupe (still low priority) and `.gitignore` on repo init remain the only open build items; success criteria are fully met. Optional: surface a `stale` badge on UI cards (currently only in the filter + detail view).

---

## 2026-06-29 — Contracts Finder connector built → success criteria met (2 sources)

**Context.** Resumed via `/resume-prompt`. Stack settled (FastAPI + React/Vite), `bids.db` had 12 rows from Find a Tender only. Active task: build source #2, Contracts Finder, to satisfy the "more than one API source" criterion.

**Work done.**

- Probed the live CF OCDS Search API. Confirmed: same OCDS release shape as FTS; pagination via `links.next` (cursor-based, identical handling); CPV carried at `tender.classification` (item-level usually empty); value frequently absent; window param is `publishedFrom` (FTS uses `updatedFrom`); notice URL is `.../Notice/{guid}` = id minus trailing `-<digits>`. Server-side CPV/keyword filter params are **ignored** by CF — filtering is client-side, like FTS.
- Built [contracts_finder_filter.py](../contracts_finder_filter.py): near drop-in of the FTS connector. **Imports** `cpvs_in`, `matches`, `PREFIXES`, `region_country`, `fetch` from `find_tender_filter` so CPV scope has a single source of truth. New bits: `is_open()` (parses offset-aware `endDate` with `datetime.fromisoformat`, correct across timezones; CF stamps `+01:00`), `notice_url()`, CF-specific `to_record()` (`source="Contracts Finder"`).
- Added polite throttling after hitting CF's rate limiter: `PAGE_DELAY=1.5s` between pages + `fetch_polite()` with exponential backoff on HTTP 429 (5 attempts, 5/10/15/20s).

**Verification (real runs).**

- `python3 contracts_finder_filter.py`: scanned 1128 tender-stage notices over 120 days / 12 pages, kept **2** open IT matches (IT Managed Services — The Careers and Enterprise Company; ERP system — East Durham College). Both genuinely IT, both `bid_status=open`. 2 inserted. ✓
- `python3 db.py`: total **14** — Find a Tender 12, Contracts Finder 2. ✓
- `source_runs`: CF run logged (scanned 1128, kept 2, stamped). ✓
- API layer: `/api/meta` → `sources=['Contracts Finder','Find a Tender']`, total 14; `/api/opportunities?source=Contracts Finder` → count 2, both open, source tags correct. ✓

**Decisions.**

- Reuse FTS logic by **import**, not copy — CPV scope (`TARGET_CPV`) stays single-sourced in `find_tender_filter`. Both connectors stay in lockstep on scope.
- Only **2** open CF IT notices is honest and correct: most 120-day IT notices have already closed, and the "store only open" hard rule forbids padding with closed ones. CF stream naturally exhausts at 12 pages.

**Notes / caveats.**

- CF rate-limits aggressively; a back-to-back idempotency re-run got a sustained 429 even after 5 backoff attempts. Idempotency is structurally guaranteed anyway (shared `db.upsert_opportunity` keyed on `(source, ocid)` + DB `UNIQUE` constraint, already proven for FTS) — not re-burned against the API.

**Open questions raised.** None new. Refresh/cleanup script and cross-source dedupe still deferred.

**Next.** Build the **refresh/cleanup script** — update changed records, archive/remove closed ones, record per-source last-checked time. Now meaningful since two sources exist.

---

## 2026-06-29 — FastAPI JSON API + React/Vite UI scaffolded and verified

**Context.** Resumed from the SQLite persistence session. `bids.db` had 12 rows from Find a Tender. Open question: what framework to use for the server/UI. User confirmed React + Vite as the preferred choice mid-session.

**Work done.**

- Settled the Server/UI open decision: **FastAPI JSON API + React/Vite frontend**.
- Built [api.py](../api.py): FastAPI app with three endpoints:
  - `GET /api/meta` — distinct filter values (sources, statuses, countries, regions, currencies, notice types), value bounds, per-source freshness from `source_runs`.
  - `GET /api/opportunities` — full-field filtered + keyword-searched list (q, source, bid_status, country, region, currency, notice_type, min_value, max_value, sort, order). Derives `bid_status` (open/closed/unknown) from deadline vs. now.
  - `GET /api/opportunities/{id}` — full record including `raw_json` parsed back to dict. CORS middleware allows the Vite origin.
- Scaffolded `web/` (Vite 6 + React 18):
  - `vite.config.js`: proxy `/api` → `http://127.0.0.1:8000`; dev server on `:5173`.
  - `web/src/App.jsx`: filter sidebar (keyword, per-field dropdowns, value range, sort/order, reset), opportunity cards (source tag, status badge, buyer, deadline, value), click-through detail modal (all stored fields + collapsible raw-payload viewer).
  - `web/src/api.js`: thin fetch wrapper for all three API endpoints.
  - `web/src/styles.css`: clean two-column layout, status badge colours, card hover, modal.
  - `web/index.html`, `web/src/main.jsx`: Vite entry points.
  - `web/package.json`, `web/.gitignore`.
- Added [requirements.txt](../requirements.txt) and [web/README.md](../web/README.md).
- Ran `npm install` (115 packages, 0 vulnerabilities).

**Bugs found and fixed.**

1. `sqlite3.Row` accessed after `conn.close()` in `/api/meta` and `/api/opportunities/{id}` → `Cannot operate on a closed database`. Fixed by materialising dicts before closing.
2. `Out of range float values are not JSON compliant: inf` — `tender.lotDetails.maximumLotsBidPerSupplier = inf` in at least one source payload. Fixed with `_json_safe()` helper that replaces `inf`/`nan` floats with `None` before serialisation.

**Verification (real runs).**

- `/api/meta`: total=12, sources=["Find a Tender"], value_bounds £833k–£4bn, source_runs row present. ✓
- `/api/opportunities?bid_status=open`: count=12, correct field types (value_max numeric). ✓
- `/api/opportunities/1`: bid_status=open, raw_json parsed, `inf` sanitized to None. ✓
- `/api/opportunities/9999`: HTTP 404. ✓
- `/api/opportunities?min_value=1000000000`: count=1. ✓
- Vite dev server: `index.html` served, JSX transforms clean, `/api` proxy returns count=12 via `localhost:5173`. ✓

**Decisions.**

- Stack settled: **FastAPI + React/Vite**. No HTML templating; clean API/frontend split.
- Vite proxy avoids CORS issues in dev and means the same fetch calls work if ever collocated behind one host.
- FastAPI's JSON encoder rejects `inf`/`nan` → sanitize at the serialisation boundary in `_row_to_dict`, not at ingest time (raw payload is stored verbatim in SQLite, sanitized on read).

**Open questions raised.** None new. Refresh/cleanup script and cross-source dedupe remain deferred.

**Next.** Build the Contracts Finder connector (`https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search`) — source #2, required for success criteria. OCDS shape, near drop-in from `find_tender_filter.py`.

---

## `2026-06-29` — SQLite persistence layer + Find a Tender connector wired to DB

**Context.** Resumed from bootstrap session. Connector existed and printed results; no DB, server, UI, or second source. Goal was to build persistence as the prerequisite for everything else.

**Work done.**

- Discovered [support/public_sector_bid_apis.md](../support/public_sector_bid_apis.md) — a full API catalogue that wasn't in the prior handover. Settled two open decisions from it.
- Built [db.py](../db.py): shared SQLite layer. `COMMON_FIELDS` table (20 columns), `upsert_opportunity()` keyed on `(source, ocid)`, `source_runs` freshness log (`record_source_run()`), `counts()` helper. `python3 db.py` creates and inspects `bids.db`.
- Refactored [find_tender_filter.py](../find_tender_filter.py): added `to_record()` (OCDS release → common shape), changed `main()` to upsert into `bids.db` and print. `--no-db` flag preserves print-only mode.
- Updated [CLAUDE.md](../CLAUDE.md): schema section now points to `db.COMMON_FIELDS` as the source of truth; run commands updated; "no DB exists yet" wording removed.
- Ran the connector twice to verify: first run → 12 inserted / 2 updated (14 matching notices; 2 shared an ocid, dedupe collapsed them); second run (idempotency) → 0 inserted / 14 updated, total stays 12. `source_runs` stamped correctly.

**Decisions.**

- Schema: **full ~18-field shape** from `support/public_sector_bid_apis.md` (not the old 12-field CLAUDE.md sketch). Richer fields include `value_min`/`value_max`/`currency`, `region`/`country`, `notice_type`, `raw_json`, `last_seen_at`.
- Dedupe/upsert key: **`(source, ocid)`**. Within-source deduplication works; cross-source dedupe (same notice on two platforms) deferred — unlikely between FTS and CF.
- Second source: **Contracts Finder** (OCDS, lower-value UK, no API key, near drop-in).
- Shared seam pattern confirmed: `db.py` is the single owner of schema + upsert; each connector maps to `COMMON_FIELDS` and calls `upsert_opportunity()`.

**Open questions raised.** Server/UI framework still unsettled (stdlib vs. Flask/FastAPI). Cross-source dedupe strategy (not yet needed). `bids.db` should be gitignored once a git repo is initialised.

**Next.** Build the Contracts Finder connector (`https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search`). OCDS shape — reuse `cpvs_in()`, `matches()`, open-only filter from FTS connector; map to same `COMMON_FIELDS`; call same `db` functions.

---

## `2026-06-29` — Project bootstrap: brief → CLAUDE.md → session scaffold

**Context.** First session. Greenfield repo containing only the PoC brief, a working Find a Tender connector script, a CPV code list, and the empty session-scaffold templates. Task was to read the brief and create CLAUDE.md, then fill in the session files.

**Work done.**

- Read [support/brief.md](../support/brief.md) (Public Sector Bidding API Platform PoC).
- Reviewed existing assets: [find_tender_filter.py](../find_tender_filter.py) (UK Find a Tender OCDS connector — fetches `stages=tender`, filters by CPV prefix + still-open, prints results) and [cpv_codes.md](../cpv_codes.md) (IT/software CPV scope).
- Wrote [CLAUDE.md](../CLAUDE.md): project spine — goals, success criteria, stack (Python + SQLite + per-source connectors + lightweight web UI), the 12-field common record shape, data sources, CPV relevance filter, hard rules, session workflow, run command.
- Replaced the three `_session/` template files with real current state.
- Pulled in two skills from `/Users/erichook-marshall/Downloads/Code/wa_poc/.claude/skills` and adapted them for this project at [.claude/skills/](../.claude/skills/): `end-session` and `resume-prompt`. Swapped the WhatsApp/TypeScript specifics (tsx dev server, cloudflared tunnel, `tsc`/`npm test`, Meta token, `PUBLIC_BASE_URL`, `/support`+`/docs`) for this project's Python stack and real docs (brief.md, cpv_codes.md, find_tender_filter.py).
- Ran `/end-session` discipline manually to close out (skills weren't loaded yet at the time).

**Findings / fixes.**

- The connector is **print-only** — it does not persist to a database yet. Storage is the first real build step.
- The brief requires **more than one** API source; only Find a Tender exists, so a second connector is needed to meet success criteria.
- No database, server, or UI exists yet — the PoC is at the connector-prototype stage.

**Decisions.** Adopt Python + SQLite + lightweight web UI per the brief's technical approach. Use `(source_api, reference_id)` as the natural upsert key (provisional). Treat Find a Tender as the reference pattern for future connectors.

**Open questions raised.** Which second API source to add; server/UI framework (stdlib vs. Flask/FastAPI); cross-source dedupe key.

**Next.** SQLite schema + persistence — define the common-record table and make the Find a Tender connector upsert into it instead of printing.

---
