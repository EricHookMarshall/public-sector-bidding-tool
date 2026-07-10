# Entra ID app-registration setup — hand-off to the Azure Admin

> **What this is:** the exact Microsoft Entra ID (Azure AD) objects an admin must
> create so the bidding tool's Phase C auth can go live, and where each returned
> value plugs into the app's config. Grounded in what the code actually validates:
> [`src/auth.py`](../../src/auth.py) (API token validation) and
> [`web/src/authConfig.js`](../../web/src/authConfig.js) (SPA MSAL sign-in).
>
> **Cost:** none. App registrations and Entra security groups are free — no Azure
> subscription or spend required. A dev tenant is enough to test the sign-in flow.
>
> **Pattern:** two app registrations (API + SPA) + two security groups, cloned from
> the TalentGrow blueprint. See [`azure-target.md`](azure-target.md) for the wider
> migration plan.

## What to ask the Admin to create

### 1. API app registration — the FastAPI backend (this is the token *audience*)

- Name it e.g. `fwf-bidding-api`.
- **Expose an API**: set the Application ID URI to `api://<this-app's-client-id>`,
  then **Add a scope** named exactly `access_as_user` (admin + user consent, enabled).
- **Token configuration**: add a **groups claim** → type **Security groups**,
  emitted into the **Access token**. ⚠️ *Critical — without this the token carries no
  `groups` claim and the API silently falls back to the default role.*
- No client secret needed — the API only *validates* tokens, it never calls Graph.

### 2. SPA app registration — the React frontend

- Name it e.g. `fwf-bidding-spa`.
- Platform: **Single-page application** (not "Web" — this selects PKCE, which MSAL
  in the browser requires).
- Redirect URIs: `http://localhost:5173` (local dev) and later the Static Web App
  URL (e.g. `https://<your-swa>.azurestaticapps.net`).
- **API permissions**: add a **delegated** permission to `fwf-bidding-api` →
  `access_as_user`, then **Grant admin consent**.

### 3. Two Entra security groups

- `FWF Bidding – Admin` and `FWF Bidding – User`.
- Add yourself to Admin; put employees in User.
- Ask the Admin for each group's **Object ID** (a GUID).

## What you get back, and where each value goes

| Value from Admin | Config key | Side |
|---|---|---|
| Tenant ID (GUID) | `AAD_TENANT_ID` / `VITE_AAD_TENANT_ID` | API + SPA |
| API app client ID | `AAD_API_CLIENT_ID` (= token audience) | API |
| SPA app client ID | `VITE_AAD_CLIENT_ID` | SPA |
| API scope URI | `VITE_AAD_API_SCOPE` = `api://<API-client-id>/access_as_user` | SPA |
| Admin + User group Object IDs | `AAD_GROUP_ROLE_MAP` (JSON) | API |

### API side — `src/.env` (see [`src/.env.example`](../../src/.env.example))

```
LOCAL_AUTH_BYPASS=0
AAD_TENANT_ID=<tenant-guid>
AAD_API_CLIENT_ID=<api-client-id>
AAD_GROUP_ROLE_MAP={"<admin-group-oid>":"Admin","<user-group-oid>":"User"}
```

### SPA side — `web/.env` (see [`web/.env.example`](../../web/.env.example))

```
VITE_AAD_CLIENT_ID=<spa-client-id>
VITE_AAD_TENANT_ID=<tenant-guid>
VITE_AAD_API_SCOPE=api://<api-client-id>/access_as_user
```

Both `.env` files are git-ignored. The `VITE_*` values are public (baked into the
browser bundle) — client IDs, tenant ID and scope are **not** secrets. Never put an
API key or client secret in `web/.env`.

## Two gotchas to state up front to the Admin

- **The groups claim must target the *access* token**, not just the ID token — the
  API reads `groups` off the access token it validates
  ([`src/auth.py:208`](../../src/auth.py#L208)). This is the single most common thing
  that gets missed.
- The code validates **v2 tokens** (issuer `.../v2.0`, audience = the API's
  client-ID GUID). The `access_as_user` scope naturally yields a v2 access token with
  the correct audience, so no manifest change is needed — but if the Admin has an old
  app registration pinned to v1, flag it.

## After you have the values — the Phase C tail (live sign-in test)

This is the parked "Phase C tail" from the handover. It's the only part that needs a
real tenant; everything else was already verified locally with self-minted tokens.

1. Fill in `src/.env` and `web/.env` as above; set `LOCAL_AUTH_BYPASS=0`.
2. Start the API (`uvicorn api:app --app-dir src --reload --port 8000`) and the SPA
   (`cd web && npm run dev`).
3. Sign in through the MSAL gate.
4. Confirm the Bearer token reaches the API (routes return 200, not 401).
5. Confirm role-gating live: an **Admin**-group user can write Settings
   (`PUT /api/config`); a **User**-group user gets **403** on the same route while the
   six-stage journey still works.

To revert to unauthenticated local dev at any time, set `LOCAL_AUTH_BYPASS=1` and
leave the `VITE_AAD_*` vars unset — the app runs exactly as the PoC did.

## Reverting / how the seams fail safe

- **Bypass on (`LOCAL_AUTH_BYPASS=1`)**: API is unauthenticated (synthetic Admin);
  SPA has no sign-in gate. Default local-dev posture.
- **Bypass off but misconfigured**: the API **fails closed** — a 500 if
  `AAD_TENANT_ID`/`AAD_API_CLIENT_ID` are missing, or if no group-role policy is set.
  It never silently runs open.
- **SPA env vars absent**: no sign-in gate, plain same-origin fetch — pairs with
  bypass-on for local dev.
