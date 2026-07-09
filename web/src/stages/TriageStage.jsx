// Stage 02 — Triage. The bid/no-bid gate, wired to real data. This is FWF's
// FOR001 Bid Qualification Questionnaire as a live form: pick a stored
// opportunity, fill the qualification (seeded from the notice), pick a
// complexity to get FWF's real "cost to chase", RAG-score the win criteria, and
// make the call. A "Go" promotes the opportunity into a Bid (the spine the
// later stages attach to). No mock data — everything here reads/writes bids.db.
import { useEffect, useMemo, useState } from "react";
import {
  getOpportunities, getTriageReference, getQualification, saveQualification,
  aiDraftQualification,
} from "../api.js";

// Handoff key set by Search's "Triage this" action (sessionStorage, so it
// survives the hash navigation between stages without an app-wide store).
const HANDOFF_KEY = "bidpath.triage.opp";

// FOR001 "Qualification" text fields — [key, label, "area"? for a textarea].
const DETAIL_FIELDS = [
  ["client_name", "Client name"],
  ["sales_owner", "Sales owner"],
  ["framework", "Framework"],
  ["platforms", "Platform(s)"],
  ["estimated_value", "Estimated value (customer budget)"],
  ["estimated_start_date", "Estimated start date"],
  ["estimated_duration", "Estimated duration"],
  ["pricing_weighting", "Pricing weighting (quality/price)"],
  ["lots_breakdown", "Lots breakdown"],
  ["team_location", "Team location"],
  ["partner_required", "Partner required?"],
];
const AREA_FIELDS = [
  ["project_requirement_sentence", "Project requirement (one sentence)"],
  ["scope_summary", "Scope summary"],
];
const DATE_FIELDS = [
  ["response_open_date", "Response open date"],
  ["clarification_deadline", "Clarification deadline"], // the founding-failure field
  ["submission_deadline", "Submission deadline"],
  ["presentation_date", "Presentation date"],
];

function fmtMoney(n) {
  if (n === null || n === undefined || n === "" || Number.isNaN(Number(n))) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency", currency: "GBP", maximumFractionDigits: 0,
  }).format(Number(n));
}

// Client-side mirror of qualification.rag_summary — instant feedback while the
// user scores; the server recomputes authoritatively on save. Score is a green
// rating (high = low risk), so 3→Low, 2→Med, 1→High risk.
function ragSummary(scores) {
  const vals = Object.values(scores || {}).filter((v) => v >= 1 && v <= 3);
  if (!vals.length) return { rating: null, label: null };
  const rating = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
  return { rating, label: { 3: "Low", 2: "Med", 1: "High" }[rating] };
}

const RAG_PILL = { 3: "p-pass", 2: "p-unk", 1: "p-fail" };

export default function TriageStage() {
  const [ref, setRef] = useState(null);
  const [opps, setOpps] = useState([]);
  const [oppId, setOppId] = useState("");
  const [view, setView] = useState(null);   // full /qualification payload
  const [form, setForm] = useState(null);    // editable qualification
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNote, setSavedNote] = useState(null);
  const [drafting, setDrafting] = useState(false);
  const [aiMeta, setAiMeta] = useState(null);   // AI rationale, shown for review

  // Load the FOR001 vocabulary + the pickable opportunity list once.
  useEffect(() => {
    Promise.all([getTriageReference(), getOpportunities({ sort: "deadline_date", order: "asc" })])
      .then(([r, list]) => {
        setRef(r);
        setOpps(list.results || []);
        // Honour a handoff from Search, if one is waiting.
        const handoff = sessionStorage.getItem(HANDOFF_KEY);
        if (handoff) {
          sessionStorage.removeItem(HANDOFF_KEY);
          setOppId(handoff);
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  // Load the qualification whenever the selected opportunity changes.
  useEffect(() => {
    if (!oppId) { setView(null); setForm(null); return; }
    setLoading(true);
    setError(null);
    setSavedNote(null);
    setAiMeta(null);
    getQualification(oppId)
      .then((p) => { setView(p); setForm(p.qualification); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [oppId]);

  const setField = (k) => (e) =>
    setForm((f) => ({ ...f, [k]: e.target && e.target.value !== undefined ? e.target.value : e }));

  const setRag = (key, score) =>
    setForm((f) => ({ ...f, win_qualification_rag: { ...(f.win_qualification_rag || {}), [key]: score } }));

  const setRole = (i, k, val) =>
    setForm((f) => {
      const dt = [...(f.delivery_team || [])];
      dt[i] = { ...dt[i], [k]: val };
      return { ...f, delivery_team: dt };
    });

  // Live economics off the chosen complexity (no round-trip — server persists on save).
  const econ = useMemo(() => {
    const c = form?.complexity;
    return (ref?.economics_by_complexity?.[c]) || { effort_days: 0, cost: 0, breakdown: [] };
  }, [form?.complexity, ref]);

  const rag = ragSummary(form?.win_qualification_rag);

  const persist = async (overrides = {}) => {
    if (!oppId || !form) return;
    setSaving(true);
    setError(null);
    setSavedNote(null);
    try {
      const payload = { ...form, ...overrides };
      const p = await saveQualification(oppId, payload);
      setView(p);
      setForm(p.qualification);
      setSavedNote(
        p.bid
          ? `Saved — bid created (“${p.bid.bid_name || "untitled"}”, stage ${p.bid.stage}).`
          : "Saved."
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const decide = (decision) => persist({ decision });

  // AI pre-fill: draft from the notice, merge non-empty fields into the form for
  // review. Nothing is saved — the user still edits and makes the call.
  const runAiDraft = async () => {
    if (!oppId || !form) return;
    setDrafting(true);
    setError(null);
    setAiMeta(null);
    try {
      const { draft, meta } = await aiDraftQualification(oppId);
      setForm((f) => {
        const merged = { ...f };
        for (const [k, v] of Object.entries(draft)) {
          if (v === null || v === undefined || v === "") continue;
          merged[k] = v;
        }
        return merged;
      });
      setAiMeta(meta);
    } catch (e) {
      setError(e.message);
    } finally {
      setDrafting(false);
    }
  };

  return (
    <div className="triage">
      <div className="triage-pick">
        <label>
          Opportunity to triage
          <select value={oppId} onChange={(e) => setOppId(e.target.value)}>
            <option value="">Select an opportunity…</option>
            {opps.map((o) => (
              <option key={o.id} value={o.id}>
                {o.title} — {o.buyer_name || "Unknown buyer"}
              </option>
            ))}
          </select>
        </label>
        {view?.bid && <span className="pill p-pass" title={`stage ${view.bid.stage}`}>● Bid live</span>}
        {view && !view.saved && <span className="triage-hint">Not triaged yet — seeded from the notice.</span>}
        {form && (
          <button className="ai-btn" onClick={runAiDraft} disabled={drafting}
                  title="Draft the whole qualification from the notice — you review & edit before saving">
            {drafting ? "✦ Drafting…" : "✦ AI draft"}
          </button>
        )}
      </div>

      {error && <p className="error">⚠ {error}</p>}
      {loading && <p className="empty">Loading qualification…</p>}

      {aiMeta && (
        <div className="ai-banner">
          <div className="ai-banner-head">
            <b>✦ AI-drafted from the notice — review every field before saving.</b>
            {aiMeta.suggested_decision && (
              <span className="ai-suggest">Suggested: <b>{aiMeta.suggested_decision}</b></span>
            )}
            <span className="ai-model">{aiMeta.provider}{aiMeta.model ? ` · ${aiMeta.model}` : ""}</span>
          </div>
          {aiMeta.decision_rationale && <p><b>Why:</b> {aiMeta.decision_rationale}</p>}
          {aiMeta.complexity_rationale && <p><b>Complexity:</b> {aiMeta.complexity_rationale}</p>}
          {aiMeta.gate_notes && <p><b>Gates:</b> {aiMeta.gate_notes}</p>}
        </div>
      )}

      {form && ref && (
        <div className="triage-form">
          {/* Qualification details */}
          <section className="tsec">
            <div className="label">Qualification</div>
            <div className="fgrid">
              {DETAIL_FIELDS.map(([k, lbl]) => (
                <label key={k} className="fld">
                  {lbl}
                  <input value={form[k] ?? ""} onChange={setField(k)} />
                </label>
              ))}
              <label className="fld">
                Pricing model
                <select value={form.pricing_model ?? ""} onChange={setField("pricing_model")}>
                  <option value="">—</option>
                  {ref.pricing_models.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </label>
            </div>
            <div className="fgrid areas">
              {AREA_FIELDS.map(([k, lbl]) => (
                <label key={k} className="fld">
                  {lbl}
                  <textarea rows={2} value={form[k] ?? ""} onChange={setField(k)} />
                </label>
              ))}
            </div>
          </section>

          {/* Response dates — clarification deadline called out (the founding failure) */}
          <section className="tsec">
            <div className="label">Response dates</div>
            <div className="fgrid">
              {DATE_FIELDS.map(([k, lbl]) => (
                <label key={k} className={`fld${k === "clarification_deadline" ? " fld-warn" : ""}`}>
                  {lbl}{k === "clarification_deadline" && " ⚑"}
                  <input value={form[k] ?? ""} onChange={setField(k)} placeholder="e.g. 2026-08-14" />
                </label>
              ))}
            </div>
          </section>

          {/* Delivery team — FOR001 fixed role set */}
          <section className="tsec">
            <div className="label">Delivery team required</div>
            <div className="team">
              {(form.delivery_team || []).map((row, i) => (
                <div className="team-row" key={row.role || i}>
                  <span className="team-role">{row.role}</span>
                  <input
                    className="team-count" type="number" min="0"
                    value={row.count ?? 0}
                    onChange={(e) => setRole(i, "count", Number(e.target.value))}
                  />
                  <input
                    className="team-comment" placeholder="comments"
                    value={row.comments ?? ""}
                    onChange={(e) => setRole(i, "comments", e.target.value)}
                  />
                </div>
              ))}
            </div>
          </section>

          {/* Complexity → bid economics (FWF's real cost-to-chase rig) */}
          <section className="tsec">
            <div className="label">Complexity → bid economics</div>
            <div className="seg complexity-seg">
              {ref.complexity_levels.map((c) => (
                <button
                  key={c}
                  className={form.complexity === c ? "on" : ""}
                  onClick={() => setForm((f) => ({ ...f, complexity: c }))}
                >
                  {c}
                </button>
              ))}
            </div>
            <div className="econ">
              <div className="stat">
                <div className="k">Est. bid effort</div>
                <div className="v">{econ.effort_days || "—"}</div>
                <div className="u">person-days to chase</div>
              </div>
              <div className="stat">
                <div className="k">Est. bid cost</div>
                <div className="v">{fmtMoney(econ.cost)}</div>
                <div className="u">@ £{ref.day_rate}/day</div>
              </div>
              <div className="stat">
                <div className="k">Contract value</div>
                <div className="v">{fmtMoney(form.estimated_value)}</div>
                <div className="u">customer budget</div>
              </div>
            </div>
            {econ.breakdown?.length > 0 && (
              <div className="econ-break">
                {econ.breakdown.map((b) => (
                  <span key={b.role}>{b.role}: {b.days}d</span>
                ))}
              </div>
            )}
          </section>

          {/* Win-qualification RAG — score each 1/2/3 (red/amber/green) */}
          <section className="tsec">
            <div className="label">
              Win qualification — 3 green · 2 amber · 1 red
              {rag.rating && (
                <span className={`pill ${RAG_PILL[rag.rating]} rag-sum`}>
                  {rag.label} risk ({rag.rating})
                </span>
              )}
            </div>
            <div className="gates">
              {ref.rag_criteria.map((c) => {
                const score = form.win_qualification_rag?.[c.key];
                return (
                  <div className="gate" key={c.key}>
                    <div className="g-txt">
                      <b>{c.label}</b>
                      {c.hint && <span className="g-note"> — {c.hint}</span>}
                    </div>
                    <div className="rag-set">
                      {[1, 2, 3].map((s) => (
                        <button
                          key={s}
                          className={`rag-btn ${RAG_PILL[s]}${score === s ? " on" : ""}`}
                          onClick={() => setRag(c.key, s)}
                          aria-label={`score ${s}`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Strategy & risks */}
          <section className="tsec">
            <div className="fgrid areas">
              <label className="fld">
                Winning strategy — how can we win?
                <textarea rows={2} value={form.winning_strategy ?? ""} onChange={setField("winning_strategy")} />
              </label>
              <label className="fld">
                Delivery risks & mitigations
                <textarea rows={2} value={form.delivery_risks ?? ""} onChange={setField("delivery_risks")} />
              </label>
            </div>
          </section>

          {/* Decision */}
          <section className="tsec">
            <div className="label">Bid decision {form.decision && <span className="pill p-pass">{form.decision}</span>}</div>
            <div className="fgrid areas">
              <label className="fld">
                Qualify-out reason (if No go)
                <textarea rows={2} value={form.qualify_out_reason ?? ""} onChange={setField("qualify_out_reason")} />
              </label>
              <label className="fld">
                Caveats
                <textarea rows={2} value={form.caveats ?? ""} onChange={setField("caveats")} />
              </label>
            </div>
            <div className="decide">
              <button className="mini-btn" disabled={saving} onClick={() => decide("Go")}>▲ Recommend BID</button>
              <button className="mini-btn ghost" disabled={saving} onClick={() => decide("No go")}>No-bid</button>
              <button className="mini-btn tonal" disabled={saving} onClick={() => decide("")}>Needs review</button>
              <button className="mini-btn tonal" disabled={saving} onClick={() => persist()}>Save draft</button>
              {saving && <span className="triage-hint">Saving…</span>}
              {savedNote && <span className="triage-hint ok">{savedNote}</span>}
            </div>
          </section>
        </div>
      )}

      {!oppId && !loading && (
        <p className="empty">Pick an opportunity above to run the bid/no-bid qualification.</p>
      )}
    </div>
  );
}
