# Handover — hot state

> **Read first when resuming.** The one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> `_session/progress.md`; reach it on demand, it does not auto-load.

## Status

`2026-07-09` — **Discovery UI is now the shell of the full 6-stage bidding journey**, not just the
Search screen. Top-level project decided "app shell first" (see top-level `_session/handover.md`);
this session extended the discovery front end into that shell rather than starting a separate app, per
`docs/design/architecture.md`. Backend/API/connectors untouched this session — only `discovery/web/`
changed. Search remains the one live, wired stage; Triage/Plan/Complete/Manage/Learn are illustrative
preview screens (real UK-procurement-style mock data, ported from `docs/design/journey-mockups.html`),
clearly banner-labelled as not-yet-built.

What happened this session:

- **`web/src/journey.js`** (new) — single source of truth for the 6 stages: id, stepper metadata,
  build `state` (`live`/`design`/`gap`), `maps`-to (which skill/PoC it corresponds to), and the full
  scope content (does / AI helps / human decides / in-v1 / out-later) ported verbatim from the
  approved mockup.
- **`web/src/App.jsx`** (rewritten) — was the Search-only page; is now the journey shell: sticky top
  bar + brand, 6-stage stepper nav, hash-based stage routing (`#plan` etc., deep-linkable, back/forward
  works), ←/→ keyboard stepping (ignored while typing in a field), light/dark theme toggle. Renders the
  active stage via a `VIEWS` map keyed by `journey.js`'s `component` field.
- **`web/src/stages/`** (new directory, 7 files):
  - `SearchStage.jsx` — the old App.jsx search UI, logic unchanged, lifted out so the shell can host it.
  - `MockStage.jsx` + `ScopeCard.jsx` — shared layout: browser-chrome screen + "Preview — illustrative
    data, not built yet" banner on the left, the scope card on the right.
  - `TriageStage.jsx`, `PlanStage.jsx`, `CompleteStage.jsx`, `ManageStage.jsx`, `LearnStage.jsx` — one
    populated mock screen per stage (qualification gates, pipeline board, compliance matrix + AI
    draft + evidence ledger, clarification register + pre-flight, outcome + library updates), all
    ported from the mockup so each future stage shows a concrete picture, not just prose.
  - `StagePlaceholder.jsx` — now unused (superseded by the per-stage mock screens) but left in place;
    not wired into `VIEWS`.
- **`web/src/styles.css`** — adopted the mockup's full design-token set (light + dark +
  `data-theme` override), added shell/stepper/scope/pager/mock-screen CSS; legacy variable names
  aliased (`--bg`, `--open`, …) so the original search-stage CSS needed no rewrite.
- **`web/index.html`** — title → "Bidpath — Public Sector Bidding".

**Verification (real runs, this session):**

- `npm run build` (after the shell rewrite, Search-only): `✓ 31 modules transformed`, no errors.
- `npm run build` (after adding the 5 mock stages): `✓ 38 modules transformed`, no errors.
- Backend + dev server started for real: `python3 db.py` → 21 rows (FTS 19, CF 2); `uvicorn api:app
  --port 8000` + `npm run dev` both came up; `curl :8000/api/meta` → `total: 21`; `curl
  :5173/api/opportunities` (via Vite proxy) → `count: 21`; page title confirmed via curl.
- Every new/changed module (`App.jsx`, `journey.js`, all 8 `stages/*.jsx`) fetched from the dev server
  → HTTP 200, no transform errors in the Vite log.
- **Not verified:** an actual in-browser click-through of the stepper/theme-toggle/routing — no browser
  tool available in this environment. Build + module-transform success is a strong but not complete
  proxy; the user was handed the running URL to look themselves.
- Services stopped cleanly at session end (`pkill -f "uvicorn api:app"`, `pkill -f vite`) — confirmed
  no leftover processes.

## Active task

**None blocking on the discovery side.** The shell exists and builds clean; the user has been asked to
look at it live and flag anything wrong. Likely next steps once they do:

- **User review of the shell** — click through all 6 stages, both themes, confirm nothing looks off
  (this is the natural next action — see also the top-level `_session/handover.md`).
- **Wire a second real stage** — Triage (B01) is the smallest real next build: gate logic against a
  real opportunity record needs the data model decision the top-level project still has open.
- **`StagePlaceholder.jsx` cleanup** — now dead code (superseded by per-stage mock screens); either
  delete it or repurpose it as the fallback for a stage that has no mock screen yet.
- Carried over, still true: `.gitignore` for `bids.db`/`web/node_modules/`; cross-source dedupe (low
  priority).

## Open decisions

1. **Data model** — the top-level project still has this open (shared bid record across all 6 stages).
   Blocks wiring Triage/Plan/etc. to real data; doesn't block further shell/preview work.
2. **Cross-source dedupe:** `(source, ocid)` dedupes within a source. Cross-source matching still
   unsettled — low priority.
3. **`.gitignore`:** `bids.db` and `web/node_modules/` should be gitignored now that the repo exists.

Settled: full ~18-field schema; `(source, ocid)` upsert key; two sources live (FTS + CF); FastAPI +
React/Vite stack; flag-don't-delete cleanup via `refresh_clean.py`; live search via `POST /api/search`;
CPV dropdown + region labels; export CSV; **journey shell built on top of the discovery UI** (not a
separate app), stage routing via URL hash, mock screens carry the approved-mockup content for stages
not yet built.

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
web/src/journey.js (6-stage metadata + scope content), web/src/App.jsx (journey shell),
web/src/stages/ (SearchStage = real; TriageStage/PlanStage/CompleteStage/ManageStage/LearnStage =
illustrative mock screens; MockStage/ScopeCard = shared layout), web/src/api.js, web/src/styles.css,
_session/progress.md (cold dated history), support/public_sector_bid_apis.md,
../docs/design/journey-mockups.html (source of the mock-screen content) and
../docs/design/architecture.md (why this became a shell, not a separate app).

The discovery engine (Search stage) is built and working; the app is now the shell of the full
6-stage journey, with 5 stages as labelled preview screens awaiting real data wiring. At session
end, REPLACE the hot-state file, append a dated entry to _session/progress.md, and update
_session/todo.md. Don't commit/push unless asked.
```

## End-of-session checklist

When wrapping up:

1. **Kill any running services** (`pkill -f "uvicorn api:app"`, `pkill -f "vite"`).
2. **Replace** the Status line and Active task above with the new current state — don't append.
3. Append a dated entry to `_session/progress.md` (cold history): work done, decisions, open questions.
4. Update the `_session/todo.md` active queue (tick/re-order; completed items belong in `progress.md`).
