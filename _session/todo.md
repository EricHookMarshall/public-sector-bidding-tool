# TODO — active queue

> **Unfinished work only.** Completed items are cold history — see [`progress.md`](progress.md)
> (most-recent-first, full dated retrospective per session). Everything through **session 13 is
> committed** (`9c31fa8`). When an item ships, note it in `progress.md` and delete it here.

## Feature backlog (needs scoping with the user)

- [ ] **C-series — "Compliance & Renewals" view** ⭐ (highest founding-purpose payoff — the missed-renewal
      failure the tool exists to prevent). **C3:** compliance docs already exist + are expiry-tracked in
      `library.py` (*Company Credentials*; ISO reads **EXPIRED 2025-10-31** in live data) — gap = structured
      renewal dates for the rest + an **org-level** view (today buried per-bid in Complete). **C4:**
      framework/contract membership-period tracker (RM6263-expired precedent). **Scope with the user first.**
- [ ] **C1 — clarifications: discoverability + AI dedupe** — the FOR003 register exists on Manage (click a
      bid); make the drill-in obvious (board shows only a count). NEW: AI-ingest incoming CQs, dedupe, flag
      "already answered by CQ #n".
- [ ] **C2 — per-bid workspace + slim per-bid KB** — opportunity visible, edits saved, a bid-specific KB the
      AI grounds on. Net-new; aligns with the `skills/` 3-library design. Needs a design pass.
- [ ] **F-series — more sources / search** — F1: Public Contracts Scotland, Sell2Wales, eTendersNI, G-Cloud
      behind the normalise→`bids.db` seam. F2: multi-criteria search. **F5: ITT ingestion → auto-build the
      compliance matrix** (biggest; matrix schema is already per-bid dynamic, just no parser).

> **Noted (already built — no action):** Modern Slavery is already a Manage pre-flight item + a library
> credential ("Anti-Bribery & Modern Slavery Policies") — don't re-add.

## Harness follow-ups (from the 2026-07-10 harness-design review — `docs/harness_design/`)

- [x] **Canonical verification command** (2026-07-11) — `make check` (`scripts/check.sh`): backend
      pytest (deadline / CPV / qualification / preflight / auth-roles + app-construct = **29 tests**) →
      doc-state consistency guard → Vite build. `make check-fast` skips the build. `tests/` + `pytest.ini`
      + `requirements-dev.txt`. **Next extension:** add live-source tests behind an explicit flag (rung 4).
- [ ] **Fold the `skills/` B00–B07 chain into the app** — declare `src/` domain vocab canonical (done in
      CLAUDE.md), align skill enums/handoff schemas to it, route skill calculations through shared code.
      Resolve the duplicate `fwf-tender-sweep` skill-name collision (two `tender_sweep/` variants). Parked
      until the chain is actually folded in.

## Code-review remediation — Waves 2–6 (open)

> Two reviews in [`docs/code_reviews/`](../docs/code_reviews/). **Waves 0 (security) + 1 (Azure-promotion)
> are DONE** — all 12 items verified in commit `0f35c70`; detail in `progress.md`. Waves 2–6 below are open,
> each item independently pickable unless a `↳` notes a coupling.

### Wave 2 — Correctness bugs ✅ CLEARED (session 14, committed `33980dd`)

All four done — FTS lexicographic deadline compare (shared offset-aware `is_open`), `seed_learn_demo.py`
3.12-only f-string, seeder `LIMIT 1` portability, seeder hard-coded dates. Retrospective in `progress.md`.

### Wave 3 — Doc/comment truth sweep ✅ CLEARED (session 15)

Done: `discovery/.env`→`src/.env` (the only real refs were `.env.example:1` + `api.py:28`; config.py/
SettingsView refs were false records; journey.js refs removed with the `asset` data); "only Search is live"
comments (App.jsx, journey.js header, SearchStage.jsx); `llm.py` opus→`claude-haiku-4-5` default;
db.py "12-field sketch"/`sqlite3.Row` + api.py SQLite-only/3-endpoint docstring; `complete_ai.py` local
import hoisted to top (**verified no cycle exists** — the "avoids a cycle" comment was wrong).

### Wave 4 — Dead / orphaned code removal ✅ CLEARED (session 15)

Done: deleted MockStage + ScopeCard + StagePlaceholder + their CSS; removed the orphaned `scope`/`asset`
data from `journey.js` + slimmed `STATE_MAP` to the pill class; `StagePlaceholder`'s never-rendered App.jsx
fallback → minimal slug guard. Unused imports: `clarification.py` `datetime`, `PlanStage.jsx` `useMemo`;
`db.py:1024` `bids` local renamed (shadowed the Table); `SearchStage.jsx` no-op spread collapsed.
**Not done (false records):** `TriageStage` "dead branch" couldn't be located; `SearchStage:268`
eslint-disable is *not* inert (suppresses a real `seeded`-dep warning) — both left as-is.

### Wave 5 — Right-sizing / consistency refactors (quality; some coupling)

- [ ] **Consolidate `web/src/api.js` error handling** (`:87-94` ×8 vs `sendJSON:299-314`) — route stage
      helpers through one JSON helper; make `getJSON:49-53` surface server `detail`. **Med.**
- [ ] **Collapse the 5 near-identical `db.py` upserts** (`:559-907`) into one `_upsert_one` + thin wrappers;
      the place to add the unique-violation retry. **Med.**
- [ ] **Extract shared web formatters** — `deadlineBadge`/`daysUntil`/`fmtMoney` duplicated 2-3× across
      stages; Complete hard-codes 7/14 thresholds while siblings read `imminent_days` from the server →
      silent disagreement on "urgent". `web/src/format.js`. **Med.**
- [ ] **De-dupe backend twins** — `api._derive_open` == `refresh_clean._open_closed` (→ `db.py`); connector
      `to_record`/`run`/`main` near-verbatim (extract when a 3rd source lands); cache
      `LocalMirrorProvider.items()` (xlsx parsed twice per `/api/library` request). **Low/Med.**

### Wave 6 — Deferred-behind-seam hardening + advisory security

- [x] **Raise on unknown `LIBRARY_PROVIDER`** (session 15 — **was already done**; false record). `src/library.py`
      `get_provider()` (now `:422-438`) already raises loudly with valid options, mirroring `llm.get_provider()`.
- [ ] **Advisory auth hardening** — `auth.py:216-219` generic 401 (log the real reason); catch
      `jwt.PyJWTError` not bare `Exception` (JWKS outage ≠ 401 → 503); `authConfig.js:31` use `sessionStorage`
      not `localStorage`; add `.env`/`.env.*`/`!.env.example` to `web/.gitignore`. **Low.**

## Surfaced / open (parallel tracks + polish)

- [ ] **Azure Phase C tail — live MSAL browser sign-in** — redirect round-trip needs a real dev-tenant app
      reg (no emulator). Supply `VITE_AAD_*` + `AAD_TENANT_ID`/`AAD_API_CLIENT_ID`, set `LOCAL_AUTH_BYPASS=0`,
      sign in, confirm the Bearer reaches the API and role-gating works.
- [ ] **Azure Phase D — hosting scaffold** per `docs/design/azure-target.md` (needs an Azure subscription).
- [ ] **Azure OpenAI provider** — `src/llm.py` has a documented skeleton, not implemented; build when Azure
      access is provisioned (sequenced into Phase E).
- [ ] **Cross-source dedupe** — `(source, ocid)` dedupes within a source; cross-source matching (same notice
      on FTS + CF) not yet handled. Low priority given the value-band split.
- [ ] **AI-draft provenance persistence** — win-themes/evidence shown in the UI but not saved with the answer.
- [ ] **Parked polish** — CPV label badge on cards · lifecycle (`stale`/`closed`) badge on cards · widen CPV
      scope beyond IT/software (`TARGET_CPV` + `src/cpv_catalog.py`) · a 3rd source via `src/sources.py`.
