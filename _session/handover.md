# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-11` (session 14) — **Wave 2 correctness bugs cleared, committed + pushed at `33980dd`.**
All four Wave 2 items done: (1) FTS lexicographic deadline compare fixed — offset-aware `is_open` now
shared in `find_tender_filter.py`, re-exported by `contracts_finder_filter.py`, used by both connectors;
(2) `seed_learn_demo.py` 3.12-only f-string extracted (importable on ≤3.11); (3) seeders drop `LIMIT 1`
(`ORDER BY`+`fetchone` → identical on sqlite/SQL Server); (4) seeder dates now relative via `_day(offset)`
so the passed/imminent/expired spread stays realistic. Verified: `make check-fast` green (29 tests) +
seed→clear roundtrip against `bids.db`. **DB still 24 real opportunities, empty pipeline** (restored after
the roundtrip). Full narrative: `progress.md`.

_Parallel Azure track (untouched since session 11):_ Phases B (DB portability) + C (Entra ID auth) done
and locally verified; **Phase D (hosting scaffold) is the next Azure step** when the user returns to it.

## Active task

**No task in flight. Pick the next work item.** The code-review remediation queue is the natural
continuation now Wave 2 is clear (all in `todo.md`):

- **Wave 3 — doc/comment truth sweep** (cheap, batch in one pass): stale `discovery/.env` refs, "only Search
  is live" comments, post-port/model stale comments. Low-risk, high tidiness.
- **Wave 4 — dead/orphaned code removal** (cheap, batch): MockStage/ScopeCard/StagePlaceholder + CSS, unused
  imports/dead branches.
- **Wave 5/6** — right-sizing refactors + seam hardening (some coupling; `library.py` unknown-provider raise
  is a cheap High/Low win).

**Higher-payoff but needs scoping:** the **C-series "Compliance & Renewals" view** (the missed-renewal
failure the tool exists to prevent) — expiry plumbing already in `library.py`; gap is an org-level view.
**Scope with the user first** (what to track, where renewal dates come from, where the view lives). Detail
in `todo.md` → "C-series".

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
