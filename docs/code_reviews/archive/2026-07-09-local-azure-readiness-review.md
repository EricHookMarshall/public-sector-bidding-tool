# Code Review: Local/Azure Readiness Audit

Inventory reviewed:
- Backend API entry point: `src/api.py`
- Backend support modules: `src/auth.py`, `src/config.py`, `src/db.py`, `src/llm.py`, `src/library.py`, `src/sources.py`, `src/find_tender_filter.py`, `src/contracts_finder_filter.py`, `src/qualification.py`, `src/bidplan.py`, `src/clarification.py`, `src/response.py`, `src/outcome.py`, `src/triage_ai.py`, `src/complete_ai.py`, `src/regions.py`, `src/cpv_catalog.py`, `src/refresh_clean.py`
- Backend demo/seed entry points: `src/seed_plan_demo.py`, `src/seed_manage_demo.py`, `src/seed_complete_demo.py`, `src/seed_learn_demo.py`
- Frontend entry points: `web/src/main.jsx`, `web/src/App.jsx`
- Frontend support/views: `web/src/api.js`, `web/src/authConfig.js`, `web/src/journey.js`, `web/src/SettingsView.jsx`, `web/src/stages/*.jsx`
- Local/Azure config and manifests: `requirements.txt`, `web/package.json`, `web/vite.config.js`, `docker-compose.yml`, `.gitignore`, `src/.env.example`, `web/.env.example`, `docs/design/azure-target.md`, `_session/todo.md`, `_session/handover.md`

## Findings

Location: src/.env.example:1
Category: Notes and annotations
Severity: Low
Issue: The comment still tells developers to copy the file to `discovery/.env`, but the backend now loads `src/.env`.
Why it matters: A new developer following the example can put local settings in the wrong location and then misdiagnose auth, LLM, or CORS failures during local/Azure parity testing.
Suggested fix: Update the comment to say `src/.env`.

Location: web/src/journey.js:11
Category: Notes and annotations
Severity: Low
Issue: The comment says only Search is real and the rest render placeholders, but the stage registry now maps Triage, Plan, Complete, Manage, and Learn to real stage components.
Why it matters: This stale annotation misleads reviewers and future migration work about which modules are live.
Suggested fix: Update the comment to describe the current all-six-stage mapping, or remove the stale build-status explanation.

Location: web/src/App.jsx:19
Category: Notes and annotations
Severity: Low
Issue: The comment says only Search is live and the rest are preview screens, but `VIEWS` maps all six stages to concrete implementations.
Why it matters: This contradicts the runtime code and can cause developers to overlook live surfaces during Azure/auth review.
Suggested fix: Replace the comment with the current mapping behavior.

Location: src/find_tender_filter.py:13
Category: Consistency
Severity: Low
Issue: This module uses grouped imports (`import json, sys, urllib.request, datetime`) while most backend modules use one import per line.
Why it matters: It is a local style deviation that makes automated cleanup and review diffs noisier.
Suggested fix: Split the grouped imports into separate import lines; do the same in `src/contracts_finder_filter.py:23`.

Location: src/api.py:258
Category: Cleanliness
Severity: Medium
Issue: API handlers open database connections and close them manually after successful work, without a `finally` block or dependency-managed connection scope.
Why it matters: Exceptions between `db.connect()` and `conn.close()` can leak pooled SQLAlchemy connections, which matters much more under Azure Functions concurrency than in the single-user local PoC.
Suggested fix: Introduce a small connection dependency/context manager that initializes and closes the connection reliably, then route handlers use that instead of manual open/close.

Location: src/clarification.py:26
Category: Unused code
Severity: Low
Issue: `datetime` is imported but never used.
Why it matters: This is dead code and was confirmed by `pyflakes`.
Suggested fix: Remove the unused import.

Location: web/src/stages/MockStage.jsx:8
Category: Orphaned code
Severity: Low
Issue: `MockStage` is exported but has no references under `web/src`; the live app now uses the real stage components and the `StagePlaceholder` fallback.
Why it matters: It leaves obsolete preview-screen scaffolding in the codebase and increases the chance stale mock UI is accidentally reused.
Suggested fix: Delete `web/src/stages/MockStage.jsx` or rewire it only if a current route still needs it.

Location: web/src/api.js:87
Category: Right-sized, not bloated
Severity: Low
Issue: Error parsing for non-OK JSON responses is repeated across multiple API helpers even though `sendJSON()` already centralizes the same pattern later in the file.
Why it matters: Repeated request plumbing increases maintenance cost and makes future auth/error changes easier to apply inconsistently.
Suggested fix: Reuse one helper for POST/PUT JSON endpoints and keep endpoint functions as thin path/body wrappers.

Location: src/seed_plan_demo.py:58
Category: Local / Azure parity and migration readiness
Severity: Low
Issue: Demo seeders still use `LIMIT 1`, which is SQLite-compatible but not SQL Server/Azure SQL-compatible. The same pattern appears in `src/seed_complete_demo.py:48`, `src/seed_manage_demo.py:102`, and `src/seed_learn_demo.py:79`.
Why it matters: With `DB_URL` pointed at SQL Server, these local support entry points require code edits before they run, violating the "configuration change, not code change" migration target for developer workflows.
Suggested fix: Move the "first matching row" query behind a helper that emits dialect-compatible SQL, or use SQLAlchemy Core `select(...).limit(1)` for these seed lookups.

Location: src/llm.py:100
Category: Local / Azure parity and migration readiness
Severity: Medium
Issue: Azure OpenAI is a commented skeleton, and `_PROVIDERS` only registers `anthropic`.
Why it matters: Moving LLM calls from local Anthropic settings to Azure OpenAI currently requires code changes, not only configuration.
Suggested fix: Implement and register `AzureOpenAIProvider`, add the `openai` dependency, and select it solely through `LLM_PROVIDER` and Azure app settings.

Location: src/library.py:388
Category: Local / Azure parity and migration readiness
Severity: High
Issue: `LIBRARY_PROVIDER` can select only `local_mirror`; any other value silently falls back to `LocalMirrorProvider`.
Why it matters: The Azure target requires SharePoint/Graph access for the bid library, but promotion currently needs new provider code and a registry change. The silent fallback can also hide a misconfigured Azure deployment by reporting the local mirror path instead of failing clearly.
Suggested fix: Implement and register `GraphSharePointProvider`; make unknown provider values raise a clear configuration error rather than falling back.

Location: web/src/api.js:77
Category: Local / Azure parity and migration readiness
Severity: Medium
Issue: CSV export is exposed as a plain URL for an anchor, while authenticated API calls use `apiFetch()` to attach the Entra Bearer token.
Why it matters: Once `LOCAL_AUTH_BYPASS` is off, the export link cannot send the Authorization header and will return 401 in Azure even though the rest of the API works. The call site is `web/src/stages/SearchStage.jsx:196`.
Suggested fix: Replace the anchor with an authenticated `apiFetch()` download that creates a Blob URL, or issue a short-lived signed export URL from the API.

Location: src/auth.py:85
Category: Security
Severity: High
Issue: `AAD_DEFAULT_ROLE` defaults to `User`, and `resolve_role_from_groups()` grants that role to a valid token when no group mapping matches.
Why it matters: In Azure, unless deployment config explicitly sets `AAD_DEFAULT_ROLE=""` and a complete `AAD_GROUP_ROLE_MAP`, any authenticated caller with a valid token for this app can enter the shared bid workspace as `User`. That is broader than least privilege for client-confidential bid data.
Suggested fix: Make strict group membership the production default, or fail startup when bypass is off and no explicit group-role policy is configured. Keep a separate local/dev override if needed.

Location: src/auth.py:219
Category: Security
Severity: Low
Issue: Token validation failures are returned to callers with the raw exception text.
Why it matters: The details are useful locally but disclose auth-validation internals in production responses.
Suggested fix: Return a generic 401 response to clients and log the detailed exception server-side with sensitive values redacted.

## Categories With No Findings

No additional findings beyond the category assignments above.

## Verification Performed

- `python3 -m pyflakes src web/src` reported only `src/clarification.py:26`.
- `python3 -m py_compile src/*.py` passed.
- `npm run build` passed.
- `npm audit --audit-level=low --json` reported 0 vulnerabilities.
- `python3 -m pip_audit -r requirements.txt` reported no known vulnerabilities.
- Secret scan for common key/token patterns returned no matches.
- `git ls-files` showed no tracked `.env`, secret, credential, local database, or SharePoint export files beyond `src/.env.example`; `.gitignore` ignores `.env`, `.env.*`, SQLite DBs, and the SharePoint folder.

Model: GPT-5 Codex

## Summary

Severity counts:
- Critical: 0
- High: 2
- Medium: 3
- Low: 8

Category counts:
- Notes and annotations: 3
- Consistency: 1
- Cleanliness: 1
- Unused code: 1
- Orphaned code: 1
- Right-sized, not bloated: 1
- Local / Azure parity and migration readiness: 4
- Security: 2

## Migration Readiness

Required changes to move from local emulation to the real Resource Group:
- Configure Azure SQL through `DB_URL`; main app code is dual-mode, but demo seeders still need SQL Server-compatible first-row queries.
- Implement and configure `GraphSharePointProvider` for `LIBRARY_PROVIDER=graph_sharepoint`.
- Implement and configure `AzureOpenAIProvider` if Azure OpenAI is the target LLM provider; otherwise store the Anthropic key in Azure app settings.
- Replace CSV anchor export with an authenticated download path.
- Set production auth config explicitly: `LOCAL_AUTH_BYPASS=0`, `AAD_TENANT_ID`, `AAD_API_CLIENT_ID`, complete `AAD_GROUP_ROLE_MAP`, and strict default-role behavior.
- Provision the still-missing Azure hosting pieces: Function App/ASGI wrapper, `host.json`, Static Web App config, storage required by Functions, IaC, CI/CD, and timer refresh.

## Security Verdict

Blocking concerns before the build is considered safe:
- Tighten production role resolution so a valid token without mapped group membership does not automatically become `User`.
- Replace raw auth exception details in 401 responses with a generic client message and server-side logging.

Secrets and dependency checks passed.
