# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-12` (session 24) — **G1 "bids we lost": the public feed can now answer it. Two real losses found.**

Full retrospective in [`progress.md`](progress.md) session-24. The load-bearing facts:

- **The bid library can't tell us what we won or lost, and `D365 Awards.xlsx` misleads** — every row is an award
  to a *different* company. An importer pointed at it writes false records into `awards`. FWF has bid ~27 times
  and recorded the outcome **twice**.
- **The OCDS APIs can't answer "who won?"** (no text search; CF *silently ignores* unknown params). Walking the
  API 429'd on **126/126 shards**. **Unlock = bulk data:** `src/cf_bulk.py` pulls the CDP daily CSVs from S3 —
  **47,797 notices in 12.3 min, 0 failed days**.
- **`src/bid_outcomes.py`** resolved the 27 folders. It **proposes, never asserts — nothing written to
  `bids.db`**. **CONFIRMED LOSS `22 UK BS (ACAS)`** (ref `PS25317`) → **Informed Solutions Ltd, £100k**.
  **PROBABLE `25 Home Office PPPT`** → Police Digital Services, £426,873 — **needs your eye**. Rest: 20 leads,
  5 no-match, 1 excluded. Two false positives caught + pinned in tests (`LOST` fell **9 → 2**).
- **`src/framework_positions.py`** — the radar said *"prepare"* for G-Cloud 15 while the library holds a
  **drafted response** (`⚠ Already in flight`); 6 agreements FWF works on were invisible to it. Ceiling pinned
  in tests: **a folder proves work, never membership.**
- **`docs/gca_findings/` (your GCA portal research) beats the folder guess:** FWF holds **three live DPS
  appointments** (AI DPS · RM6173 · Spark = APPOINTED). Not yet folded in — see Active task.
- **`make check` green: 118 backend tests** + doc-consistency + vite build.

## Active task

**Pick one — both were opened this session, both are cheap:**

1. **Fold the GCA portal facts into `framework_positions` as an authoritative overlay** (portal beats folder).
   `docs/gca_findings/FINDINGS.md` proves 3 live DPS appointments — the exact fact the folder view honestly
   refuses to infer. Stops the radar calling FWF "not a member" of DPSs it's appointed to. **Small, high value.**
2. **Mine tender refs/titles from INSIDE the bid documents** (`00 Bid Admin/FOR001 …xlsx`, `01 Customer
   Documents/`). 20 of 27 bids stall at "buyer seen, bid not identifiable" because folder names carry no subject
   words; `ref` is the only tier that works. **Feed is already cached (`src/.cache/`) — no crawling needed.**

Then **design the human confirm step** (see Open decision 1). Still open: **click G1/G2/G3 in a live browser**.

## Blockers / prerequisites

- **The bulk feed is CF/CDP only — devolved notices are absent.** Scottish (Forestry and Land Scotland,
  Scottish Water) and Welsh (Cardiff Uni) bids may never appear in it. A `NO MATCH` for those buyers is a
  **coverage gap, not a loss** — never record it as one.
- **⚠️ Plaintext portal passwords** in the bid library: `04 Portal Registrations/Portal Registration
  Tracker.xlsx` holds live portal credentials in clear text. The folder is gitignored so nothing leaked to
  git, but this needs raising with Emma — it's a credential-hygiene problem, not a code one.
- **Sell2Wales upstream is down**, not us — re-check periodically; no code fix possible on our side.
- **Empty *bid* pipeline is expected** (session-13 cleanse). Compliance register separate, seeded (19).
- **Live `GraphSharePoint`/`SharePointStore`** — no MS Graph here. **Azure:** subscription live, no resource
  group; Bicep/IaC (A1) is the real gap. Neither blocks the Active task.

## Open decisions

1. **How a confirmed outcome gets recorded.** `bid_outcomes.py` only proposes. Does an accepted verdict write
   to `bids.db` via Stage 6 (Learn) outcome capture, or via the G1 manual-award path (session 23)? Both exist;
   pick one so there's a single way in. **Never auto-import** — see the `D365 Awards.xlsx` near-miss.
2. **Cert pin maintenance** — `src/certs/sectigo_dv_r36_intermediate.pem` is shared by PCS + Sell2Wales;
   refresh instructions live in the module docstrings + `src/certs/README.md` if either site changes CA.
3. Carried from session 19 (untouched): compliance write-gating, file-content expiry extraction —
   see `progress.md` session-19 entry.

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
