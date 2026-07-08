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
