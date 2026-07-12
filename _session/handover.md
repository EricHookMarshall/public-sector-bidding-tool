# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-12` (session 21) — **Two small F-series follow-ons shipped, both from session 20's punch list:**

- **Search partition-error surfacing** — `/api/search` now passes `incomplete: true` + a `failed_partitions`
  count through on a partial source run (e.g. Sell2Wales's per-partition degrade), so a live Wales outage is
  visible instead of masquerading as "kept 0". Raw `partition_errors` (upstream detail) are deliberately kept
  server-side-only, matching the endpoint's existing don't-leak-internals policy. UI: an amber "⚠ partial —
  N partition(s) unavailable upstream" note in the Search run-summary (`SearchStage.jsx`), new `.warn` style.
- **F6 — hide closed opps by default** — `_query_opportunities` now drops `bid_status == "closed"` by default
  unless the opp is "in flight" (in `triage_selections`, has a qualification, or has a bid) — new
  `_inflight_opportunity_ids()` helper mirrors the Triage pull-gate carve-out. An explicit `bid_status` filter
  always overrides. Applies to both the list view and CSV export (same query). UI: a "Hide closed (unless in
  pipeline)" checkbox, checked by default, auto-disabled when Bid-status is explicitly filtered.
- **Live-verified against real `bids.db`** (24 opps, read-only): `hide_closed=false` → 24 (14 open/6 unknown/4
  closed); default → 20 (the 4 closed dropped); `bid_status=closed` override → 4, correctly bypassing the hide.
- **`make check` green: 80 backend tests** (74 + 2 partition-surfacing + 4 hide-closed), doc-consistency, vite
  build (133.49 kB). `bids.db` untouched — verification was GET-only, no live search run.

⚠️ **Not committed.** 3 modified (`src/api.py`, `web/src/stages/SearchStage.jsx`, `web/src/styles.css`) + 2
new test files (`tests/test_search_surfacing.py`, `tests/test_search_hide_closed.py`), all on disk only.

## Active task

**No task in flight — both punch-list items are done; next step is the user's call.**

1. **Commit this session's work** (your call — nothing staged yet; session 20's F1 connectors are already
   committed/pushed at `7c954e2`, so this would be a clean, separate commit).
2. **Sell2Wales bulk-download fallback** — their official monthly JSON/XML/CSV, but it's behind an
   aspx-postback form (`__VIEWSTATE` present), not a clean GET. Bigger lift.
3. **F1 remainder** — eTendersNI (different platform, Jaggaer), G-Cloud as a source.
4. Or pick up **G1–G3** (GCA/frameworks intelligence — user reqs from session 19, not yet built).

## Blockers / prerequisites

- **Sell2Wales upstream is down**, not us — re-check periodically; no code fix possible on our side.
- **Empty *bid* pipeline is expected** (session-13 cleanse). Compliance register separate, seeded (19).
- **Live `GraphSharePoint`/`SharePointStore`** — no MS Graph here; unrelated to this session's work.
- **Azure:** FWF Intern subscription live; no resource group yet — Bicep/IaC (A1) is the real gap.

## Open decisions

1. **What next** — commit this session's work, chase the Sell2Wales bulk-download fallback, do F1
   remainder (eTendersNI/G-Cloud), or start on G1–G3. Not decided.
2. **Cert pin maintenance** — `src/certs/sectigo_dv_r36_intermediate.pem` is shared by PCS + Sell2Wales;
   refresh instructions live in the module docstrings + `src/certs/README.md` if either site changes CA.
3. Carried from session 19 (untouched this session): compliance write-gating, file-content expiry
   extraction — see `progress.md` session-19 entry.

## Auth quick-reference

Unchanged this session. Local dev default `LOCAL_AUTH_BYPASS=1`. Full config: `src/.env.example` +
`web/.env.example`.

## Start-of-session checklist

1. Read [`state.yaml`](state.yaml), [`CLAUDE.md`](../CLAUDE.md), this file, and [`todo.md`](todo.md).
2. Confirm DB: `python3 src/db.py` → `opportunities: 24` (unchanged this session — verification was GET-only).
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev`. Search now
   default-hides closed opps (toggle in the Filters panel) and shows a partial-results warning if a source
   (e.g. Sell2Wales) returns `incomplete`.
4. `git status` will show 3 modified + 2 new files from this session, uncommitted.

## End-of-session checklist

1. Kill services: `pkill -f "uvicorn api:app"; pkill -f vite`.
2. Update [`state.yaml`](state.yaml) first, then **replace** the Status + Active task above (don't append).
3. **Prepend** a dated entry to [`progress.md`](progress.md) (most-recent-first).
4. Update the [`todo.md`](todo.md) active queue; commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
