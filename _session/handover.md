# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-10` (session 11) — **Phase C committed + the code-review Wave 0 (security) and Wave 1
(Azure-promotion) remediation confirmed complete and verified green.** Phase C is now in git as
`0f35c70` ("Azure Phase C: Entra ID auth …"). On verifying Wave 0/1 against the actual code (not the
stale todo checklist), **all 12 items were already implemented in the Phase C tree** — so they shipped
inside `0f35c70` rather than as separate commits. Verified this session: backend imports clean + FastAPI
app constructs; newline-injection **functionally rejected** by a live `upsert_env` call; SPA `npm build`
clean (472 kB / 130 kB gz); DB intact (21 opps). The stale todo.md Wave 0/1 checkboxes are now flipped to
match reality.

`2026-07-09` (session 10) — **Azure migration Phase C (auth) is DONE and verified locally (no Azure spend).**
The "no auth anywhere" gap — the #1 gap — is closed. Every `/api/*` route is now behind a
`Depends(require_auth)` guard; the SPA has an Entra ID / MSAL sign-in gate and attaches a Bearer token on
every call. **`LOCAL_AUTH_BYPASS=1` keeps local dev unauthenticated exactly as before** — no behaviour
change to the feature-complete six-stage journey. **Now committed as `0f35c70` (session 11).**

**Backend (`src/auth.py`, new — clones TalentGrow's `aadAuth`/`devAuth`/`groupRoleMap` in Python):**
`require_auth` validates a real Entra **v2 token** via PyJWT + `PyJWKClient` (JWKS signature + issuer +
audience + expiry), resolves a role from the `groups` claim, returns an `Identity`. Wired app-wide as
`FastAPI(dependencies=[Depends(require_auth)])` in `src/api.py` (can't forget a route); the two
config-write endpoints add `Depends(require_roles("Admin"))`. `LOCAL_AUTH_BYPASS=1` → synthetic **Admin**
identity, no token. CORS is now env-driven (`CORS_ALLOWED_ORIGINS`, localhost fallback). `auth_status()`
surfaced in `/api/meta`.

**Frontend:** `web/src/authConfig.js` (MSAL config, null when unconfigured) + `MsalProvider` in
`main.jsx` + sign-in gate / `UserChip` in `App.jsx`. **All 10 fetch calls route through one new `apiFetch`**
in `web/src/api.js` that attaches the Bearer (`acquireTokenSilent` + redirect fallback) and prefixes
`VITE_API_BASE_URL`. `@azure/msal-browser` + `msal-react` added. When the `VITE_AAD_*` vars are absent
(local dev) it's a plain unauthenticated same-origin fetch.

**Two deliberate divergences from TalentGrow** (FWF's bidding-tool Entra groups don't exist yet, so no
invented group IDs are committed): the group→role map is **env-driven** (`AAD_GROUP_ROLE_MAP` JSON, empty
default) and an authenticated caller with no mapped group gets a configurable `AAD_DEFAULT_ROLE`
("User"; set `""` for strict gating). Roles kept small: **Admin > User**.

## Verified this session (all live, honest)

- **Backend unit rig** (`scratchpad/verify_auth.py`, not committed) — self-minted RSA tokens against a
  local JWKS injected into `auth._jwks_clients`: **15/15 PASS** — bypass→Admin; `LOCAL_AUTH_ROLE=User`→User
  and blocked from an Admin route; bogus role→Admin fallback; no-token→401; valid→default User; mapped
  groups→most-privileged Admin; strict+unmapped→403; expired / wrong-aud / wrong-iss / tampered →401;
  unconfigured→500 (fail-closed); `require_roles` blocks User / allows Admin.
- **HTTP** — bypass ON: `/api/meta` (21 opps, `auth.bypass:true`), `/api/plan/board`, `PUT /api/config`
  all 200. Bypass OFF + Entra configured + no token → **401 on every route**; garbage token → 401.
  **`LOCAL_AUTH_BYPASS=1 LOCAL_AUTH_ROLE=User`** → journey routes 200 but `PUT /api/config` → **403**
  (`Role 'User' is not permitted. Requires one of: Admin`) — role-gating exercised live in the local app.
- **Frontend** — `npm run build` clean (MSAL bundled, 473 kB gz 130 kB); full local stack (bypass API +
  Vite on :5199) serves the SPA and proxies `/api/meta` → 21 opps. Unauthenticated local path unchanged.
- **One real fix**: the bypass shim first inherited the default User role, which would 403 the
  now-Admin-gated Settings locally → changed bypass to always grant Admin (TalentGrow's full-access dev
  posture).

## Active task

**Phase C committed + Wave 0/1 remediation confirmed done — pick the next Azure-migration step (user's
call), roughly in priority order. Remaining code-review debt is Wave 2 (correctness bugs) → Wave 6 in
todo.md; none are Azure-promotion blockers.**

1. **Phase C tail — live MSAL browser sign-in** (Tier-2, needs the user): the code path is built + unit-
   proven, but the actual redirect round-trip is only verifiable against a **real dev-tenant app
   registration**. Supply `VITE_AAD_CLIENT_ID/TENANT_ID/API_SCOPE` (SPA) + `AAD_TENANT_ID`/`AAD_API_CLIENT_ID`
   (API), set `LOCAL_AUTH_BYPASS=0`, sign in, confirm the Bearer reaches the API and role-gating works.
2. **Phase D — hosting scaffold** per `docs/design/azure-target.md`: `AsgiFunctionApp` wrapper +
   `host.json`; clone TalentGrow's `infra/main.bicep` (SWA + Functions Flex + Azure SQL free + Storage +
   MI) + the two CI workflows. Needs an Azure subscription + tenant admin (not purely local).
3. **Finish Phase B tail** — port the 4 `seed_*_demo.py` `LIMIT 1` queries to OFFSET/FETCH (low priority).
4. **User browser walk of Complete + Learn** — still open from session 7; verified server-side only.
5. **Deferred externals** — Azure OpenAI provider; live `GraphSharePoint`; HubSpot.

## Auth config quick-reference (new this session)

- **Local dev (default):** `LOCAL_AUTH_BYPASS=1` in `src/.env` → API unauthenticated (synthetic Admin);
  leave `web/.env` `VITE_AAD_*` unset → SPA has no sign-in gate. Runs exactly like sessions 1–9.
- **Test role-gating live locally:** `LOCAL_AUTH_ROLE=User` alongside bypass → the local app runs as a
  User; Admin-only routes (Settings writes) return 403. Default is Admin (full access).
- **Turn auth on:** set `LOCAL_AUTH_BYPASS=0` + `AAD_TENANT_ID` + `AAD_API_CLIENT_ID` (API fails closed
  with a 500 if bypass is off and these are missing — by design). SPA: set all three `VITE_AAD_*`.
- **Templates:** `src/.env.example` (API: bypass, AAD_*, `AAD_GROUP_ROLE_MAP`, `AAD_DEFAULT_ROLE`,
  `CORS_ALLOWED_ORIGINS`) and `web/.env.example` (SPA: `VITE_AAD_*`, `VITE_API_BASE_URL`). Both git-ignored
  when copied to `.env`.
- **Deps added:** `PyJWT[crypto]` (already installed: 2.12.1 + cryptography 46) in `requirements.txt`;
  `@azure/msal-browser` + `@azure/msal-react` in `web/package.json` (`npm install` done).

## Surfaced / parked threads

- **`seed_*_demo.py` use `LIMIT 1`** — sqlite-only; needs OFFSET/FETCH for SQL Server (Phase B tail, low
  priority — seeders are dev-local).
- **Connection lifecycle** — api.py opens a `db.connect()` per request and mostly doesn't close it (same
  as the old sqlite code). Fine for a local single-user PoC; revisit pooling before real multi-user cloud.
- **`web/src/stages/MockStage.jsx` + `StagePlaceholder.jsx` are dead code** — every stage is real. Safe to delete.
- **AI-draft provenance isn't persisted** — win-themes/evidence shown in UI but not saved with the answer.
- **`question_ref` repeats across lots** in the FOR006 master — matrix rows keyed by index, not qref. Don't reintroduce qref as a key.
- **`GraphSharePoint` provider** — not built (no MS Graph here); slots into `library.get_provider()`. **Azure OpenAI provider** — skeleton in `src/llm.py`, not implemented.
- **Team capacity default (25 days, `src/bidplan.py`)** — placeholder, not a real FWF number.
- **CSV export under auth** — `exportUrl()` returns a plain `/api/export?…` URL used by an `<a>` link; an
  anchor can't carry a Bearer header, so under real auth (bypass off) the download would 401. Fine locally
  (bypass) and unauthenticated. Fix when Phase C goes live: fetch+blob download, or a short-lived signed
  link. Low priority; parked.
- **`api._load_dotenv` reads `src/.env`** — the new `AAD_*` / `LOCAL_AUTH_BYPASS` / `LOCAL_AUTH_ROLE` /
  `CORS_*` vars load the same way as the LLM keys (whitelist-free `setdefault`, existing env wins). In
  Azure these come from App Settings → `os.environ`, so no `.env` needed there.
- **Role-aware SPA UI** ✅ **built** — new `GET /api/auth/me` returns the caller's `{role, display_name,
  email, via}`; `App.jsx` fetches it and hides the ⚙ Settings gear for non-Admins + bounces a non-Admin
  who deep-links `#settings` to the journey. Presentation only — the backend `require_roles("Admin")` gate
  still enforces server-side. Verified: `/api/auth/me` → Admin under default bypass, User under
  `LOCAL_AUTH_ROLE=User`; `npm run build` clean.

## Open decisions

1. **What next** — Phase C tail (live sign-in test, needs a dev-tenant app reg), Phase D (hosting scaffold,
   needs Azure), Phase B seeder tail, browser-review Complete/Learn, or polish. Not decided.
2. **AI-draft provenance persistence** — save the evidence/win-themes with the answer?
3. **Azure OpenAI / GraphSharePoint timing** — build when the respective access is provisioned (Azure migration Phase E).

Settled this session (session 10): **Phase C done** — Entra ID auth via `src/auth.py` (`require_auth`
PyJWT/JWKS guard wired app-wide) + SPA MSAL sign-in gate, verified locally with self-minted tokens (no
Azure spend); `LOCAL_AUTH_BYPASS=1` preserves the unauthenticated local dev path. Roles: **Admin > User**
(the two Entra security groups); group→role map is **env-driven** (no invented group IDs committed) with a
configurable default role. Bypass grants Admin by default; `LOCAL_AUTH_ROLE=User` switches it for live
role-gating tests. **Auth model = shared team workspace** (user decision): any authenticated User works
every bid through all six stages; **Admin-only = the Settings/LLM-config writes** (`PUT`/`POST /api/config`)
— no per-user ownership, so no IDOR/row-scoping needed (unlike TalentGrow, whose data was user-owned).

**From TalentGrow's git history** (`eek2020-old/main`, 47 commits, read locally — no repo exposure needed):
real MSAL login was **never tested against localhost** — they used SWA-CLI mock auth locally, env-gated
real Entra to deploy-only, then went Azure-only (`az login` against a deployed dev env). Confirms our
plan: real sign-in verifies at deploy (Phase D/F); `LOCAL_AUTH_BYPASS` is the local equivalent. Two
carry-forward lessons: (1) the SWA deploy workflow **must inject `VITE_AAD_*`** or the deployed SPA
silently falls back to unauthenticated (their `ca2924e`); (2) real-auth 401s are opaque unless errors are
logged (their `3fbddee`) — our `auth.py` returns the failure reason in the 401 detail already.

Settled session 9, unchanged: **Phase B done** — `db.py` dual-mode via SQLAlchemy Core, verified on a
local SQL Server 2022 container; repurpose the existing 2022 image (not 2025) until `VECTOR` is needed;
Azurite is Blob/Queue/Table only, **not** a SQL emulator (it's scaffolded for later, not used by Phase B).

Settled session 8, unchanged: **Azure/SPA target design** — clone TalentGrow's blueprint (SWA + Functions
Flex + Azure SQL free + Managed Identity everywhere, no Key Vault); Entra ID/MSAL sign-in; `docs/design/azure-target.md` is the plan of record.

Settled session 7, unchanged: journey feature-complete, all 6 stages real; Complete via LocalMirror; Learn built; browser review of stages 1–3/5 done.

Settled earlier, unchanged: Manage (Stage 5) FOR003 + pre-flight gate; flat repo structure; Plan real;
Triage + AI + Settings; six-stage journey shape + visual style approved; library-provider seam; stack =
FastAPI + (now dual-mode) SQLAlchemy/SQLite + React/Vite; shared bid record from `docs/design/data-model.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. Confirm DB state: `python3 src/db.py` → `opportunities: 21`, `qualifications: 3`, `bids: 3`,
   `bid_plans: 3`, `bid_manage: 3`, `bid_responses: 1`, `bid_outcomes: 2` — unless prior testing left
   different rows; check before assuming.
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev` →
   `http://localhost:5173`. Seeders: `seed_plan_demo.py` / `seed_manage_demo.py` / `seed_complete_demo.py`
   / `seed_learn_demo.py` (each takes `--clear`).
4. **Dual-mode DB**: default = local sqlite (`src/bids.db`), no setup. To exercise SQL Server: `docker
   compose up -d --wait db`, then set `DB_URL` (see the SQL Server URL above). `pyodbc` + system
   `msodbcsql18` required for that path only.
5. Complete's library reads the real gitignored export at `knowledge/SharePoint Folder/Bids/`; absent =
   "library not connected" (honest, not a bug). `src/.env` holds the Anthropic key for AI drafting.
6. **Auth (Phase C)**: default local dev is `LOCAL_AUTH_BYPASS=1` (API unauthenticated) + no `VITE_AAD_*`
   (SPA no sign-in gate) — runs like before. See "Auth config quick-reference" above to turn auth on.
   Re-run the backend rig any time: `python3 scratchpad/verify_auth.py` (if the scratchpad persists) —
   or re-derive from `src/auth.py`.
7. Azure migration: `docs/design/azure-target.md` is the plan of record; Phases B (DB) + C (auth) are done,
   Phase D (hosting scaffold) is next (needs Azure).

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`). Optionally `docker compose down`.
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
