# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-10` (session 13) — **Journey feature-complete (all 6 stages real, committed at `9c31fa8`).**
Cleared the session-12 UI-walkthrough quick-wins queue: team roster (S5), search defaults (S3), Triage
card board (U1), and a reversible "dismiss from Triage" (U2) all shipped, committed, and live-verified
(user confirmed S5/S3/U1 in the browser). The demo bids were cleansed → **24 real opportunities, empty
pipeline**, so the user can push a real test bid end-to-end. Full session narrative: `progress.md`.

_Parallel Azure track (untouched since session 11):_ Phases B (DB portability) + C (Entra ID auth) done
and locally verified; **Phase D (hosting scaffold) is the next Azure step** when the user returns to it.

## Active task

**Quick-wins queue is cleared. Next: the C-series "Compliance & Renewals" view — but SCOPE IT WITH THE
USER FIRST (don't start cold).** Highest founding-purpose payoff (the missed-renewal/expiry failure the
tool exists to prevent). The expiry plumbing already exists in `library.py` (*Company Credentials*; ISO
already reads **EXPIRED 2025-10-31** in live data) — the gap is an **org-level** view (today the ledger is
buried per-bid in Complete). **C3** = structured renewal dates for the rest of the credentials + an
org-level compliance view; **C4** = framework/contract membership-period tracker (RM6263-expired
precedent). Scoping questions to ask: what exactly to track, where renewal dates come from, and where the
org-level view lives (new stage/screen vs a Settings-adjacent page). Detail in `todo.md` → "C-series".

**Lower-priority alternatives if the user redirects:** U-series polish on the new Triage board · the Wave 2
correctness bugs (FTS lexicographic deadline compare — note `make check`'s deadline tests document the
correct offset-aware behaviour the fix should adopt; the 3.12-only f-string in `seed_learn_demo.py`) ·
Azure Phase D hosting scaffold (needs a subscription).

**New this session:** `make check` (`scripts/check.sh`) is the canonical health baseline — 29 backend
tests (deadline / CPV / qualification / preflight / auth-roles + app-construct) + a doc-consistency guard
+ the Vite build. Run it before committing nontrivial changes.

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
