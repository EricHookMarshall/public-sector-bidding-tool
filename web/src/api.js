// Thin wrapper over the FastAPI JSON endpoints. In dev, Vite proxies /api -> :8000.
//
// Every call goes through apiFetch, the single place that (a) prefixes the API
// base URL when the SPA and API are separate origins (Azure SWA → Function App,
// VITE_API_BASE_URL) and (b) attaches the Entra ID Bearer token when MSAL is
// configured (Phase C). With neither env var set — local dev — it's a plain
// same-origin fetch, so the app behaves exactly as before against the
// LOCAL_AUTH_BYPASS backend.
import { msalInstance, apiScopes, isAadConfigured } from "./authConfig.js";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

function resolveUrl(path) {
  return apiBaseUrl && path.startsWith("/api/") ? `${apiBaseUrl}${path}` : path;
}

// Bearer header for an /api/* call, or {} when auth isn't configured / no token
// is obtainable (the request then gets a clean 401 from the API). A silent
// token renewal failure falls back to a full-page interactive redirect — a
// first-party navigation that works whenever the user has a live Entra session.
async function authHeader(path) {
  if (!isAadConfigured || !msalInstance || !path.startsWith("/api/")) return {};
  const account = msalInstance.getActiveAccount() ?? msalInstance.getAllAccounts()[0];
  if (!account) return {};
  try {
    const { accessToken } = await msalInstance.acquireTokenSilent({ scopes: apiScopes, account });
    return { Authorization: `Bearer ${accessToken}` };
  } catch (err) {
    // Stable message in every build; the raw MSAL error object (tokens/claims/URLs)
    // is gated to dev so it never lands in the deployed browser console.
    console.error("[api] silent token acquisition failed; redirecting to sign in");
    if (import.meta.env.DEV) console.error(err);
    try {
      await msalInstance.acquireTokenRedirect({ scopes: apiScopes, account });
    } catch (redirectErr) {
      console.error("[api] interactive redirect failed");
      if (import.meta.env.DEV) console.error(redirectErr);
    }
    return {};
  }
}

// The one fetch every helper below routes through. Merges the auth header and
// resolves the base URL; callers still pass their own method/body/headers.
async function apiFetch(path, init = {}) {
  const auth = await authHeader(path);
  return fetch(resolveUrl(path), {
    ...init,
    headers: { ...(init.headers || {}), ...auth },
  });
}

// Build an Error from a non-OK response, preferring the API's JSON `detail`
// (e.g. the pre-flight 409 reason, or a 403 from the Entra role gate) over the
// bare status text. One place so every helper surfaces failures the same way.
async function errorFrom(res) {
  let detail = `${res.status} ${res.statusText}`;
  try {
    const j = await res.json();
    if (j.detail) detail = j.detail;
  } catch { /* non-JSON body — keep status text */ }
  return new Error(detail);
}

async function getJSON(url) {
  const res = await apiFetch(url);
  if (!res.ok) throw await errorFrom(res);
  return res.json();
}

// POST/PUT a JSON body (or no body) and parse the JSON result. `sendJSON` is the
// single mutating-request helper every save/draft endpoint routes through, so the
// error shape and auth/base-URL handling stay identical across all of them.
async function sendJSON(url, method, body) {
  const res = await apiFetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw await errorFrom(res);
  return res.json();
}

// Multipart POST (file uploads). Deliberately does NOT set Content-Type — the
// browser sets it with the correct boundary. Routes through apiFetch so auth +
// base-URL handling stay identical to the JSON helpers.
async function sendForm(url, method, formData) {
  const res = await apiFetch(url, { method, body: formData });
  if (!res.ok) throw await errorFrom(res);
  return res.json();
}

export const getMeta = () => getJSON("/api/meta");

// The signed-in caller's identity ({role, display_name, email, via}) — drives
// role-aware UI (e.g. hiding the Admin-only Settings gear). The API still
// enforces every gate server-side regardless of what the UI shows.
export const getAuthMe = () => getJSON("/api/auth/me");

function filterParams(filters) {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v !== "" && v !== null && v !== undefined) params.set(k, v);
  }
  return params;
}

export function getOpportunities(filters) {
  return getJSON(`/api/opportunities?${filterParams(filters).toString()}`);
}

export const getOpportunity = (id) => getJSON(`/api/opportunities/${id}`);

// Download the current filter set as CSV. Goes through apiFetch (so it carries
// the Entra Bearer + the VITE_API_BASE_URL prefix on Azure) and streams the body
// into a Blob download — an <a href> can't attach an Authorization header, so a
// plain link would 404/401 once the SPA and API are on separate authenticated
// origins. Local dev is unchanged (same-origin, no token).
export async function downloadExport(filters) {
  const res = await apiFetch(`/api/export?${filterParams(filters).toString()}`);
  if (!res.ok) throw await errorFrom(res);
  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = "opportunities.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}

// Live search: POST the chosen CPV/stage/date/source params; connectors run
// upstream and upsert into bids.db. Returns a per-source summary.
export const runSearch = (body) => sendJSON("/api/search", "POST", body);

// ---- Stage 2: Triage / FOR001 qualification ----

// FOR001 vocabulary (complexity levels, day-rate table, RAG criteria, roles).
export const getTriageReference = () => getJSON("/api/triage/reference");

// The Triage card board: every pickable opportunity with its triage state
// (untriaged / decided / bid live) + a funnel summary.
export const getTriageBoard = () => getJSON("/api/triage/board");

// Pull an opportunity into the Triage board (the "Triage this →" handoff), or
// remove it. Selection controls Triage membership only — it stays in Search.
export const setTriageSelected = (oppId, selected) =>
  sendJSON(`/api/opportunities/${oppId}/triage-select`, "PUT", { selected });

// Reversibly dismiss an opportunity from the Triage board (or restore it).
// Dismissal only hides it from Triage — it stays in Search and the DB.
export const setTriageDismissed = (oppId, dismissed) =>
  sendJSON(`/api/opportunities/${oppId}/triage-dismiss`, "PUT", { dismissed });

// The Triage view for one opportunity: qualification (saved or seeded), the live
// bid economics, and any spun-off bid.
export const getQualification = (oppId) =>
  getJSON(`/api/opportunities/${oppId}/qualification`);

// Save the FOR001 qualification; server recomputes economics + RAG and, on a Go
// decision, promotes the opportunity into a Bid. Returns the same shape as GET.
export const saveQualification = (oppId, fields) =>
  sendJSON(`/api/opportunities/${oppId}/qualification`, "PUT", fields);

// AI-draft the qualification from the notice. Returns {draft, meta}; the draft is
// for review only (not saved). Throws with the server detail on 503 (no LLM
// configured) or other errors, so the UI can show why AI drafting is unavailable.
export const aiDraftQualification = (oppId) =>
  sendJSON(`/api/opportunities/${oppId}/qualification/ai-draft`, "POST");

// ---- Stage 3: Plan / FOR002 bid plan ----

// FOR002 vocabulary (pipeline stages, phase list, owner roles, statuses).
export const getPlanReference = () => getJSON("/api/plan/reference");

// The cross-bid Plan board: bids grouped into pipeline columns, plus the
// team-capacity summary and the computed deadline/owner/capacity alerts.
export const getPlanBoard = (capacityDays) =>
  getJSON(`/api/plan/board${capacityDays ? `?capacity_days=${capacityDays}` : ""}`);

// One bid's FOR002 plan (pipeline position + phase timeline), seeded if unsaved,
// with the bid/opportunity context the timeline shows.
export const getBidPlan = (bidId) => getJSON(`/api/bids/${bidId}/plan`);

// Save a bid's plan (pipeline position, owner, dates, phases). Returns GET shape.
export const saveBidPlan = (bidId, fields) =>
  sendJSON(`/api/bids/${bidId}/plan`, "PUT", fields);

// ---- Stage 5: Manage / FOR003 CQLOG + pre-flight gate ----

// FOR003 vocabulary (clarification statuses, pre-flight checklist template).
export const getManageReference = () => getJSON("/api/manage/reference");

// The cross-bid Manage board: every live bid with its clarification-register
// summary + pre-flight readiness, plus the computed clarification/gate alerts.
export const getManageBoard = () => getJSON("/api/manage/board");

// One bid's FOR003 register + resolved pre-flight checklist (seeded if unsaved),
// with the bid/opportunity context the register shows.
export const getBidManage = (bidId) => getJSON(`/api/bids/${bidId}/manage`);

// Save a bid's manage record (register, pre-flight, notes, submitted flag).
// Marking submitted only sticks if the pre-flight gate is clear (else a 409 with
// the reason). Returns GET shape.
export const saveBidManage = (bidId, fields) =>
  sendJSON(`/api/bids/${bidId}/manage`, "PUT", fields);

// ---- Stage 4: Complete / FOR006 matrix + library pre-fill ----

// FOR006 vocabulary (response statuses, question types) + library categories.
export const getCompleteReference = () => getJSON("/api/complete/reference");

// The cross-bid Complete board: every bid with its FOR006 matrix completion, plus
// the shared library provider status.
export const getCompleteBoard = () => getJSON("/api/complete/board");

// Browse the shared bid library (LocalMirror). Optional category / q filter.
export const getLibrary = (params = {}) =>
  getJSON(`/api/library?${filterParams(params).toString()}`);

// One bid's FOR006 matrix (seeded from the master template if unstarted) + the
// completion summary, evidence ledger, and library provider status.
export const getBidResponses = (bidId) => getJSON(`/api/bids/${bidId}/responses`);

// Save a bid's response matrix. Server recomputes word counts + validates status.
// Returns GET shape.
export const saveBidResponses = (bidId, fields) =>
  sendJSON(`/api/bids/${bidId}/responses`, "PUT", fields);

// AI-draft one answer, retrieval-grounded in the real library. Identified by the
// question's row index (question_ref repeats across lots). Returns {item_index,
// question_ref, draft, matches, meta}; the draft is for review only (not saved).
// Throws with the server detail on 503 (no LLM) or other errors.
export const aiDraftResponse = (bidId, itemIndex) =>
  sendJSON(`/api/bids/${bidId}/responses/${itemIndex}/ai-draft`, "POST");

// ---- Stage 6: Learn / B07 Outcome + Lessons Learned ----

// B07 vocabulary (results, lesson categories, library actions).
export const getLearnReference = () => getJSON("/api/learn/reference");

// The cross-bid Learn board: every bid with its recorded outcome, the win-rate
// summary tracked bid-by-bid, and the loop-closing alerts.
export const getLearnBoard = () => getJSON("/api/learn/board");

// One bid's B07 outcome + derived library suggestions (seeded blank if unrecorded),
// with the bid/opportunity context the form shows.
export const getBidOutcome = (bidId) => getJSON(`/api/bids/${bidId}/outcome`);

// Save a bid's outcome (result, score, feedback, lessons, library sign-off).
// Returns GET shape so the UI can re-render in place.
export const saveBidOutcome = (bidId, fields) =>
  sendJSON(`/api/bids/${bidId}/outcome`, "PUT", fields);

// ---- Settings: LLM config ----

// Never returns the API key — only provider/model/options + key status.
export const getConfig = () => getJSON("/api/config");

// Save provider/model/key. Omit api_key (or send blank) to leave the stored key
// untouched. Returns the refreshed config.
export const saveConfig = (body) => sendJSON("/api/config", "PUT", body);

// Cheap live round-trip to verify the current key + model. Throws on failure.
export const testConfig = () => sendJSON("/api/config/test", "POST");

// Bid-writing day rates (per FOR001 role) that drive the "cost to chase".
export const getDayRates = () => getJSON("/api/settings/day-rates");
export const saveDayRates = (rates) =>
  sendJSON("/api/settings/day-rates", "PUT", { rates });

// Editable AI prompt context (profile + per-stage guidance). Send only what
// changed; a blank profile falls back to the built-in default.
export const getAiPrompts = () => getJSON("/api/settings/ai-prompts");
export const saveAiPrompts = (body) =>
  sendJSON("/api/settings/ai-prompts", "PUT", body);

// Team bid-writing capacity (person-days) the Plan board measures commitment against.
export const getTeamCapacity = () => getJSON("/api/settings/team-capacity");
export const saveTeamCapacity = (capacity_days) =>
  sendJSON("/api/settings/team-capacity", "PUT", { capacity_days });

// Team roster — the people who own bids/phases/clarifications; feeds the owner
// dropdowns on Plan and Manage.
export const getTeamRoster = () => getJSON("/api/settings/team-roster");
export const saveTeamRoster = (people) =>
  sendJSON("/api/settings/team-roster", "PUT", { people });

// Live-search defaults (CPV scope, sources, stage, window) the Search form seeds from.
export const getSearchDefaults = () => getJSON("/api/settings/search-defaults");
export const saveSearchDefaults = (body) =>
  sendJSON("/api/settings/search-defaults", "PUT", body);

// ---- Our awarded contracts (G1) ----

// FWF's own-org identity (the Companies House number that drives award matching).
export const getOwnOrg = () => getJSON("/api/settings/own-org");
export const saveOwnOrg = (body) => sendJSON("/api/settings/own-org", "PUT", body);

// The board of FWF's own awarded contracts + summary + own-org config.
export const getAwardsBoard = () => getJSON("/api/awards/board");

// Pull awards from the OCDS award packages and upsert them (Admin; hits live APIs).
export const refreshAwards = (days = 365) =>
  sendJSON(`/api/awards/refresh?days=${days}`, "POST");

// Record a known award public OCDS can't surface (named-only / sub-threshold /
// subcontract). Stored as an internal record, never a faked public match (Admin).
export const addManualAward = (body) => sendJSON("/api/awards/manual", "POST", body);

// Remove an award by primary key — for correcting a manual entry (Admin).
export const deleteAward = (id) => sendJSON(`/api/awards/${id}`, "DELETE");

// ---- Framework radar (G2) ----

// Candidate GCA agreements relevant to FWF, each scored (act/pursue/prepare/
// maintain/watch/skip) live against today, with a recommendation summary.
export const getFrameworksRadar = () => getJSON("/api/frameworks/radar");

// ---- How to supply reference (G3) ----

// Curated, read-only help on the UK routes to market (frameworks, dynamic
// markets, DPS, catalogues, finding notices) + a getting-started path and help
// links. Static/re-verifiable content — carries a `verified` date.
export const getSupplyReference = () => getJSON("/api/supply/reference");

// ---- Compliance & Renewals (C-series) ----

// Vocabulary for the Compliance view (categories + the expiring-soon window).
export const getComplianceReference = () => getJSON("/api/compliance/reference");

// The org-level register: every asset with derived expiry status (sorted
// soonest-to-lapse first), status counts, and whether a library import is offerable.
export const getComplianceBoard = () => getJSON("/api/compliance/board");

// Register (or upload) an asset. `fields` = {name, category, expiry_date,
// review_frequency, owner, notes}; `file` optional (a File from an <input>). When
// a file is present the bytes go to the store; otherwise it's a reference.
export const createComplianceAsset = (fields, file) => {
  const fd = new FormData();
  Object.entries(fields).forEach(([k, v]) => fd.append(k, v ?? ""));
  if (file) fd.append("file", file);
  return sendForm("/api/compliance/assets", "POST", fd);
};

// Update an asset's metadata (name/category/expiry/owner/notes/review). Returns
// the refreshed asset so the UI can re-render in place.
export const updateComplianceAsset = (id, fields) =>
  sendJSON(`/api/compliance/assets/${id}`, "PUT", fields);

// Delete an asset (and its stored file).
export const deleteComplianceAsset = (id) =>
  sendJSON(`/api/compliance/assets/${id}`, "DELETE");

// Seed the register from the bid library's credential items (idempotent — only
// populates an empty register). Throws 409 if the library isn't available.
export const importComplianceFromLibrary = () =>
  sendJSON("/api/compliance/import-from-library", "POST");

// Download an asset's stored file. Fetches through apiFetch (so the Entra Bearer
// is attached when auth is on) and triggers a browser save via a blob URL.
export const downloadComplianceAsset = async (id, filename) => {
  const res = await apiFetch(`/api/compliance/assets/${id}/file`);
  if (!res.ok) throw await errorFrom(res);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || `asset-${id}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};
