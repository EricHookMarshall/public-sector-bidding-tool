// Stage 03 — Plan. The pipeline board + team capacity, wired to real data. This
// is FWF's FOR002 BidPlan as a live view: every bid that came through a Triage
// "Go" lands on the board; its pipeline column, owner, deadlines and "cost to
// chase" are read from bids.db, the capacity bar sums committed bid-effort
// against the team's days, and the alerts fire on the real deadlines — including
// the clarification deadline whose loss is the failure this whole tool exists to
// prevent. Click a bid to open its FOR002 phase timeline. No mock data.
import { useEffect, useMemo, useState } from "react";
import { getPlanReference, getPlanBoard, getBidPlan, saveBidPlan } from "../api.js";

// Trim float noise (19.5 stays 19.5, 5.0 → 5) for the capacity readout.
const round1 = (n) => Math.round(Number(n) * 10) / 10;

function fmtMoney(n, currency = "GBP") {
  if (n === null || n === undefined || n === "" || Number.isNaN(Number(n))) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency", currency, maximumFractionDigits: 0,
  }).format(Number(n));
}

// A days-to-deadline count → short label + urgency class (drives colour).
function deadlineBadge(days, imminent) {
  if (days === null || days === undefined) return null;
  if (days < 0) return { label: `${Math.abs(days)}d late`, cls: "crit" };
  if (days <= imminent) return { label: `${days}d left`, cls: "crit" };
  if (days <= imminent * 2) return { label: `${days}d`, cls: "warn" };
  return { label: `${days}d`, cls: "ok" };
}

// Card top-border colour: red if a deadline is imminent/passed, green if it's
// owned and in flight, neutral-blue otherwise (still needs attention).
function cardTone(card, imminent) {
  const d = card.days_to_submission;
  const c = card.days_to_clarification;
  if ((d !== null && d <= imminent) || (c !== null && c <= imminent)) return "risk";
  return card.owner ? "go" : "draft";
}

export default function PlanStage() {
  const [ref, setRef] = useState(null);
  const [board, setBoard] = useState(null);
  const [capacityDays, setCapacityDays] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBid, setSelectedBid] = useState(null);   // null → board view

  const imminent = ref?.imminent_days ?? 7;

  // Load the FOR002 vocabulary once; seed the capacity input from its default.
  useEffect(() => {
    getPlanReference()
      .then((r) => { setRef(r); setCapacityDays(r.default_capacity_days); })
      .catch((e) => setError(e.message));
  }, []);

  const loadBoard = (cap) => {
    setLoading(true);
    setError(null);
    return getPlanBoard(cap)
      .then(setBoard)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  // (Re)load the board whenever capacity changes — but only while on the board
  // view (not while a bid detail is open).
  useEffect(() => {
    if (capacityDays === null || selectedBid) return;
    loadBoard(capacityDays);
  }, [capacityDays, selectedBid]);

  if (selectedBid) {
    return (
      <PlanDetail
        bidId={selectedBid}
        ref_={ref}
        imminent={imminent}
        onBack={() => setSelectedBid(null)}
      />
    );
  }

  return (
    <div className="plan">
      {error && <p className="error">⚠ {error}</p>}
      {loading && !board && <p className="empty">Loading pipeline…</p>}

      {board && board.count === 0 && (
        <p className="empty">
          No bids on the board yet. A <b>Go</b> decision in Triage promotes an
          opportunity into a bid, and it appears here to be planned.
        </p>
      )}

      {board && board.count > 0 && (
        <>
          {/* Real alerts — the clarification/deadline warnings, most-urgent first */}
          {board.alerts.length > 0 && (
            <div className="alert-list">
              {board.alerts.map((a, i) => (
                <div key={i} className={`alert-strip${a.level === "warn" ? " warn" : ""}`}>
                  ⚠ {a.text}
                </div>
              ))}
            </div>
          )}

          {/* Pipeline board — columns from the FOR002 pipeline stages */}
          <div className="board plan-board">
            {board.columns.map((col) => (
              <div className="col" key={col.stage}>
                <div className="col-h"><span>{col.stage}</span><span className="c">{col.cards.length}</span></div>
                {col.cards.map((card) => (
                  <BidCard key={card.bid_id} card={card} imminent={imminent}
                           onOpen={() => setSelectedBid(card.bid_id)} />
                ))}
              </div>
            ))}
          </div>

          {/* Team capacity — committed bid-effort vs the team's days */}
          <CapacityBar cap={board.capacity} capacityDays={capacityDays}
                       onCapacity={setCapacityDays} />
        </>
      )}
    </div>
  );
}

function BidCard({ card, imminent, onOpen }) {
  const tone = cardTone(card, imminent);
  const sub = deadlineBadge(card.days_to_submission, imminent);
  const clar = deadlineBadge(card.days_to_clarification, imminent);
  return (
    <button className={`kcard t-${tone} plan-card`} onClick={onOpen} title="Open the FOR002 plan">
      <div className="kt">{card.title}</div>
      {card.buyer_name && <div className="km-sub">{card.buyer_name}</div>}
      <div className="km">
        {card.owner
          ? <span className="who">{card.owner}</span>
          : <span className="who none" title="No owner assigned">?</span>}
        {card.value != null && <span className="tag val">{fmtMoney(card.value, card.currency)}</span>}
        {card.effort_days > 0 && <span className="tag">{card.effort_days}d chase</span>}
      </div>
      <div className="km plan-deadlines">
        {sub && <span className={`dl dl-${sub.cls}`}>▸ {sub.label}</span>}
        {clar && <span className={`dl dl-${clar.cls}`} title="Clarification deadline">⚑ {clar.label}</span>}
      </div>
    </button>
  );
}

function CapacityBar({ cap, capacityDays, onCapacity }) {
  return (
    <div className={`cap${cap.over ? " is-over" : ""}`}>
      <div className="col-h" style={{ margin: 0 }}>
        <span>Team capacity — committed vs available</span>
        <span className="c">{cap.committed_days} / {cap.capacity_days} days</span>
      </div>
      <div className={`bar${cap.over ? " over" : ""}`}><i style={{ width: `${cap.pct}%` }} /></div>
      <div className="cap-foot">
        {cap.over ? (
          <span className="cap-warn">
            Over-committed by {round1(cap.committed_days - cap.capacity_days)} days — something has to give:
            drop a bid, or add capacity.
          </span>
        ) : (
          <span>{round1(cap.remaining_days)} days spare across live bids.</span>
        )}
        <label className="cap-input">
          Capacity
          <input type="number" min="1" value={capacityDays ?? ""}
                 onChange={(e) => onCapacity(Number(e.target.value) || 1)} />
          days
        </label>
      </div>
    </div>
  );
}

// ---- Per-bid FOR002 plan detail (pipeline position + phase timeline) --------

function PlanDetail({ bidId, ref_, imminent, onBack }) {
  const [payload, setPayload] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNote, setSavedNote] = useState(null);

  useEffect(() => {
    setLoading(true);
    getBidPlan(bidId)
      .then((p) => { setPayload(p); setForm(p.plan); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [bidId]);

  const setField = (k) => (e) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const setPhase = (i, k, val) =>
    setForm((f) => {
      const phases = [...(f.phases || [])];
      phases[i] = { ...phases[i], [k]: val };
      return { ...f, phases };
    });

  const save = async () => {
    setSaving(true);
    setError(null);
    setSavedNote(null);
    try {
      const p = await saveBidPlan(bidId, form);
      setPayload(p);
      setForm(p.plan);
      setSavedNote("Saved.");
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="empty">Loading plan…</p>;
  if (error && !payload) return <p className="error">⚠ {error}</p>;
  if (!payload || !form || !ref_) return null;

  const opp = payload.opportunity;
  const econ = payload.economics;
  const subBadge = deadlineBadge(daysUntil(opp.submission_deadline), imminent);
  const clarBadge = deadlineBadge(daysUntil(opp.clarification_deadline), imminent);

  return (
    <div className="plan-detail">
      <div className="pd-head">
        <button className="mini-btn ghost" onClick={onBack}>← Board</button>
        <h3>{opp.title}</h3>
        {payload.bid?.status && <span className="pill p-pass">{payload.bid.status}</span>}
      </div>

      {/* At-a-glance: the numbers Planning weighs, and the two deadlines */}
      <div className="pd-facts">
        <div className="stat"><div className="k">Buyer</div><div className="v sm">{opp.buyer_name || "—"}</div></div>
        <div className="stat"><div className="k">Contract value</div><div className="v sm">{fmtMoney(opp.value, opp.currency)}</div></div>
        <div className="stat"><div className="k">Cost to chase</div><div className="v sm">{fmtMoney(econ.cost)}</div><div className="u">{econ.effort_days}d · {econ.complexity || "—"}</div></div>
        <div className="stat">
          <div className="k">Submission</div>
          <div className="v sm">{opp.submission_deadline || "—"}</div>
          {subBadge && <div className={`u dl-${subBadge.cls}`}>{subBadge.label}</div>}
        </div>
        <div className={`stat${clarBadge ? " stat-warn" : ""}`}>
          <div className="k">⚑ Clarification</div>
          <div className="v sm">{opp.clarification_deadline || "—"}</div>
          {clarBadge && <div className={`u dl-${clarBadge.cls}`}>{clarBadge.label}</div>}
        </div>
      </div>

      {/* Pipeline position */}
      <section className="tsec">
        <div className="label">Pipeline position</div>
        <div className="fgrid">
          <label className="fld">
            Stage
            <select value={form.pipeline_stage ?? ""} onChange={setField("pipeline_stage")}>
              {ref_.pipeline_stages.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="fld">
            Owner
            <input list="owner-roles" value={form.owner ?? ""} onChange={setField("owner")}
                   placeholder="person or role" />
            <datalist id="owner-roles">
              {ref_.owner_roles.map((r) => <option key={r} value={r} />)}
            </datalist>
          </label>
          <label className="fld">
            Bid work starts
            <input value={form.start_date ?? ""} onChange={setField("start_date")} placeholder="e.g. 2026-07-20" />
          </label>
          <label className="fld">
            Internal target submission
            <input value={form.target_submission ?? ""} onChange={setField("target_submission")}
                   placeholder="e.g. 2026-08-10" />
          </label>
        </div>
      </section>

      {/* FOR002 phase timeline */}
      <section className="tsec">
        <div className="label">FOR002 bid plan — phase timeline</div>
        <div className="timeline">
          <div className="tl-row tl-head">
            <span>Phase</span><span>Owner</span><span>Start</span><span>Complete</span><span>Status</span><span>Comments</span>
          </div>
          {(form.phases || []).map((ph, i) => (
            <div className={`tl-row st-${(ph.status || "").replace(/\s+/g, "-").toLowerCase()}`} key={ph.phase || i}>
              <span className="tl-phase">{ph.phase}</span>
              <input list="owner-roles" value={ph.owner ?? ""} onChange={(e) => setPhase(i, "owner", e.target.value)} placeholder="—" />
              <input value={ph.start_date ?? ""} onChange={(e) => setPhase(i, "start_date", e.target.value)} placeholder="—" />
              <input value={ph.completion_date ?? ""} onChange={(e) => setPhase(i, "completion_date", e.target.value)} placeholder="—" />
              <select value={ph.status ?? "Not started"} onChange={(e) => setPhase(i, "status", e.target.value)}>
                {ref_.phase_statuses.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <input value={ph.comments ?? ""} onChange={(e) => setPhase(i, "comments", e.target.value)} placeholder="—" />
            </div>
          ))}
        </div>
      </section>

      <section className="tsec">
        <div className="fgrid areas">
          <label className="fld">
            Notes
            <textarea rows={2} value={form.notes ?? ""} onChange={setField("notes")} />
          </label>
        </div>
        <div className="decide">
          <button className="mini-btn" disabled={saving} onClick={save}>Save plan</button>
          {saving && <span className="triage-hint">Saving…</span>}
          {savedNote && <span className="triage-hint ok">{savedNote}</span>}
          {error && <span className="error">⚠ {error}</span>}
        </div>
      </section>
    </div>
  );
}

// Local mirror of bidplan.days_until for the detail badges (the board sends
// pre-computed days; the detail reads raw opportunity dates).
function daysUntil(value) {
  if (!value) return null;
  const d = new Date(String(value).slice(0, 10));
  if (Number.isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((d - today) / 86400000);
}
