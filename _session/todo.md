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

### Wave 2 — Correctness bugs (real defects, not just Azure)

- [ ] **FTS deadline kept by string compare** (`src/find_tender_filter.py:155`) — `end >= now.isoformat()`
      is lexicographic; an offset-stamped deadline already past UTC can be stored as **open** — in a deadline
      tool. CF already solves this with a parsed offset-aware `is_open`; move `is_open` into find_tender and
      use it in both connectors. **Med.** `↳` also removes duplication (Wave 5).
- [ ] **`seed_learn_demo.py:115` is Python-3.12-only** — nested same-type quotes in an f-string (PEP 701);
      `SyntaxError` at import on ≤3.11. Extract the fragment, or declare `requires-python>=3.12`. **Med.**
- [ ] **Seeders use `LIMIT 1`** (`seed_plan/complete/manage/learn_demo.py`) — sqlite-only; needs
      `OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY` for SQL Server. **Low** (dev-local seeders).
- [ ] **Seeder demo dates hard-coded to ~July 2026** — the passed/imminent/done alert spread decays to
      all-OVERDUE within weeks. Compute from `date.today()` offsets. **Low.**

### Wave 3 — Doc/comment truth sweep (cheap; batch in one pass)

- [ ] **Stale `discovery/.env` refs** (7×: `src/.env.example:1`, `config.py:4`, `api.py:26,455`,
      `SettingsView.jsx:111`, `journey.js:72,132`) — dir doesn't exist; `.env` lives in `src/`. Two are
      user-facing UI copy → make host-neutral. **Med.**
- [ ] **"only Search is live" stale comments** (`App.jsx:19`, `journey.js:8-12`, `SearchStage.jsx:1`,
      `styles.css:207-209` banner) — all six stages are live; these contradict the code. **Med/Low.**
- [ ] **Post-port / model stale comments** — `llm.py:5` says Opus default (actually `claude-haiku-4-5`);
      `db.py:12-13,536` + `api.py:164` still say "sqlite3.Row"/"12-field sketch"; `complete_ai.py:88` claims
      a non-existent import cycle; `api.py:2-16` docstring lists 3 of ~30 endpoints + "SQLite" not dual-mode. **Low.**

### Wave 4 — Dead / orphaned code removal (cheap; batch)

- [ ] **Delete MockStage + ScopeCard + StagePlaceholder + their CSS** (`web/src/stages/MockStage.jsx`,
      `ScopeCard.jsx`, `StagePlaceholder.jsx`; `styles.css:211-230,298-314`; strand the `scope`/`asset` data
      in `journey.js:24-193`) — preview-era orphans imported by nothing. **Med.**
- [ ] **Unused imports / dead branches** — `clarification.py:26` unused `datetime`; `PlanStage.jsx:8` unused
      `useMemo`; `TriageStage.jsx:103-104` dead branch; `db.py:1015` `bids` local shadows the Table;
      `SearchStage.jsx:88` no-op spread + `:259` inert eslint-disable. **Low.**

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

- [ ] **Raise on unknown `LIBRARY_PROVIDER`** (`src/library.py:388`) — currently silently falls back to
      LocalMirror, so a typo'd `graph_sharepoint` reads the absent mirror and reports "not connected" with no
      hint. Mirror `llm.get_provider()`'s raise-with-valid-options. Cheap; do it now. **High/Low.**
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
