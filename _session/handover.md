# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-11` (session 17) — **Local/Azure hybrid review (58 findings) — security gate + tests + hygiene
cleared and committed.** Scope chosen with the user: fix the security gate, add the two missing test suites,
and sweep the ~35 mechanical hygiene findings; defer the big refactors + Azure infra. **Net −461 lines**
across 32 files, 4 commits (`5d5e317` backend · `33512fa` frontend · `b73a23f` skills/config · `43ed07a`
review docs). Highlights: CSV-injection neutraliser (S1); search-input bounds → 422 (S2); generic client
errors + server logging (S3); DEV-gated browser logs (S4); urlencoded + stage-validated connector queries
(S6); prompt-injection data fences (S7); provisional AI-date + unsupported-evidence flags surfaced in the UI
(S8/S9); clean non-JSON handling (S10). New `tests/test_outcome.py` + `tests/test_response.py` take the suite
**29 → 53**. Real behaviour fixes beyond cosmetics: `--stage` in preflight.py now genuinely differs
(readiness advisory vs final blocking); `_require_bid`/`_require_opp` helpers replace ~10 duplicated 404
guards; `IMMINENT_DAYS` shared from bidplan. Verified: `make check` green (53 tests + doc-consistency + vite),
plus a TestClient security smoke (S1/S2/S3/S6/S10 + the 404 paths). **DB unchanged: 24 opportunities, empty
pipeline.** Full narrative + the deferred list: `progress.md` and the review's remediation-status header.

⚠️ **User action — S5 (High):** the real Anthropic key in gitignored `src/.env` must be **rotated/revoked**
by a human — I can't rotate a credential. `.env.example` + `.gitignore` are already correct.

## Active task

**No task in flight.** The review's in-scope work is done + committed. Remaining, explicitly deferred
(now tracked in `state.yaml → deferred` and the review header):

1. **S5 key rotation** — user action, do this first (security).
2. **Structural refactors** — R1 (split ~1.6k-line `api.py` into routers), R3 (dedupe connector
   `to_record`/`run`), C3 (shared fetch/backoff helper). Extract R3/C3 together when convenient (or when a
   3rd source lands).
3. **Azure readiness A1–A9** — Functions host, Bicep/IaC, `GraphSharePoint` provider, `pyodbc`; mostly
   net-new and A3 is blocked without MS Graph. Ties into the parallel Azure track (Phases B+C done).
4. **C-series "Compliance & Renewals" view** ⭐ — still the highest founding-purpose payoff (`todo.md`);
   scope with the user first.

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
