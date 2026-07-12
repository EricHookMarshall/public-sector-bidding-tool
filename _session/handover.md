# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-12` (session 18) — **Triage is now an explicit "pull" gate — only opps the user picks reach the
board.** Bug the user spotted: the Triage board ran the *same unfiltered query as Search*, so all 24 stored
opportunities showed up as "Untriaged" by default. Fix (mirrors the existing `triage_dismissals` side-table
pattern so Search stays untouched): new **`triage_selections`** table + `selected_opportunity_ids()` /
`set_triage_selected()` helpers ([src/db.py](../src/db.py)); the board now skips any opp that isn't
selected **and** isn't already worked (`triage_board` in [src/api.py](../src/api.py) — the OR-worked clause
keeps existing Go/No-go decisions from vanishing); new `PUT /api/opportunities/{id}/triage-select`; the
Search "Triage this →" button now actually pulls the opp in before navigating
([SearchStage.jsx](../web/src/stages/SearchStage.jsx)); Triage empty-state copy updated
([TriageStage.jsx](../web/src/stages/TriageStage.jsx)). Verified: `make check` green (53 tests + doc + vite);
TestClient select→board→deselect round-trip, worked-item backward-compat, and 404 on missing opp; **live
`/api/triage/board` on the real `bids.db` now returns 0 items (was 24).** DB gains an empty `triage_selections`
table; **still 24 opportunities, empty pipeline.**

⚠️ **Gotcha that wasted the first pass:** the running `uvicorn` had been started **without `--reload`**, so
it kept serving pre-change code and the user's browser still showed 24. Restarted with `--reload`; endpoint
now correct. If a code change "doesn't take", check the server was started with `--reload` first.

⚠️ **User action — S5 (High, still open):** the real Anthropic key in gitignored `src/.env` must be
**rotated/revoked** by a human — I can't rotate a credential. `.env.example` + `.gitignore` are already correct.

## Active task

**No task in flight.** The pull-gate is shipped + committed. Remaining, explicitly deferred
(tracked in `state.yaml → deferred`):

1. **S5 key rotation** — user action, do this first (security).
2. **Structural refactors** — R1 (split ~1.6k-line `api.py` into routers), R3 (dedupe connector
   `to_record`/`run`), C3 (shared fetch/backoff helper). Extract R3/C3 together when convenient (or when a
   3rd source lands).
3. **Azure readiness A1–A9** — Functions host, Bicep/IaC, `GraphSharePoint` provider, `pyodbc`; mostly
   net-new and A3 is blocked without MS Graph. Ties into the parallel Azure track (Phases B+C done).
4. **C-series "Compliance & Renewals" view** ⭐ — still the highest founding-purpose payoff (`todo.md`);
   scope with the user first.

*(Follow-on the user may want next: the board's ✕ still `dismiss`es (reversible hide) rather than
de-selecting; in a pull model these overlap. Left as-is deliberately — flag if you want ✕ to remove the
selection outright.)*

`make check` / `make check-fast` (`scripts/check.sh`) is the canonical health baseline — run before
committing nontrivial changes.

## Blockers / prerequisites

- **Empty pipeline is expected, not a regression** — the session-13 cleanse removed the seeded demo bids
  so a real bid could be pushed through. Plan/Manage/Complete/Learn boards read 0 bids until an
  opportunity is triaged to "Go". Re-seed with `seed_*_demo.py --clear` for reviewable demo data.
- **Live `GraphSharePoint`** — no MS Graph in this environment; Complete runs on the sanctioned local
  export via `LocalMirror`. **Azure Phase D** needs a subscription. Don't fake either — see CLAUDE.md hard rules.

## Open decisions

1. **What next** — C-series (scope first) vs U-series polish vs Wave 2 bugs vs Azure Phase D. Not decided.
2. **AI-draft provenance persistence** — save the evidence/win-themes alongside the saved answer? (Not yet.)
3. **Live `GraphSharePoint` / Azure OpenAI timing** — build behind the existing seams when access is provisioned.

## Auth quick-reference

Local dev default is `LOCAL_AUTH_BYPASS=1` (API unauthenticated, synthetic Admin) + `VITE_AAD_*` unset
(SPA no sign-in gate) → runs like sessions 1–9. To exercise role-gating locally, add `LOCAL_AUTH_ROLE=User`.
To turn auth on, set `LOCAL_AUTH_BYPASS=0` + `AAD_TENANT_ID` + `AAD_API_CLIENT_ID` (+ all three `VITE_AAD_*`).
Full config lives in the templates: `src/.env.example` (API) and `web/.env.example` (SPA).

## Start-of-session checklist

1. Read [`state.yaml`](state.yaml), [`CLAUDE.md`](../CLAUDE.md), this file, and [`todo.md`](todo.md).
2. Confirm DB: `python3 src/db.py` → `opportunities: 24`, **empty pipeline** (expected — see Blockers).
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev` → <http://localhost:5173>.
4. Complete's library reads the gitignored export at `knowledge/SharePoint Folder/Bids/`; absent = "library
   not connected" (honest, not a bug). `src/.env` holds the Anthropic key for AI drafting.
5. Dual-mode DB defaults to local sqlite; SQL Server path via `docker compose up -d --wait db` + `DB_URL`.

## End-of-session checklist

1. Kill services: `pkill -f "uvicorn api:app"; pkill -f vite`.
2. Update [`state.yaml`](state.yaml) first, then **replace** the Status + Active task above (don't append).
3. **Prepend** a dated entry to [`progress.md`](progress.md) (most-recent-first).
4. Update the [`todo.md`](todo.md) active queue; commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
