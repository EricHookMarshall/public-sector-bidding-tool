# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-12` (session 22) — **G-series (GCA/frameworks intelligence) shipped — G3, G1, G2, in that order:**

- **G3 — How to supply** (`#supply`, 📘): curated read-only reference — 5 routes to market (Frameworks,
  Dynamic Markets, DPS, Catalogues, finding notices) + novice getting-started + help links. Source link per
  route + a `verified` date + re-verify disclaimer. `src/supply_reference.py`, `GET /api/supply/reference`.
- **G1 — Our contracts** (`#awards`, 🏆): FWF's OWN awards from the OCDS **award** packages (FTS + CF), matched
  by **Companies House number** (GB-COH) so no false records. New `awards` sibling table +
  `upsert_award`/`list_awards`. CH number is app config (`own_org` = `11934102`, lives in the gitignored
  bids.db), never hardcoded. `src/own_awards.py`; `GET/PUT /api/settings/own-org`, `/api/awards/board`, `/api/awards/refresh`.
- **G2 — Framework radar** (`#frameworks`, 📡): curated GCA agreements, but **lifecycle + recommendation
  computed LIVE against today** (act/pursue/prepare/maintain/watch/skip) — guards the RM6263 stale-listing
  failure. `src/frameworks_radar.py`, `GET /api/frameworks/radar`.
- **`make check` green: 98 backend tests** (was 80; +4 supply, +8 own-awards, +6 radar), doc-consistency, vite
  build (135.92 kB). Live via uvicorn: all endpoints OK; **G1 matcher fired on real live FTS data** (Softcat Plc).

## Active task

**No task in flight — G3/G1/G2 all shipped and committed to main. Two open threads:**

1. **A clean award refresh** — the first refresh 429'd (I'd hammered FTS in the smokes); backoff added to both
   sources + page pacing; a **4-year retry was running** at session close (check its output + `awards` count).
   FWF's real awards (likely NHS, 3–4yr back) only populate once a run completes un-rate-limited.
2. **"Bids we lost" (user req)** — NOT available from public OCDS (award notices name only the winner). Source
   it from the app's internal **Learn/outcome capture (Stage 6) + bid library**, not the connector — new work.
3. **Click the 3 new views in a live browser** — API + build verified only so far.

## Blockers / prerequisites

- **Sell2Wales upstream is down**, not us — re-check periodically; no code fix possible on our side.
- **Empty *bid* pipeline is expected** (session-13 cleanse). Compliance register separate, seeded (19).
- **Live `GraphSharePoint`/`SharePointStore`** — no MS Graph here; unrelated to this session's work.
- **Azure:** FWF Intern subscription live; no resource group yet — Bicep/IaC (A1) is the real gap.

## Open decisions

1. **What next** — chase the Sell2Wales bulk-download fallback, do F1 remainder (eTendersNI/G-Cloud),
   or start on G1–G3. Not decided.
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
4. `git status` for the true commit state (this doc doesn't duplicate it).

## End-of-session checklist

1. Kill services: `pkill -f "uvicorn api:app"; pkill -f vite`.
2. Update [`state.yaml`](state.yaml) first, then **replace** the Status + Active task above (don't append).
3. **Prepend** a dated entry to [`progress.md`](progress.md) (most-recent-first).
4. Update the [`todo.md`](todo.md) active queue; commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
