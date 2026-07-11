# Local / Azure Hybrid Code Review — Merged

Date: 2026-07-11

## Remediation status (updated 2026-07-11)

Worked in three waves against a green `make check` (now 53 backend tests, up from 29).
Scope for this pass: **security gate + tests + hygiene**. Structural refactors and the
Azure-readiness block were deliberately deferred (see below).

**Resolved (this pass):**

- **Security gate — S1–S4, S6–S10 done.** CSV neutralisation (S1), search input
  bounds/validation → 422 (S2), generic client errors + server-side logging (S3),
  DEV-gated browser logging (S4), URL-encoded + stage-validated connector queries (S6),
  prompt-injection data-boundary fences (S7), provisional AI-date flagging (S8),
  evidence cross-check (S9), clean non-JSON-body handling (S10). Full rate-limiting/
  queueing for S2 was scoped out as heavier infra — caps + validation landed.
- **Tests — T1, T2 done.** New `tests/test_outcome.py` + `tests/test_response.py`.
- **Hygiene — all N/C/CL/U/O/R2/R4 in scope done.** Includes N1–N7, C1–C10, CL1–CL4,
  U1–U5, O1–O4, R2, R4. `U2` was resolved by making `--stage` genuinely differ
  (readiness advisory vs final blocking) rather than deleting the documented flag.

**Your action — S5 (High):** the real Anthropic key in the gitignored `src/.env` must be
**rotated/revoked** by a human; the tooling side (`.env.example`, `.gitignore`) is already
correct. Not closeable in-session.

**Deferred by scope (separate follow-up):** the structural refactors **R1** (split
`api.py`), **R3** (dedupe connector orchestration), **C3** (shared fetch/backoff helper);
and the **Azure migration-readiness** block **A1–A9** (Functions host, Bicep/IaC,
`GraphSharePoint` provider — blocked without MS Graph, `pyodbc`). **R5/R6** are "no action"
by design. This review stays active (not archived) until those are addressed.

---

Sources:

- `2026-07-11-local-azure-hybrid-review-gpt-5.md`
- `2026-07-11-local-azure-hybrid-review-opus-4-8.md`

This is the canonical merged review. Findings were deduplicated only when they describe the same underlying defect and remediation. Similar findings about the same file were retained when they concern different failure modes. Severity below preserves the source review's assessment; `Low–Medium` is also preserved where used by the source.

## Deduplication record

Four genuine duplicate groups were collapsed:

1. `src/api.py:21` — unused `datetime` import appeared in both reviews.
2. `src/api.py:358-362` — raw connector exception leakage appeared in both reviews.
3. `src/cpv_catalog.py:10-12,88-90` — the misleading docstring and orphaned `label()` describe one underlying unused API and are one finding here.
4. The connector `run()` duplication appeared under both Cleanliness and Right-sizing in the Opus review; the more complete Right-sizing formulation subsumes the narrower cleanliness observation.

No other findings were merged. In particular, connector formatting, retry behaviour, URL construction, logging, configuration, parsing, and structural duplication are separate defects.

## Executive summary

The reviews found no Critical defect. They agree that the codebase has useful provider seams and a genuinely dual-mode data layer, but it is not yet deployable to the documented Azure target without additive hosting, infrastructure, dependency, provider, and test work. The security gate remains open because of several High and Medium findings. One review also identified a real Anthropic key in an ignored local `.env`; it was not tracked in Git, but should be rotated.

Verification reported across the source reviews included 29 passing pytest tests, a successful frontend build and Python compile pass, Ruff analysis, `npm audit` with no vulnerabilities, `pip-audit` with no known vulnerabilities, full-file inspection, and grep/Git verification of unused-code and secret claims.

## 1. Notes and annotations

### N1 — Commented Azure provider sketch

- **Location:** `src/llm.py:102`
- **Severity:** Low
- **Issue:** A 34-line commented-out `AzureOpenAIProvider` sketch remains in executable source and can drift while looking ready to uncomment.
- **Fix:** Remove it from `llm.py`; retain a short extension note and the design in `docs/design/azure-target.md`.
- **Source:** GPT-5

### N2 — Misleading back-compat alias comment

- **Location:** `src/triage_ai.py:31-32`
- **Severity:** Low
- **Issue:** `FWF_PROFILE` is described as imported by other modules, but no in-repo caller uses it.
- **Fix:** Delete the alias/comment or accurately document its external purpose.
- **Source:** Opus 4.8

### N3 — Unused CPV label API advertised as active

- **Location:** `src/cpv_catalog.py:10-12,88-90`
- **Severity:** Low
- **Issue:** The docstring says `label()` enriches API notices, but it has no caller or reachable entry point.
- **Fix:** Wire it into notice enrichment or remove the claim and function.
- **Source:** Opus 4.8 (two source entries merged)

### N4 — Retry-loop invariant is implicit

- **Location:** `src/contracts_finder_filter.py:37-49`
- **Severity:** Low
- **Issue:** `fetch_polite` relies on the final attempt re-raising; no explicit terminal raise or comment documents that invariant.
- **Fix:** Document the invariant or add an explicit unreachable raise.
- **Source:** Opus 4.8

### N5 — Dynamic SQL safety invariant is undocumented

- **Location:** `src/api.py:168`
- **Severity:** Low
- **Issue:** `distinct(col)` interpolates a column name safely only because every caller supplies an internal literal; that constraint is undocumented.
- **Fix:** Document that `col` must never originate from request input, or constrain it structurally.
- **Source:** Opus 4.8

### N6 — Unreachable future-stage presentation branches

- **Location:** `web/src/journey.js:6-7,74-79`; `web/src/styles.css:141-142`
- **Severity:** Low
- **Issue:** `design` and `gap` state entries and styles are retained for hypothetical future stages, while all current stages are live.
- **Fix:** Retain only if such stages are planned; otherwise remove the entries and CSS.
- **Source:** Opus 4.8

### N7 — Seed-script SQL comment overstates exercised parity

- **Location:** `src/seed_plan_demo.py:66`; equivalent comments in the other three stage seed scripts
- **Severity:** Low
- **Issue:** The cross-dialect comment is technically accurate, but can imply the wired SQL Server path is exercised when it is not tested.
- **Fix:** Clarify that SQL Server is supported through `DB_URL` but not yet provisioned/tested.
- **Source:** Opus 4.8

## 2. Consistency

### C1 — Nonstandard multi-statement lines

- **Location:** `skills/b02-compliance-matrix/scripts/build_matrix.py:62,71,72,82`
- **Severity:** Low
- **Issue:** Multiple statements are joined with semicolons, contrary to repository style and Ruff.
- **Fix:** Split the statements and add an agreed linter to `scripts/check.sh`.
- **Source:** GPT-5

### C2 — Comma-separated standard-library imports

- **Location:** `src/find_tender_filter.py:13`; `src/contracts_finder_filter.py:23`
- **Severity:** Low
- **Issue:** Both connectors group standard-library imports unlike the rest of the backend and Ruff convention.
- **Fix:** Put one imported module per line.
- **Source:** GPT-5

### C3 — Connector retry policies diverge and omit transient failures

- **Location:** `src/find_tender_filter.py:92-95`; `src/contracts_finder_filter.py:37-49`
- **Severity:** Medium
- **Issue:** Find-a-Tender has no retry; Contracts Finder retries only HTTP 429. Neither consistently handles transient network, timeout, or decode failures.
- **Fix:** Share a fetch/backoff helper covering 429 and a bounded set of transient failures, with per-source pacing.
- **Source:** Opus 4.8

### C4 — One board query bypasses row normalisation

- **Location:** `src/db.py:913` versus `:770,817,875`
- **Severity:** Low
- **Issue:** `list_bids_for_board` uses `dict(r)` while sibling queries use `_row_dict(r)`, risking future JSON-column drift.
- **Fix:** Use `_row_dict(r)` consistently.
- **Source:** Opus 4.8

### C5 — Mixed `HTTPException` call styles

- **Location:** `src/api.py` (for example `:336,501,594,940,1079,1587`)
- **Severity:** Low
- **Issue:** Positional and keyword construction styles are mixed.
- **Fix:** Standardise on `status_code=` and `detail=`.
- **Source:** Opus 4.8

### C6 — Repeated entity-existence guards

- **Location:** `src/api.py:962,1126,1252,1421,1453,1581`
- **Severity:** Low
- **Issue:** Roughly six mutation endpoints repeat bid/opportunity existence checks and already vary in wording.
- **Fix:** Extract `_require_bid` and `_require_opp` helpers.
- **Source:** Opus 4.8

### C7 — Same connector variable holds different types

- **Location:** `src/find_tender_filter.py:166-167`; `src/contracts_finder_filter.py:127-128`
- **Severity:** Low
- **Issue:** `end` is a string in one connector and a dictionary in the other for the same open-notice test.
- **Fix:** Normalise both to an end-date string before calling `is_open`.
- **Source:** Opus 4.8

### C8 — Copied urgency threshold can drift

- **Location:** `src/clarification.py:43-44`; `src/bidplan.py:60`
- **Severity:** Low
- **Issue:** `IMMINENT_DAYS = 7` is copied instead of imported, despite being a shared Plan/Manage invariant.
- **Fix:** Import `IMMINENT_DAYS` from `bidplan`.
- **Source:** Opus 4.8

### C9 — AI prompt configurability is asymmetric

- **Location:** `src/complete_ai.py:39-77`; `src/triage_ai.py:99-141`
- **Severity:** Low
- **Issue:** Triage supports settings-overridden prompt templates while Complete hardcodes its prompt without explaining the difference.
- **Fix:** Add the equivalent seam or document why Complete is intentionally fixed.
- **Source:** Opus 4.8

### C10 — Duplicate frontend date formatter

- **Location:** `web/src/stages/SearchStage.jsx:25-33`; `web/src/stages/TriageStage.jsx:43-49`
- **Severity:** Low
- **Issue:** Identical `fmtDate` implementations live in two screens despite an existing shared formatter module.
- **Fix:** Move `fmtDate` to `format.js`.
- **Source:** Opus 4.8

## 3. Cleanliness

### CL1 — Non-atomic, unmanaged skill persistence

- **Location:** `skills/b06-clarification-management/scripts/clarification_log.py:28`
- **Severity:** Medium
- **Issue:** Reads/writes use unclosed `open()` calls and overwrite the live register non-atomically; similar patterns exist in other skill helpers.
- **Fix:** Use context managers and temporary-file plus `os.replace` writes across JSON-producing helpers.
- **Source:** GPT-5

### CL2 — Library code prints request diagnostics

- **Location:** `src/contracts_finder_filter.py:45`
- **Severity:** Low
- **Issue:** Rate-limit diagnostics go directly to stdout even when invoked through `/api/search`.
- **Fix:** Use a module logger; reserve `print` for CLI output.
- **Source:** GPT-5

### CL3 — Unknown outcomes silently create API buckets

- **Location:** `src/outcome.py:191`
- **Severity:** Low
- **Issue:** An unknown stored result adds a new key to the pre-seeded counts and leaks into `by_result`.
- **Fix:** Guard against unknown results or normalise them to `Awaiting`.
- **Source:** Opus 4.8

### CL4 — Redundant buried opportunity query

- **Location:** `src/api.py:985-989`
- **Severity:** Low
- **Issue:** `save_qualification` embeds a redundant `SELECT *` inside a fallback expression after existence was already checked.
- **Fix:** Query only `title` into a named local, or reuse the earlier row.
- **Source:** Opus 4.8

## 4. Unused code

### U1 — Unused runtime import

- **Location:** `src/api.py:21`
- **Severity:** Low
- **Issue:** `datetime` is imported but never used.
- **Fix:** Remove the import.
- **Source:** Both reviews (merged)

### U2 — CLI stage option has no effect

- **Location:** `skills/b05-submission-preflight/scripts/preflight.py:51,118`
- **Severity:** Medium
- **Issue:** `run(cfg, stage)` never reads `stage`, so `readiness` and `final` modes run the same gate.
- **Fix:** Implement stage-specific checks or remove the parameter and option.
- **Source:** GPT-5

### U3 — Ignored helper return contract

- **Location:** `skills/b02-compliance-matrix/scripts/build_matrix.py:74,94`
- **Severity:** Low
- **Issue:** `keys` exists only to be returned, but the sole caller ignores the result.
- **Fix:** Remove it and the return value unless a real consumer needs them.
- **Source:** GPT-5

### U4 — Dead response-field constant duplicates live schemas

- **Location:** `src/response.py:29-34`
- **Severity:** Medium
- **Issue:** `RESPONSE_FIELDS` is unused while equivalent field lists exist in `db.py` and `default_response_item()`.
- **Fix:** Make it the single source for response construction/reference data, or delete it.
- **Source:** Opus 4.8

### U5 — Unused default CPV-prefix argument

- **Location:** `src/find_tender_filter.py:47-49`
- **Severity:** Low
- **Issue:** Every real caller passes `prefixes`, so the module-level default is never exercised.
- **Fix:** Make the argument required or explicitly document the default as an interactive convenience.
- **Source:** Opus 4.8

## 5. Orphaned code

### O1 — Incompatible standalone clarification model

- **Location:** `skills/b06-clarification-management/scripts/clarification_log.py:25`; `src/clarification.py:36`
- **Severity:** Medium
- **Issue:** The unreferenced skill helper defines a second incompatible clarification status vocabulary.
- **Fix:** Integrate it with the canonical domain module/vocabulary or retire it.
- **Source:** GPT-5

### O2 — Unused Azurite service implies false parity

- **Location:** `docker-compose.yml:41`
- **Severity:** Low
- **Issue:** Azurite exposes all storage endpoints, but no runtime code consumes Azure Storage.
- **Fix:** Put it in an opt-in Compose profile until a storage-backed path exists and document its current status.
- **Source:** GPT-5

### O3 — Dead CSS selectors

- **Location:** `web/src/styles.css:231-236,243,246-247`
- **Severity:** Low
- **Issue:** `.reg*`, `.ck .cnote`, and `.outcome-head*` selectors have no matching JSX.
- **Fix:** Delete those blocks.
- **Source:** Opus 4.8

### O4 — Manual seed scripts lack a supported entry point

- **Location:** `src/seed_complete_demo.py`, `seed_learn_demo.py`, `seed_manage_demo.py`, `seed_plan_demo.py`
- **Severity:** Low
- **Issue:** The scripts are deliberate dev tools but have no Make/CI entry point, no smoke coverage, and an undocumented run-order dependency on Plan.
- **Fix:** Add a `make seed-demo` chain and/or smoke coverage.
- **Source:** Opus 4.8

## 6. Right-sized, not bloated

### R1 — Monolithic API module

- **Location:** `src/api.py:164` onward
- **Severity:** Medium
- **Issue:** A roughly 1,613-line module owns app construction, models, validation, search orchestration, response assembly, and all six stages' routes.
- **Fix:** Split stage, settings, and search routers while keeping cross-cutting construction in `api.py`.
- **Source:** GPT-5

### R2 — Stale-term substring matching creates false positives

- **Location:** `skills/b04-response-drafter/scripts/check_answer.py:86`
- **Severity:** Low
- **Issue:** All stale terms use substring matching, so short entries can match inside unrelated words.
- **Fix:** Default to whole-word matching with explicit substring exceptions.
- **Source:** GPT-5

### R3 — Connector orchestration is duplicated

- **Location:** `src/find_tender_filter.py:108-193`; `src/contracts_finder_filter.py:72-154`
- **Severity:** Medium
- **Issue:** `to_record` and `run` duplicate pagination, dedupe, filtering, persistence, and commit logic despite only a few source-specific differences.
- **Fix:** Extract shared OCDS orchestration/persistence parameterised by the window parameter, pacing/fetcher, mapper, dates, and URL builder.
- **Source:** Opus 4.8 (Cleanliness and Right-sizing entries merged)

### R4 — Repeated row-to-dictionary comprehension

- **Location:** `src/api.py:144,1080,1200,1379,1540`
- **Severity:** Low
- **Issue:** Five sites manually build `{k: row[k] for k in row.keys()}` although the row adapter is a mapping.
- **Fix:** Use `dict(row)`.
- **Source:** Opus 4.8

### R5 — Similar numeric parsers do not yet justify abstraction

- **Location:** `src/outcome.py:86-99`; `src/response.py:69-74`
- **Severity:** Low
- **Issue:** Three tolerant string-to-number helpers are similar but have distinct semantics.
- **Fix:** Take no action now; consolidate only if another use appears.
- **Source:** Opus 4.8

### R6 — Repeated board-loading scaffold

- **Location:** `web/src/stages/{Plan,Manage,Complete,Learn}Stage.jsx`
- **Severity:** Low
- **Issue:** Four stages repeat loading/error/reload state scaffolding.
- **Fix:** Leave inline for now; introduce `useBoard` only if further board-style stages make the abstraction worthwhile.
- **Source:** Opus 4.8

## 7. Local / Azure parity and migration readiness

### A1 — Azure Functions host artifacts do not exist

- **Location:** `docs/design/azure-target.md:168`
- **Severity:** High
- **Issue:** The selected target needs an `AsgiFunctionApp` wrapper and Functions metadata, but the adapter, `host.json`, local settings template, and timer trigger are absent.
- **Fix:** Add and locally verify those artifacts before describing the build as promotion-ready.
- **Source:** GPT-5

### A2 — Infrastructure and deployment automation do not exist

- **Location:** `docs/design/azure-target.md:146`
- **Severity:** High
- **Issue:** Required Bicep, parameters, identity grants, and OIDC frontend/backend workflows are absent.
- **Fix:** Implement them and validate a resource-group-scoped what-if deployment.
- **Source:** GPT-5

### A3 — Documented SharePoint provider is unimplemented

- **Location:** `src/library.py:428`
- **Severity:** High
- **Issue:** `LIBRARY_PROVIDER=graph_sharepoint` raises `RuntimeError`; the local mirror cannot simply move to ephemeral cloud storage.
- **Fix:** Implement and contract-test `GraphSharePointProvider` with managed identity and `Sites.Selected`.
- **Source:** GPT-5

### A4 — Azure SQL production dependency is omitted

- **Location:** `requirements.txt:10`
- **Severity:** High
- **Issue:** The Azure SQL path needs `pyodbc`, but it is commented out with a manual install note.
- **Fix:** Add a deployment manifest/extra with `pyodbc>=5.1` and ensure ODBC Driver 18 exists in the host image.
- **Source:** GPT-5

### A5 — Local and target SQL versions differ

- **Location:** `docker-compose.yml:16`; `docs/design/azure-target.md:188-198`
- **Severity:** Medium
- **Issue:** Compose pins SQL Server 2022 while the design targets SQL Server 2025 native vector capability.
- **Fix:** Test the intended version or state explicitly that local 2022 parity covers only the current relational path and vectors are deferred.
- **Source:** GPT-5

### A6 — Dev runner is loopback/reload-only

- **Location:** `src/api.py:1613`
- **Severity:** Low
- **Issue:** The direct runner hardcodes `127.0.0.1:8000` with reload, which is unsuitable if reused in a container.
- **Fix:** Read host/port/reload from environment or label the block explicitly as local-only.
- **Source:** Opus 4.8

### A7 — Connector endpoints and tuning are not configurable

- **Location:** connector API URLs, UA, timeout, pacing, and retry constants
- **Severity:** Low
- **Issue:** Fixed literals hinder stub testing and tuning behind an Azure proxy; the UA also identifies as a generic browser.
- **Fix:** Support environment overrides with current defaults and use a truthful application UA.
- **Source:** Opus 4.8

### A8 — Azure-specific DB and auth paths are untested

- **Location:** `tests/test_app_construct.py:11`; `tests/test_auth_roles.py:5-6`
- **Severity:** Low–Medium
- **Issue:** Tests cover SQLite and local auth bypass, but not the `mssql+pyodbc` dialect or real JWKS/signature verification.
- **Fix:** Add skip-gated SQL Server integration coverage and local RSA accept/reject auth tests.
- **Source:** Opus 4.8

### A9 — Azure design gap table is stale

- **Location:** `docs/design/azure-target.md` gap table around line 137
- **Severity:** Documentation gap
- **Issue:** It still describes the database as hardcoded SQLite and the largest unfinished piece, although `db.py` is now dual-mode SQLAlchemy Core.
- **Fix:** Update the row to show Phase B is substantially implemented and identify the remaining provisioning/testing gaps.
- **Source:** Opus 4.8

## 8. Security (final gate)

### S1 — Spreadsheet formula injection in CSV export

- **Location:** `src/api.py:301`
- **Severity:** High
- **Issue:** Upstream-controlled cell values beginning with `=`, `+`, `-`, or `@` are exported without neutralisation.
- **Fix:** Apply a documented CSV-safe encoding policy and test all four prefixes.
- **Source:** GPT-5

### S2 — Search workload and input are insufficiently bounded

- **Location:** `src/api.py:314`
- **Severity:** Medium
- **Issue:** `days`, CPV-list size, and dates are unbounded/unvalidated, and any authenticated User can initiate synchronous external searches without throttling.
- **Fix:** Add Pydantic bounds/date validation, cap ranges/lists, and rate-limit, queue, or more tightly authorise live refreshes.
- **Source:** GPT-5

### S3 — Raw connector exceptions leak to clients

- **Location:** `src/api.py:358-362`
- **Severity:** Medium
- **Issue:** Per-source failures return exception types and messages verbatim, potentially exposing URLs, paths, request data, or future connector configuration.
- **Fix:** Log full context server-side and return a stable generic client message.
- **Source:** Both reviews (merged)

### S4 — Browser logs raw authentication errors

- **Location:** `web/src/api.js:29`; `web/src/main.jsx:47`
- **Severity:** Medium
- **Issue:** Production code logs raw MSAL error objects during silent, redirect, and initialisation failures.
- **Fix:** Log stable codes/messages only in production or gate detailed objects behind `import.meta.env.DEV`.
- **Source:** GPT-5

### S5 — Real local Anthropic credential requires rotation

- **Location:** `src/.env:3`
- **Severity:** High
- **Issue:** A credential-shaped, apparently real Anthropic key exists in the ignored working-tree `.env`. It is not tracked and was not found in Git history, but remains plaintext local secret material.
- **Fix:** Rotate/revoke it, then inject development secrets from a secret manager or an untracked location outside the repository.
- **Source:** Opus 4.8

### S6 — Outbound query parameters are injectable/unencoded

- **Location:** `src/find_tender_filter.py:150-152`; `src/contracts_finder_filter.py:111-113`; `src/api.py:317`
- **Severity:** Medium
- **Issue:** Free-form `stage` and date values are interpolated into upstream URLs without URL encoding; crafted values can alter query parameters or break requests.
- **Fix:** Validate `stage`, normalise dates, and construct queries with `urllib.parse.urlencode`.
- **Source:** Opus 4.8

### S7 — Public notice text is prompt-injection capable

- **Location:** `src/triage_ai.py:152-174,219-220`
- **Severity:** Medium
- **Issue:** Untrusted notice text is inserted into the LLM prompt without a strong data boundary or instruction to ignore embedded commands.
- **Fix:** Delimit notice data explicitly, state that its content is not instruction, and retain human approval.
- **Source:** Opus 4.8

### S8 — AI-extracted deadlines are not marked provisional

- **Location:** `src/triage_ai.py:208-210`
- **Severity:** Low
- **Issue:** Hallucinated fallback deadlines can enter a draft without provenance, although structured dates take precedence and a human reviews the result.
- **Fix:** Mark AI-sourced dates as provisional in metadata/UI.
- **Source:** Opus 4.8

### S9 — Model-reported evidence is not cross-checked

- **Location:** `src/complete_ai.py:54-58,108-111`
- **Severity:** Low
- **Issue:** `evidence_used` is shown without verifying it is a subset of `matches_offered`.
- **Fix:** Intersect the lists or visibly flag unsupported entries.
- **Source:** Opus 4.8

### S10 — Non-JSON upstream success bodies abort a run

- **Location:** `src/find_tender_filter.py:157`; corresponding Contracts Finder `json.load`
- **Severity:** Low
- **Issue:** An HTML/non-JSON body returned with HTTP 200 raises an unhandled decode error rather than a clean source-scoped failure.
- **Fix:** Catch decode failures and report them through the shared connector error path.
- **Source:** Opus 4.8

## 9. Test coverage

### T1 — Outcome calculations lack unit tests

- **Location:** `src/outcome.py:102,174`
- **Severity:** Medium
- **Issue:** Competitive win-rate and score-percentage invariants are untested while sibling domain modules have tests.
- **Fix:** Add tests for competitive denominators, empty values, and rounding.
- **Source:** Opus 4.8

### T2 — Response word-count compliance gate lacks tests

- **Location:** `src/response.py:61,77`
- **Severity:** Medium
- **Issue:** Word counting and over-limit blocking are untested despite being described as a hard compliance gate.
- **Fix:** Test empty/`None`, whitespace variants, and exact under/over-limit boundaries.
- **Source:** Opus 4.8

## Consolidated disposition

- **Critical:** 0
- **High:** 6
- **Medium:** 15
- **Low–Medium:** 1
- **Low:** 35
- **Documentation gap:** 1
- **Total unique findings:** 58

The build should not yet receive a clean security or Azure-promotion verdict. The immediate priorities are secret rotation, CSV neutralisation, search input/workload controls, safe error handling, validated/encoded connector queries, prompt-injection hardening, and the missing Azure host/IaC/provider/dependency work.
