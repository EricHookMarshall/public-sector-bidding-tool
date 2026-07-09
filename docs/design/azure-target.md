# Azure + SPA target architecture — Public Sector Bidding Tool

> **Status: design / not yet started.** Captured 2026-07-09 as a forward plan for when the
> tool moves to Azure. Nothing here is provisioned yet. Facts (Azure free-tier terms,
> service names) decay — re-verify before acting (see `knowledge/VERIFIED_FACTS.md`).

## Context

The bidding tool is a local PoC (FastAPI + SQLite + Vite/React) that will eventually run in
Azure as a hosted SPA. It was built anticipating this: three swappable seams (LLM `src/llm.py`,
bid library `src/library.py`, sources `src/sources.py`), a whitelisted `.env` loader that reads
straight from `os.environ`, relative `/api` frontend paths, and a commented-out
`AzureOpenAIProvider`. The lift is real but the shape is already right.

The decisive input: **TalentGrow** (a sibling FWF app) is already deployed in the **same Entra
tenant and resource-group family** (`fwf-rg-talentgrow-dev-westeur`). Its Azure blueprint is
proven and in-house, so the target is to **clone TalentGrow's topology**, adapting only where
the backend differs (TalentGrow is Node Functions; ours is Python FastAPI).

Decisions locked in: **Entra ID sign-in (MSAL)**, **mirror TalentGrow's build pattern**,
**cheapest/free DB**, **Managed Identity + federated credential** for SharePoint/Graph.

---

## Target architecture (clone of TalentGrow, adapted for Python)

```
Browser ──► Azure Static Web App (Free)          ← Vite/React SPA (web/), MSAL sign-in
   │            └ VITE_API_BASE_URL, Bearer token
   ▼ (CORS'd, separate origin)
Azure Functions (Flex Consumption, Python)        ← FastAPI wrapped as ASGI app
   ├ HTTP function  → existing /api/* routes (src/api.py)
   ├ Timer function → daily refresh_clean.py
   ├ System-assigned Managed Identity ──► Azure SQL (AAD-only)
   │                                  ──► MS Graph / SharePoint (Sites.Selected)
   │                                  ──► Azure OpenAI (or Anthropic key in App Settings)
   └ Storage account (Blob) ─ deployment pkg + any bid-doc/export files
Provisioned by one resource-group-scoped infra/main.bicep
Deployed by two path-filtered GitHub Actions workflows (SWA token; Functions via OIDC)
```

**Key adaptation vs TalentGrow:** keep the Python FastAPI backend intact and host it on
**Azure Functions Python (Flex Consumption)** via the ASGI integration
(`azure.functions.AsgiFunctionApp(app=fastapi_app)`). This reuses TalentGrow's Bicep, CI, MI,
and SWA topology verbatim while keeping every existing `src/` module. (Alternative: App Service
Linux Python — simpler for long-running sync connectors, but diverges from the pattern.
Functions-Flex is recommended for parity.)

---

## Answers to the framing questions

### Do we need Azurite?
**Only for Blob — and yes, indirectly.** Azurite emulates Blob/Queue/Table *only*.
- **DB** → not Azurite; emulate locally with a **SQL Server / Azure SQL Edge container** (or keep SQLite for local dev — see dual-mode below).
- **SharePoint/Graph** → no emulator exists; dev against a **real test SharePoint site** in the dev tenant.
- **Entra ID / Key Vault** → no emulator; `az login` + `DefaultAzureCredential` locally.
- **Blob** → TalentGrow uses a Storage account (deployment pkg + file uploads). Flex Consumption
  *requires* a storage account, and if we mirror TalentGrow's file pattern (store generated bid
  docs/exports in Blob), **Azurite is the right local emulator for that** — not needed until we
  actually add Blob file handling.

### App registration(s)
Entra app regs for **auth**; Managed Identity for **runtime resource access**:
1. **API app registration** — exposes scope `api://<id>/access_as_user`; its client id is the
   JWT audience the backend validates (`AAD_API_CLIENT_ID`).
2. **SPA app registration** (or one combined app) — SPA platform + redirect URIs;
   `VITE_AAD_CLIENT_ID` / `VITE_AAD_TENANT_ID` / `VITE_AAD_API_SCOPE` (public, build-time).
3. **SharePoint/Graph** — **no secret-bearing app reg.** The Function App's system-assigned
   **Managed Identity** is granted the Graph **`Sites.Selected`** app role, then granted read on
   FWF's specific bid-library site. Runtime code gets a Graph token via `DefaultAzureCredential`
   — no client secret to store or rotate.
4. **CI/CD** — the "**federated credential**" is the GitHub Actions → Azure OIDC trust
   (`azure/login@v2`), as in TalentGrow's Functions workflow. No publish profile/secret.

### Database (cheap/free)
**Azure SQL Database free offer** — serverless General Purpose, **100k vCore-seconds + 32 GB free per
database per month**, **up to 10 free DBs per subscription**, renewing monthly for the life of the
subscription (auto-pause when the monthly limit is hit). Confirmed 2026-07-09 — genuinely £0 for this
workload (a few thousand opportunities/bids sits nowhere near the limits). It reuses TalentGrow's
*exact* data pattern (Azure SQL, **AAD-only auth**, MI via `Active Directory Integrated`, the one-time
`CREATE USER ... FROM EXTERNAL PROVIDER` grant), but drops from TalentGrow's paid S0 to the free
serverless tier. No cheaper managed relational option fits — Cosmos/Table are NoSQL and break the
board joins; Postgres free is only a 12-month trial. *(Verify current free-offer terms before relying.)*

### Documents & AI retrieval (SharePoint, no Blob) — decided 2026-07-09
**Bid docs stay in SharePoint; no Azure Blob doc store.** The structure already exists in SP, it's
security-trimmed, and it's already paid for under M365. Users get a SharePoint/Graph link rather than
files streamed through storage. **Asterisk:** Functions Flex Consumption still requires a small storage
account for its *deployment package* — unavoidable, pennies, and not a document store, so "no Blob for
docs" holds.

**AI retrieval without paying for a vector store.** All three options below plug into the existing
`library.py` retrieval seam that feeds `complete_ai.py`, so ship the cheapest first and swap up later
with no app rewrite. Do the **text-cache regardless** — extract past-response text at ingest into an
Azure SQL table; it decouples retrieval from live SP and avoids re-downloading/re-parsing (and Graph
throttling) on every query. It's the substrate for all three.

- **A — M365 Copilot Retrieval API (preferred; spike first).** `POST https://graph.microsoft.com/v1.0/copilot/retrieval`
  returns grounded text chunks from SharePoint via *Copilot's own hybrid index* — no embeddings to
  build, no re-indexing, no Blob, security-trimmed, scopeable to the bid-library site with a
  `SiteID`/`Path` KQL filter. The tenant already has a Copilot agent on that library, so the index
  exists. Cost = existing M365 Copilot licences (nothing new in Azure). May make embeddings moot.
  Prefer this Graph API over scripting the Copilot Studio *agent* (the API is the clean RAG primitive).
  *(GA/recent-GA as of 2025 — verify current status + licence requirement.)*
- **B — Native vectors in the free Azure SQL DB (self-contained fallback).** Azure SQL's `VECTOR` type
  + `VECTOR_DISTANCE` went **GA June 2025**; `AI_GENERATE_EMBEDDINGS` calls an Azure OpenAI embedding
  endpoint from T-SQL. Real semantic search with **zero extra data infra** — vectors live in the same
  free DB, no Azure AI Search (~£60+/mo, avoided), no Blob. Only cost is embedding generation (pennies).
  Use if Copilot API access is restricted or retrieval must stay fully under our control.
- **C — Cached text + SQL Full-Text Search (£0 baseline).** Lexical only, no Azure OpenAI dependency,
  but free and already better than today's naive keyword match in `library.py`. Ship this first.

**Recommendation:** ship **C** as the baseline in Phase E, **spike A** in parallel (index already
exists, no embedding infra), hold **B** as the self-contained fallback. Net additional Azure cost over
the free DB: £0 (C), pennies (B), nothing-new (A).

**The main lift** is porting `src/db.py` off raw `sqlite3`. pyodbc uses the same `?` placeholder
style. Recommended vehicle: **SQLAlchemy Core** as a thin dialect shim so **local dev keeps
SQLite and cloud uses Azure SQL** (dual-mode, matching TalentGrow's local-container-vs-cloud
split). Work concentrated in: hardcoded `DB_PATH` (`src/db.py:31` → env connection string),
`init_db` `executescript`, SQLite `UPSERT` (`upsert_opportunity` etc. → T-SQL `MERGE`), and
`PRAGMA table_info` migrations (→ `sys.columns`). All-TEXT schema keeps typing simple.

### Managed Identity + federated cred
System-assigned MI for **all** runtime access (SQL, Graph, Azure OpenAI, Blob) via
`DefaultAzureCredential`; OIDC federated credentials for CI. **No Key Vault** unless a genuine
third-party secret appears (TalentGrow omits it) — if we keep Anthropic instead of Azure OpenAI,
its key is the one secret that would justify Key Vault or an App Setting.

---

## Gap checklist (grounded in the seams)

| Concern | Today | Azure target | Effort |
|---|---|---|---|
| **DB** | SQLite+WAL, `DB_PATH` hardcoded `src/db.py:31` | Azure SQL free; SQLAlchemy Core dual-mode | **High** (biggest piece) |
| **Auth** | none anywhere (`src/api.py`, no `Depends` guard) | MSAL in SPA + PyJWT/JWKS `Depends` guard; group-claim→role like TalentGrow's `groupRoleMap` | Medium |
| **Backend host** | uvicorn local | Functions Python Flex, FastAPI via `AsgiFunctionApp` | Medium |
| **Frontend host** | Vite dev proxy | Static Web App (Free); add `@azure/msal-browser`+`msal-react`, `VITE_API_BASE_URL`, Bearer on `fetch` (`web/src/api.js`) | Medium |
| **CORS** | hardcoded localhost `src/api.py:67` | env-driven allowed origins (SWA hostname) | Trivial |
| **Secrets/config** | `.env`→`os.environ` | App Settings inject as env vars — loaders already read `os.environ`, near-zero change | Low |
| **LLM** | Anthropic live; Azure OpenAI commented `src/llm.py:100` | uncomment `AzureOpenAIProvider`, `LLM_PROVIDER=azure_openai`, MI token auth — or keep Anthropic key in App Settings | Low |
| **SharePoint** | `LocalMirrorProvider` `src/library.py:263` | implement `GraphSharePointProvider.items()` at `src/library.py:393` via Graph + MI; `LIBRARY_PROVIDER=graph_sharepoint` | Medium |
| **Connectors/refresh** | synchronous in-request `src/api.py:289`; manual `refresh_clean.py` | Timer-triggered Function for daily refresh; keep on-demand search inline (or Queue+Azurite later) | Medium |
| **IaC + CI/CD** | none | clone TalentGrow `infra/main.bicep` + 2 GitHub Actions workflows | Medium |
| **Ops** | none | App Insights, budget alert (both in TalentGrow's Bicep) | Low |

---

## Phased path

- **Phase A — Design doc.** *(this doc)* Expand with a component diagram + go-live runbook
  cross-referenced to TalentGrow's `docs/guides/azure-build-guide.md`.
- **Phase B — DB portability.** SQLAlchemy Core dual-mode (SQLite local / Azure SQL cloud);
  `DB_PATH` → env connection string; port upserts + migrations. Verify the full journey locally.
- **Phase C — Auth.** MSAL in the SPA; PyJWT/JWKS FastAPI dependency validating audience/issuer +
  group-claim→role; `LOCAL_AUTH_BYPASS` for local dev (TalentGrow pattern).
- **Phase D — Hosting scaffold.** `AsgiFunctionApp` wrapper + `host.json`; clone `infra/main.bicep`
  (SWA + Functions Flex + Azure SQL free + Storage + MI + role assignments) and the two CI
  workflows; env-drive CORS.
- **Phase E — Azure-native providers.** `GraphSharePointProvider` (MI + Sites.Selected); switch
  LLM to Azure OpenAI (or keep Anthropic key); Timer-triggered refresh Function.
- **Phase F — Provision & go-live.** `az deployment group create`; one-time SQL MI grant; Graph
  Sites.Selected consent + site grant; smoke-test the deployed journey.

Phases B and C are the substantive code work and are **independent of Azure being provisioned** —
they can land and be verified locally first. D–F need an Azure subscription + tenant admin.

---

## Local emulation / dev parity (added 2026-07-09)

Two tiers. **Emulate Tier 1** (real local parity, de-risks B/D before any Azure spend); **use the
seams for Tier 2** (no emulator exists — faking Graph/Entra would violate the CLAUDE.md no-faking
rule; the provider seams *are* the local substitute). This mirrors TalentGrow, whose
`api/local.settings.json` already runs against a **local SQL Server container** + `LOCAL_AUTH_BYPASS`.

**Tier 1 — emulate:**
- **Azure SQL → SQL Server 2025 Linux container** (`mcr.microsoft.com/mssql/server`). Same T-SQL engine
  and it has the native **`VECTOR` type**, so the DB port *and* retrieval Option B both test locally.
  (NB: **Azure SQL Edge retired 30 Sept 2025** — do not use it. On Apple Silicon, enable Docker
  Desktop **Rosetta** for the x64 image.)
- **Azure Functions → Functions Core Tools** (`func start`) — real host for the ASGI-wrapped FastAPI +
  `host.json` + timer-trigger refresh (vs. plain `uvicorn` for pure API dev).
- **Storage backing / async queue → Azurite** — `AzureWebJobsStorage` and any connector queue.
- **Static Web App → SWA CLI** (`swa start`) — optional, only if we use SWA's built-in routing/auth.

Target local stack: `docker compose` of **SQL Server 2025 + Azurite + `func start` + Vite**.

**Tier 2 — no emulator; use the seam / real dev-tenant:**
- **Entra ID / MSAL** — real **dev-tenant app registration** (free, localhost redirects) + a
  `LOCAL_AUTH_BYPASS` shim for offline dev.
- **MS Graph / SharePoint** — the **`LocalMirror` provider over the local export** is the local
  stand-in; real Graph only in cloud, behind the `library.py` seam.
- **Copilot Retrieval API / Azure OpenAI** — keep the provider seam; locally fall back to Full-Text
  (Option C) + the existing Anthropic key; wire real endpoints in cloud.

---

## Files this will touch (when implemented)

- **New:** `infra/main.bicep` (+ `.bicepparam`, README, `grant-managed-identity.sql`),
  `.github/workflows/*` (2), backend `function_app.py` / `host.json`, SPA `authConfig.js` + MSAL wiring.
- **Modified:** `src/db.py` (dialect abstraction), `src/api.py` (auth dependency, env CORS),
  `src/library.py:393` (`GraphSharePointProvider`), `src/llm.py:100` (uncomment Azure OpenAI),
  `web/src/api.js` (base URL + Bearer), `web/package.json` (MSAL deps).
- **Copy-from references (TalentGrow):** `infra/main.bicep`, `infra/grant-function-managed-identity.sql`,
  `.github/workflows/*`, `src/authConfig.ts`, `src/services/apiClient.ts`,
  `api/src/middleware/aadAuth.ts`, `api/src/config/groupRoleMap.ts`, `api/src/services/db.ts`,
  `docs/guides/azure-build-guide.md`.

## Verification

- **Phase B:** run the full 6-stage journey locally on the SQLAlchemy/SQLite path
  (`uvicorn api:app`, `npm run dev`); connectors upsert; boards render — no behavioral change.
  Spin a **SQL Server 2025 container** (not Azure SQL Edge — retired) and run the same suite against it
  to prove dual-mode; the container's `VECTOR` type also lets Option B be tested here.
- **Phase C:** sign in via MSAL locally against the dev-tenant app reg; confirm the Bearer token
  reaches the API and unauthenticated calls 401; role from group claim gates correctly.
- **Phase F:** hit the deployed SWA URL, sign in, exercise Search→Learn end-to-end against Azure
  SQL + Graph SharePoint; confirm the Timer refresh runs and MI (not a secret) is used.
