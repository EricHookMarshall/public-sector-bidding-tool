// Entra ID (Azure AD) sign-in config — Azure-migration Phase C. Clones
// TalentGrow's authConfig.ts. These come from build-time env vars (set in the
// SWA deploy workflow, or a local web/.env for dev against a dev-tenant app reg):
//
//   VITE_AAD_CLIENT_ID   SPA app-registration client id
//   VITE_AAD_TENANT_ID   Entra tenant GUID
//   VITE_AAD_API_SCOPE   the API's exposed scope, e.g.
//                        api://<api-client-id>/access_as_user
//
// When all three are present the SPA signs in with MSAL and attaches a Bearer
// token on every /api/* call (see api.js). When they're ABSENT — the default
// for local dev — the SPA runs unauthenticated exactly as before, pairing with
// the backend's LOCAL_AUTH_BYPASS shim. No Entra config, no sign-in gate.
import { PublicClientApplication } from "@azure/msal-browser";

const clientId = import.meta.env.VITE_AAD_CLIENT_ID;
const tenantId = import.meta.env.VITE_AAD_TENANT_ID;
const apiScope = import.meta.env.VITE_AAD_API_SCOPE;

export const isAadConfigured = Boolean(clientId && tenantId && apiScope);

// Scopes requested when acquiring the API access token.
export const apiScopes = apiScope ? [apiScope] : [];

const msalConfig = {
  auth: {
    clientId: clientId ?? "",
    authority: tenantId ? `https://login.microsoftonline.com/${tenantId}` : undefined,
    redirectUri: "/",
  },
  // sessionStorage over localStorage: the token cache is scoped to the tab and
  // cleared when it closes, so a cached access token can't linger on a shared
  // machine or be read by another tab. Trade-off is a re-auth per new tab, which
  // is a silent redirect against a live Entra session.
  cache: { cacheLocation: "sessionStorage" },
};

// Null when Entra isn't configured — App.jsx / main.jsx branch on that so the
// app never depends on MSAL in local dev.
export const msalInstance = isAadConfigured ? new PublicClientApplication(msalConfig) : null;
