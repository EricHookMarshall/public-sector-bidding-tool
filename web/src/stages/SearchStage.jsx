// Stage 01 — Search. The discovery engine's search UI, lifted out of the old
// top-level App so the journey shell can host it alongside the other five
// stages. Logic is unchanged; only the outer page chrome (moved to App.jsx as
// the shared top bar) was removed.
import { useEffect, useState } from "react";
import { getMeta, getOpportunities, getOpportunity, runSearch, downloadExport } from "../api.js";
import { fmtMoney } from "../format.js";

const EMPTY_FILTERS = {
  q: "",
  source: "",
  bid_status: "",
  lifecycle: "",
  country: "",
  region: "",
  currency: "",
  notice_type: "",
  min_value: "",
  max_value: "",
  sort: "deadline_date",
  order: "asc",
};


function fmtDate(s) {
  if (!s) return "—";
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? s : d.toLocaleDateString("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function truncate(s, n = 220) {
  if (!s) return "";
  return s.length > n ? `${s.slice(0, n).trimEnd()}…` : s;
}

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export default function SearchStage() {
  const [meta, setMeta] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  const loadMeta = () => getMeta().then(setMeta).catch((e) => setError(e.message));

  useEffect(() => {
    loadMeta();
  }, []);

  // Refetch whenever filters change (debounced for the keyword box).
  useEffect(() => {
    const t = setTimeout(() => {
      setLoading(true);
      getOpportunities(filters)
        .then((d) => {
          setData(d);
          setError(null);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(t);
  }, [filters]);

  const set = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));

  const openDetail = (id) =>
    getOpportunity(id)
      .then(setSelected)
      .catch((e) => setError(e.message));

  // After a live search, pull fresh meta (new sources/regions/options) + list.
  const afterSearch = () => {
    loadMeta();
    getOpportunities(filters).then(setData).catch((e) => setError(e.message));
  };

  return (
    <>
      {meta && (
        <p className="stage-sub">
          {meta.total} stored ·{" "}
          {meta.by_source.map((s) => `${s.source} (${s.count})`).join(" · ")}
        </p>
      )}

      <SearchPanel meta={meta} onSearched={afterSearch} />

      <div className="layout">
        <aside className="filters">
          <div className="filter-head">
            <h2>Filters</h2>
            <button className="link" onClick={() => setFilters(EMPTY_FILTERS)}>
              Reset
            </button>
          </div>

          <label>
            Keyword
            <input
              type="search"
              placeholder="title, buyer, description, CPV…"
              value={filters.q}
              onChange={set("q")}
            />
          </label>

          <Select label="Source" value={filters.source} onChange={set("source")} options={meta?.sources} />
          <Select
            label="Bid status"
            value={filters.bid_status}
            onChange={set("bid_status")}
            options={["open", "closed", "unknown"]}
          />
          <Select
            label="Lifecycle"
            value={filters.lifecycle}
            onChange={set("lifecycle")}
            options={meta?.lifecycles}
          />
          <Select label="Country" value={filters.country} onChange={set("country")} options={meta?.countries} />
          <RegionSelect
            value={filters.region}
            onChange={set("region")}
            options={meta?.regions}
            labels={meta?.region_labels}
          />
          <Select label="Currency" value={filters.currency} onChange={set("currency")} options={meta?.currencies} />
          <Select
            label="Notice type"
            value={filters.notice_type}
            onChange={set("notice_type")}
            options={meta?.notice_types}
          />

          <div className="row">
            <label>
              Min value
              <input type="number" value={filters.min_value} onChange={set("min_value")} placeholder="0" />
            </label>
            <label>
              Max value
              <input type="number" value={filters.max_value} onChange={set("max_value")} placeholder="∞" />
            </label>
          </div>

          <div className="row">
            <label>
              Sort by
              <select value={filters.sort} onChange={set("sort")}>
                {(meta?.fields || ["deadline_date"]).map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Order
              <select value={filters.order} onChange={set("order")}>
                <option value="asc">Asc</option>
                <option value="desc">Desc</option>
              </select>
            </label>
          </div>
        </aside>

        <main className="results">
          <div className="results-head">
            <span>
              {loading ? "Loading…" : `${data.count} opportunit${data.count === 1 ? "y" : "ies"}`}
            </span>
            <span className="results-actions">
              {error && <span className="error">⚠ {error}</span>}
              <button
                type="button"
                className="export-btn"
                onClick={() => downloadExport(filters).catch((e) => setError(String(e.message || e)))}
                title="Download the current results as CSV"
              >
                ⤓ Export CSV
              </button>
            </span>
          </div>

          <ul className="cards">
            {data.results.map((o) => (
              <li key={o.id} className="card" onClick={() => openDetail(o.id)}>
                <div className="card-top">
                  <h3>{o.title}</h3>
                  <StatusBadge status={o.bid_status} />
                </div>
                <p className="buyer">{o.buyer_name || "Unknown buyer"}</p>
                {o.description && <p className="card-desc">{truncate(o.description)}</p>}
                <div className="card-meta">
                  <span className="source-tag">{o.source}</span>
                  <span>Closes {fmtDate(o.deadline_date)}</span>
                  <span>{fmtMoney(o.value_max, o.currency)}</span>
                  {o.region && (
                    <span title={o.region_label !== o.region ? `Region code: ${o.region}` : undefined}>
                      📍 {o.region_label || o.region}
                    </span>
                  )}
                  {o.cpv_codes && <span>CPV {o.cpv_codes}</span>}
                </div>
              </li>
            ))}
          </ul>
          {!loading && data.results.length === 0 && (
            <p className="empty">No opportunities match these filters.</p>
          )}
        </main>
      </div>

      {selected && <Detail opp={selected} onClose={() => setSelected(null)} />}
    </>
  );
}

// ---- Live search panel: drives the upstream fetch (CPV / stage / dates / sources) ----
function SearchPanel({ meta, onSearched }) {
  const opts = meta?.search_options;
  const [open, setOpen] = useState(false);
  const [sources, setSources] = useState([]);
  const [cpv, setCpv] = useState([]);
  const [cpvInput, setCpvInput] = useState("");
  const [stage, setStage] = useState("tender");
  const [openOnly, setOpenOnly] = useState(true);
  const [useDates, setUseDates] = useState(false);
  const [days, setDays] = useState(120);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState(null);
  const [err, setErr] = useState(null);
  const [seeded, setSeeded] = useState(false);

  // Seed the whole form from the team's persisted search defaults (S3) the first
  // time the options arrive — falling back to the code defaults if unset.
  useEffect(() => {
    if (!opts || seeded) return;
    const d = opts.defaults || {};
    setSources(d.sources ?? opts.sources.map((s) => s.key));
    setCpv(d.cpv_codes ?? opts.default_cpv);
    setStage(d.stage ?? "tender");
    setOpenOnly(d.open_only ?? true);
    setDays(d.days ?? 120);
    setSeeded(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts]);

  if (!opts) return null;

  const toggleSource = (key) =>
    setSources((s) => (s.includes(key) ? s.filter((k) => k !== key) : [...s, key]));

  const cpvCatalog = meta?.cpv_catalog || [];
  const cpvLabels = Object.fromEntries(cpvCatalog.map((c) => [c.code, c.description]));

  const addCode = (code) => setCpv((c) => (c.includes(code) ? c : [...c, code]));
  const addCpv = () => {
    const codes = cpvInput
      .split(/[\s,]+/)
      .map((c) => c.trim())
      .filter((c) => /^\d{2,8}$/.test(c) && !cpv.includes(c));
    if (codes.length) setCpv((c) => [...c, ...codes]);
    setCpvInput("");
  };
  const removeCpv = (code) => setCpv((c) => c.filter((x) => x !== code));

  const onCpvKey = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addCpv();
    }
  };

  const run = async () => {
    setRunning(true);
    setErr(null);
    setSummary(null);
    try {
      const res = await runSearch({
        sources,
        cpv_codes: cpv.length ? cpv : null,
        stage,
        open_only: openOnly,
        days: Number(days) || 120,
        published_from: useDates && from ? from : null,
        published_to: useDates && to ? to : null,
      });
      setSummary(res);
      onSearched();
    } catch (e) {
      setErr(e.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="search-panel">
      <button className="search-toggle" onClick={() => setOpen((o) => !o)}>
        <span>{open ? "▾" : "▸"} Run a live search</span>
        <span className="hint">add/remove CPV codes, pick sources, stages & date range</span>
      </button>

      {open && (
        <div className="search-body">
          <div className="search-grid">
            <div className="search-field">
              <label>Sources</label>
              <div className="checks">
                {opts.sources.map((s) => (
                  <label key={s.key} className="check" title={s.note}>
                    <input
                      type="checkbox"
                      checked={sources.includes(s.key)}
                      onChange={() => toggleSource(s.key)}
                    />
                    {s.name}
                  </label>
                ))}
              </div>
            </div>

            <div className="search-field">
              <label>Stage</label>
              <select value={stage} onChange={(e) => setStage(e.target.value)}>
                {opts.stages.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <label className="check inline">
                <input
                  type="checkbox"
                  checked={openOnly}
                  onChange={(e) => setOpenOnly(e.target.checked)}
                />
                Only still-open notices
              </label>
            </div>

            <div className="search-field">
              <label>Date window</label>
              <div className="seg">
                <button className={!useDates ? "on" : ""} onClick={() => setUseDates(false)}>
                  Last N days
                </button>
                <button className={useDates ? "on" : ""} onClick={() => setUseDates(true)}>
                  Date range
                </button>
              </div>
              {!useDates ? (
                <input
                  type="number"
                  min="1"
                  value={days}
                  onChange={(e) => setDays(e.target.value)}
                  title="How many days back to search"
                />
              ) : (
                <div className="row">
                  <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} title="From" />
                  <input type="date" value={to} onChange={(e) => setTo(e.target.value)} title="To" />
                </div>
              )}
            </div>
          </div>

          <div className="search-field cpv-field">
            <label>CPV codes ({cpv.length})</label>
            <div className="chips">
              {cpv.map((c) => (
                <span key={c} className="chip" title={cpvLabels[c] || "custom code"}>
                  {c}
                  {cpvLabels[c] && <span className="chip-desc">{cpvLabels[c]}</span>}
                  <button onClick={() => removeCpv(c)} aria-label={`remove ${c}`}>
                    ×
                  </button>
                </span>
              ))}
              {cpv.length === 0 && <span className="chip-empty">none — connector default will be used</span>}
            </div>
            <div className="cpv-add">
              <select
                className="cpv-picker"
                value=""
                onChange={(e) => {
                  if (e.target.value) addCode(e.target.value);
                }}
              >
                <option value="">＋ Add from CPV list…</option>
                {cpvCatalog.map((c) => (
                  <option key={c.code} value={c.code} disabled={cpv.includes(c.code)}>
                    {c.code} — {c.description}
                  </option>
                ))}
              </select>
              <input
                type="text"
                placeholder="or type custom code(s), e.g. 79000000"
                value={cpvInput}
                onChange={(e) => setCpvInput(e.target.value)}
                onKeyDown={onCpvKey}
              />
              <button onClick={addCpv}>Add</button>
              <button className="link" onClick={() => setCpv(opts.default_cpv)}>
                Reset to default
              </button>
              <button className="link" onClick={() => setCpv([])}>
                Clear
              </button>
            </div>
          </div>

          <div className="search-run">
            <button className="run-btn" onClick={run} disabled={running || sources.length === 0}>
              {running ? "Searching… (Contracts Finder is rate-limited, may take ~30s)" : "Run search"}
            </button>
            {err && <span className="error">⚠ {err}</span>}
            {summary && (
              <span className="run-summary">
                {summary.runs.map((r) => (
                  <span key={r.key} className={r.ok ? "ok" : "bad"}>
                    {r.source}:{" "}
                    {r.ok
                      ? `scanned ${r.scanned}, kept ${r.kept} (${r.inserted} new, ${r.updated} updated)`
                      : `failed — ${r.error}`}
                  </span>
                ))}
              </span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <label>
      {label}
      <select value={value} onChange={onChange}>
        <option value="">All</option>
        {(options || []).map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

// Region filter that shows the human label but filters on the stored code.
function RegionSelect({ value, onChange, options, labels }) {
  return (
    <label>
      Region
      <select value={value} onChange={onChange}>
        <option value="">All</option>
        {(options || []).map((o) => (
          <option key={o} value={o}>
            {labels?.[o] && labels[o] !== o ? `${o} — ${labels[o]}` : o}
          </option>
        ))}
      </select>
    </label>
  );
}

const FIELD_ORDER = [
  "title", "buyer_name", "source", "source_endpoint", "ocid", "notice_id",
  "status", "bid_status", "lifecycle", "notice_type", "cpv_codes",
  "region", "region_label", "country",
  "value_min", "value_max", "currency", "published_date", "deadline_date",
  "last_seen_at", "url", "description",
];

function Detail({ opp, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h2>{opp.title}</h2>
            <p className="buyer">{opp.buyer_name}</p>
          </div>
          <button className="close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="badges">
          <span className="source-tag">{opp.source}</span>
          <StatusBadge status={opp.bid_status} />
          {opp.status && <span className="badge">{opp.status}</span>}
        </div>

        <div className="detail-actions">
          {opp.url && (
            <a className="cta" href={opp.url} target="_blank" rel="noreferrer">
              View original notice ↗
            </a>
          )}
          {/* The Search → Triage handoff: hand this opportunity to Stage 2. The
              id rides in sessionStorage so it survives the hash navigation; the
              Triage stage picks it up on mount. */}
          <button
            className="cta cta-triage"
            onClick={() => {
              sessionStorage.setItem("bidpath.triage.opp", String(opp.id));
              window.location.hash = "triage";
            }}
          >
            ▲ Triage this →
          </button>
        </div>

        <table className="fields">
          <tbody>
            {FIELD_ORDER.filter((k) => k in opp && k !== "title" && k !== "buyer_name").map((k) => (
              <tr key={k}>
                <th>{k}</th>
                <td>{renderField(k, opp[k])}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {opp.raw_json && (
          <details className="raw">
            <summary>Raw source payload</summary>
            <pre>{JSON.stringify(opp.raw_json, null, 2)}</pre>
          </details>
        )}
      </div>
    </div>
  );
}

function renderField(key, value) {
  if (value === null || value === undefined || value === "") return "—";
  if (key === "url") {
    return (
      <a href={value} target="_blank" rel="noreferrer">
        {value}
      </a>
    );
  }
  if ((key === "value_min" || key === "value_max") && typeof value === "number") {
    return new Intl.NumberFormat("en-GB").format(value);
  }
  return String(value);
}
