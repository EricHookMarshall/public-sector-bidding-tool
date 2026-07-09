// Thin wrapper over the FastAPI JSON endpoints. In dev, Vite proxies /api -> :8000.

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const getMeta = () => getJSON("/api/meta");

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

// CSV download URL for the current filter set (used by an <a download> / button).
export const exportUrl = (filters) => `/api/export?${filterParams(filters).toString()}`;

// Live search: POST the chosen CPV/stage/date/source params; connectors run
// upstream and upsert into bids.db. Returns a per-source summary.
export async function runSearch(body) {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return res.json();
}

// ---- Stage 2: Triage / FOR001 qualification ----

// FOR001 vocabulary (complexity levels, day-rate table, RAG criteria, roles).
export const getTriageReference = () => getJSON("/api/triage/reference");

// The Triage view for one opportunity: qualification (saved or seeded), the live
// bid economics, and any spun-off bid.
export const getQualification = (oppId) =>
  getJSON(`/api/opportunities/${oppId}/qualification`);

// Save the FOR001 qualification; server recomputes economics + RAG and, on a Go
// decision, promotes the opportunity into a Bid. Returns the same shape as GET.
export async function saveQualification(oppId, fields) {
  const res = await fetch(`/api/opportunities/${oppId}/qualification`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return res.json();
}

// AI-draft the qualification from the notice. Returns {draft, meta}; the draft is
// for review only (not saved). Throws with the server detail on 503 (no LLM
// configured) or other errors, so the UI can show why AI drafting is unavailable.
export async function aiDraftQualification(oppId) {
  const res = await fetch(`/api/opportunities/${oppId}/qualification/ai-draft`, {
    method: "POST",
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return res.json();
}

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
export async function saveBidPlan(bidId, fields) {
  const res = await fetch(`/api/bids/${bidId}/plan`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return res.json();
}

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
export async function saveBidManage(bidId, fields) {
  const res = await fetch(`/api/bids/${bidId}/manage`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return res.json();
}

// ---- Settings: LLM config ----

async function sendJSON(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return res.json();
}

// Never returns the API key — only provider/model/options + key status.
export const getConfig = () => getJSON("/api/config");

// Save provider/model/key. Omit api_key (or send blank) to leave the stored key
// untouched. Returns the refreshed config.
export const saveConfig = (body) => sendJSON("/api/config", "PUT", body);

// Cheap live round-trip to verify the current key + model. Throws on failure.
export const testConfig = () => sendJSON("/api/config/test", "POST");
