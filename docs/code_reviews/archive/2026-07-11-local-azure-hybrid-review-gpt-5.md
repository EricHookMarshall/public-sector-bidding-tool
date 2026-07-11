# Local / Azure Hybrid Code Review — GPT-5

Date: 2026-07-11

Scope: all tracked runtime code, helper scripts, manifests, local-emulator configuration, tests, and Azure design material. Historical reviews were read only for context; every finding below was re-verified against the current tree. No source changes were applied.

Verification performed: `python3 -m pytest` (29 passed), `npm --prefix web run build` (passed), `python3 -m compileall -q src skills tests` (passed), Ruff static analysis, `npm audit` (0 vulnerabilities), and `pip-audit` against both Python manifests (0 known vulnerabilities).

## Inventory

- Backend project: flat Python modules under `src/`. Runtime entry point is `src/api.py` (`api:app`); `src/db.py` is the SQLite/Azure SQL data layer. Domain modules are `qualification.py`, `bidplan.py`, `response.py`, `clarification.py`, and `outcome.py`. AI and library provider seams are `llm.py`, `triage_ai.py`, `complete_ai.py`, and `library.py`.
- Connector/maintenance CLIs: `find_tender_filter.py`, `contracts_finder_filter.py`, `refresh_clean.py`, and four `seed_*_demo.py` scripts. `sources.py` is the connector registry.
- Frontend project: React/Vite under `web/`. Entry point is `web/src/main.jsx`; `App.jsx` is the journey shell; six live screens are under `web/src/stages/`; `api.js` and `authConfig.js` are the API/auth seams.
- Standalone skill helpers: seven Python scripts under `skills/b00-*` through `skills/b07-*`, plus their `SKILL.md` and reference files. These are not called by the app entry points.
- Local infrastructure/configuration: `docker-compose.yml` (SQL Server and Azurite), `src/.env.example`, `web/.env.example`, `requirements*.txt`, `web/package*.json`, `Makefile`, `scripts/check.sh`, and `pytest.ini`.
- Tests: seven modules under `tests/`, reached through pytest and `scripts/check.sh`.
- Azure target: `docs/design/azure-target.md`. The Functions host adapter, Functions metadata, infrastructure-as-code, deployment workflows, and Graph provider described there do not yet exist.

## 1. Notes and annotations

**Location:** `src/llm.py:102`

**Category:** Notes and annotations

**Severity:** Low

**Issue:** A 34-line commented-out `AzureOpenAIProvider` implementation sketch remains in executable source rather than in design documentation or a tracked implementation task.

**Why it matters:** The block can drift from the current OpenAI SDK and Azure authentication design while appearing to be an implementation ready to uncomment.

**Suggested fix:** Remove the commented implementation from `llm.py`; retain only a short provider-extension note and keep the intended design in `docs/design/azure-target.md`.

No outstanding `TODO`, `FIXME`, `HACK`, or `XXX` markers, stale stage-status comments, or decaying hard-coded demo dates were found in runtime code.

## 2. Consistency

**Location:** `skills/b02-compliance-matrix/scripts/build_matrix.py:62`

**Category:** Consistency

**Severity:** Low

**Issue:** This helper repeatedly puts multiple statements on one line with semicolons, contrary to the style used throughout `src/` and flagged by Ruff at lines 62, 71, 72, and 82.

**Why it matters:** The repository has no enforced formatter/linter gate, and this module already deviates from the dominant Python style.

**Suggested fix:** Split each statement onto its own line and add Ruff (or an equivalent agreed linter) to `scripts/check.sh` so local deviations are caught consistently.

**Location:** `src/find_tender_filter.py:13`

**Category:** Consistency

**Severity:** Low

**Issue:** Both connector modules use comma-separated standard-library imports (`contracts_finder_filter.py:23` has the same pattern), unlike the rest of the backend and Ruff's configured/default convention.

**Why it matters:** Parallel connector modules should follow the same import and formatting pattern as the project they plug into.

**Suggested fix:** Put one imported module per line in both connector files.

## 3. Cleanliness

**Location:** `skills/b06-clarification-management/scripts/clarification_log.py:28`

**Category:** Cleanliness

**Severity:** Medium

**Issue:** The clarification register is loaded and overwritten through unclosed `open()` calls, and `_save` writes the live file directly rather than atomically. The same unmanaged-open pattern occurs in several other skill helpers.

**Why it matters:** An exception or interruption during a write can truncate the only clarification register, directly recreating the missed-clarification failure mode the tool is intended to prevent.

**Suggested fix:** Use context managers for reads and an atomic temporary-file-plus-`os.replace` write in `_save`; apply the same persistence pattern to the other JSON-producing helpers.

**Location:** `src/contracts_finder_filter.py:45`

**Category:** Cleanliness

**Severity:** Low

**Issue:** Connector library code prints rate-limit diagnostics directly to stdout even when invoked inside `/api/search`.

**Why it matters:** The message is not structured with request/source context and cannot be controlled through the application's logging configuration in Azure.

**Suggested fix:** Use a module logger in connector functions and reserve `print` for CLI `main()` output.

## 4. Unused code

**Location:** `src/api.py:21`

**Category:** Unused code

**Severity:** Low

**Issue:** `datetime` is imported but never used; Ruff reports it as `F401`.

**Why it matters:** It is dead runtime-module surface and makes dependency/use inspection noisier.

**Suggested fix:** Remove the import.

**Location:** `skills/b05-submission-preflight/scripts/preflight.py:51`

**Category:** Unused code

**Severity:** Medium

**Issue:** `run(cfg, stage)` never reads `stage`, although the CLI exposes distinct `readiness` and `final` modes at line 118.

**Why it matters:** Users receive the same gate while being told they selected different review stages, so the stated two-stage control is not implemented.

**Suggested fix:** Implement the intended stage-specific checks, or remove the parameter and CLI option.

**Location:** `skills/b02-compliance-matrix/scripts/build_matrix.py:74`

**Category:** Unused code

**Severity:** Low

**Issue:** `keys` is constructed only to be returned at line 94, but the sole caller ignores the return value.

**Why it matters:** This advertises a contract the script does not use.

**Suggested fix:** Remove `keys` and the return value unless a real caller needs them.

## 5. Orphaned code

**Location:** `skills/b06-clarification-management/scripts/clarification_log.py:25`

**Category:** Orphaned code

**Severity:** Medium

**Issue:** The standalone clarification helper is not referenced by any app entry point and defines a second, incompatible status vocabulary (`open/drafting/with_reviewer/sent/closed`) alongside the canonical app implementation in `src/clarification.py:36`.

**Why it matters:** Data created by the skill cannot be wired into the live Manage stage without translation, so promotion/future integration is not merely configuration.

**Suggested fix:** Either wire the helper to the canonical domain module and shared vocabulary, or explicitly retire it; do not maintain two clarification models.

**Location:** `docker-compose.yml:41`

**Category:** Orphaned code

**Severity:** Low

**Issue:** Azurite is provisioned and publishes Blob/Queue/Table ports, but no runtime module or manifest contains an Azure Storage client or an `AzureWebJobsStorage` consumer.

**Why it matters:** `docker compose up` starts and persists an emulator that exercises no application path, giving a misleading impression of Storage parity.

**Suggested fix:** Move Azurite to an opt-in Compose profile until the Functions host or Storage-backed feature exists, and state that it is currently unused.

## 6. Right-sized, not bloated

**Location:** `src/api.py:164`

**Category:** Right-sized, not bloated

**Severity:** Medium

**Issue:** One 1,613-line module owns all HTTP routes, request models, response assembly, settings validation, search orchestration, and six stages' handlers.

**Why it matters:** Unrelated changes share one high-conflict file, and security/role/input policies are difficult to audit consistently across roughly 30 routes.

**Suggested fix:** Split routes by journey stage plus settings/search routers while retaining the existing domain and DB modules; keep app construction and cross-cutting dependencies in `api.py`.

**Location:** `skills/b04-response-drafter/scripts/check_answer.py:86`

**Category:** Right-sized, not bloated

**Severity:** Low

**Issue:** Stale terms are deliberately searched as substrings (`whole_word=False`), so short entries can match inside unrelated words.

**Why it matters:** False positives make a simple checker create avoidable manual review work and can fail otherwise clean drafts.

**Suggested fix:** Use whole-word matching for stale terms, with explicit exceptions only for terms that genuinely require substring matching.

## 7. Local / Azure parity and migration readiness

**Location:** `docs/design/azure-target.md:168`

**Category:** Local / Azure parity and migration readiness

**Severity:** High

**Issue:** The selected Azure Functions target requires an `AsgiFunctionApp` wrapper and `host.json`, but the document still lists that work as a future Phase D and neither artifact exists in the inventory.

**Why it matters:** The current FastAPI/uvicorn entry point cannot be hosted by Azure Functions Core Tools or deployed to the selected Functions Flex target through configuration alone.

**Suggested fix:** Add and locally verify the Functions ASGI adapter, `host.json`, local Functions settings template, and timer trigger before calling the build promotion-ready.

**Location:** `docs/design/azure-target.md:146`

**Category:** Local / Azure parity and migration readiness

**Severity:** High

**Issue:** The target requires resource-group Bicep and two deployment workflows, while the design records IaC and CI/CD as absent.

**Why it matters:** Resource creation, managed identity, role grants, app settings, CORS origins, and deployments are currently manual/undefined; moving to a Resource Group is not a configuration switch.

**Suggested fix:** Add the documented resource-group-scoped Bicep, parameter files, managed-identity SQL grant, and OIDC-based frontend/backend workflows, then validate a what-if deployment.

**Location:** `src/library.py:428`

**Category:** Local / Azure parity and migration readiness

**Severity:** High

**Issue:** Selecting the documented Azure library target with `LIBRARY_PROVIDER=graph_sharepoint` raises `RuntimeError` because no Graph provider exists.

**Why it matters:** The local confidential-library mirror cannot exist on an ephemeral cloud host; using the real SharePoint library requires application code, SDK/auth wiring, and tests rather than configuration.

**Suggested fix:** Implement `GraphSharePointProvider` behind `LibraryProvider`, authenticate with managed identity and `Sites.Selected`, and contract-test it against the same item shape as `LocalMirrorProvider`.

**Location:** `requirements.txt:10`

**Category:** Local / Azure parity and migration readiness

**Severity:** High

**Issue:** The Azure SQL code path requires `pyodbc`, but the production manifest comments the dependency out and provides only a manual `pip install` instruction.

**Why it matters:** A clean Azure deployment built from `requirements.txt` cannot import the SQL Server driver selected by `DB_URL`; promotion requires editing the build/install process.

**Suggested fix:** Add an Azure deployment requirements file or supported dependency extra containing `pyodbc>=5.1`, and provision Microsoft ODBC Driver 18 in the hosting image.

**Location:** `docker-compose.yml:16`

**Category:** Local / Azure parity and migration readiness

**Severity:** Medium

**Issue:** Local parity pins SQL Server 2022, while `docs/design/azure-target.md:188-198` says the target stack is SQL Server 2025 and relies on its native vector capability.

**Why it matters:** The local stack does not test the documented retrieval option or exact target-engine assumption, so a claimed parity check can pass without exercising planned SQL features.

**Suggested fix:** Reconcile the design and Compose file: either pin and test 2025, or explicitly defer vectors and update the design to state that 2022 covers only the current relational path.

## 8. Security (final gate)

**Location:** `src/api.py:301`

**Category:** Security

**Severity:** High

**Issue:** CSV export writes upstream-controlled fields directly into cells without neutralising values beginning with `=`, `+`, `-`, or `@`.

**Why it matters:** A malicious procurement notice can become a spreadsheet formula; opening the exported file in Excel or another spreadsheet can execute formula actions or exfiltrate data. This blocks a safe verdict.

**Suggested fix:** Before `writer.writerow`, prefix formula-leading text cells with an apostrophe (or use a documented CSV-safe encoding policy) and add tests covering all four formula prefixes.

**Location:** `src/api.py:314`

**Category:** Security

**Severity:** Medium

**Issue:** `SearchRequest` accepts unbounded `days`, CPV-list length, and date strings, and `/api/search` executes synchronous external fetches for every authenticated User with no request throttling.

**Why it matters:** A valid low-privilege account can trigger expensive, long-running upstream scans repeatedly, consuming Functions executions and hitting procurement API rate limits after Azure promotion.

**Suggested fix:** Add Pydantic bounds and ISO-date validation, cap list sizes/date ranges, and rate-limit or queue searches per identity; consider making live refresh an Admin or dedicated-service operation.

**Location:** `src/api.py:358`

**Category:** Security

**Severity:** Low

**Issue:** Raw connector exception type and message are returned to the client.

**Why it matters:** Upstream URLs, library/runtime details, or network errors can be exposed to callers and differ across Azure environments.

**Suggested fix:** Log the full exception server-side with source/request context and return a stable generic source-failure message.

**Location:** `web/src/api.js:29`

**Category:** Security

**Severity:** Low

**Issue:** Production browser code logs raw MSAL error objects on silent and redirect token failures; `web/src/main.jsx:47` does the same during initialisation.

**Why it matters:** Correlation identifiers, tenant/auth diagnostics, and claims-related context are exposed in browser developer tools and create unnecessary production log noise.

**Suggested fix:** Log only a stable error code/message in production, or gate detailed objects behind `import.meta.env.DEV`.

Secret/config checks: no committed API keys, tokens, production connection strings, or credential files were found. Root and web gitignore rules exclude `.env` variants while retaining examples; the examples contain empty placeholders. The Compose password is operator-supplied and all published emulator ports are loopback-bound. `npm audit` and `pip-audit` reported no known dependency vulnerabilities on 2026-07-11.

## Summary

Total findings: **21** — Critical 0, High 5, Medium 6, Low 10.

| Category | Total | Critical | High | Medium | Low |
|---|---:|---:|---:|---:|---:|
| Notes and annotations | 1 | 0 | 0 | 0 | 1 |
| Consistency | 2 | 0 | 0 | 0 | 2 |
| Cleanliness | 2 | 0 | 0 | 1 | 1 |
| Unused code | 3 | 0 | 0 | 1 | 2 |
| Orphaned code | 2 | 0 | 0 | 1 | 1 |
| Right-sized, not bloated | 2 | 0 | 0 | 1 | 1 |
| Local / Azure parity and migration readiness | 5 | 0 | 4 | 1 | 0 |
| Security | 4 | 0 | 1 | 1 | 2 |

## Migration readiness

The move is **not yet configuration-only**. Required code/build work before promotion:

1. Add the Azure Functions ASGI wrapper, Functions metadata, timer trigger, and local Core Tools configuration.
2. Add Bicep/parameters and OIDC deployment workflows for SWA, Functions, Storage, Azure SQL, managed identity, monitoring, roles, and app settings.
3. Implement and test `GraphSharePointProvider`; grant its managed identity least-privilege `Sites.Selected` read access to the specific library site.
4. Package `pyodbc` and ODBC Driver 18 for the Azure deployment.
5. Reconcile SQL Server 2022 local emulation with the documented 2025/vector target and run the full suite against the selected container.
6. Neutralise exported CSV formulas and bound/rate-limit live searches before exposing the Azure deployment.

After those changes, the environment switch is the expected configuration set: `DB_URL`; `LOCAL_AUTH_BYPASS=0`; `AAD_TENANT_ID`, `AAD_API_CLIENT_ID`, and an explicit group/default-role policy; `CORS_ALLOWED_ORIGINS`; `LIBRARY_PROVIDER=graph_sharepoint`; LLM provider credentials/settings; and the SPA's `VITE_AAD_*` plus `VITE_API_BASE_URL`.

## Security verdict

**Fail.** The CSV formula-injection issue at `src/api.py:301-305` is blocking. The unbounded synchronous live-search surface should also be constrained before public Azure use. No committed-secret or known dependency-vulnerability blocker was found.
