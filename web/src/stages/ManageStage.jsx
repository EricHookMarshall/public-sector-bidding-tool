// Stage 05 — Manage. The FOR003 clarification register + pre-flight gate, wired
// to real data. This is the stage the whole tool exists for: a missed
// clarification is the admin failure that lost the G-Cloud 15 bid. Every live bid
// shows its open clarifications, the nearest buyer deadline (captured with time +
// timezone), and whether its pre-flight gate is clear. Click a bid to work its
// register and gate. The gate blocks "submitted" until every mandatory item
// passes — nothing auto-submits; the buyer's portal submission stays a human act.
import { useEffect, useState } from "react";
import {
  getManageReference, getManageBoard, getBidManage, saveBidManage,
} from "../api.js";

// A days-to-deadline count → short label + urgency class (drives colour).
// Mirrors PlanStage's badge so Plan and Manage read the same.
function deadlineBadge(days, imminent) {
  if (days === null || days === undefined) return null;
  if (days < 0) return { label: `${Math.abs(days)}d late`, cls: "crit" };
  if (days <= imminent) return { label: `${days}d left`, cls: "crit" };
  if (days <= imminent * 2) return { label: `${days}d`, cls: "warn" };
  return { label: `${days}d`, cls: "ok" };
}

// Local mirror of bidplan.days_until for the detail badges (the board sends
// pre-computed days; the detail reads raw dates from the register form).
function daysUntil(value) {
  if (!value) return null;
  const d = new Date(String(value).slice(0, 10));
  if (Number.isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((d - today) / 86400000);
}

// A blank FOR003 register row — matches clarification.default_clarification.
const blankClarification = () => ({
  question_number: "", question: "", channel: "",
  owner: "", backup_owner: "",
  buyer_deadline: "", deadline_note: "",
  date_submitted: "", response_date: "", buyer_response: "",
  status: "Open", notes: "",
});

export default function ManageStage() {
  const [ref, setRef] = useState(null);
  const [board, setBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBid, setSelectedBid] = useState(null);   // null → board view

  const imminent = ref?.imminent_days ?? 7;

  useEffect(() => {
    getManageReference().then(setRef).catch((e) => setError(e.message));
  }, []);

  const loadBoard = () => {
    setLoading(true);
    setError(null);
    return getManageBoard()
      .then(setBoard)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  // (Re)load the board whenever we return to it (not while a detail is open).
  useEffect(() => {
    if (selectedBid) return;
    loadBoard();
  }, [selectedBid]);

  if (selectedBid) {
    return (
      <ManageDetail
        bidId={selectedBid}
        ref_={ref}
        imminent={imminent}
        onBack={() => setSelectedBid(null)}
      />
    );
  }

  return (
    <div className="manage">
      {error && <p className="error">⚠ {error}</p>}
      {loading && !board && <p className="empty">Loading register…</p>}

      {board && board.count === 0 && (
        <p className="empty">
          No live bids to manage yet. A <b>Go</b> in Triage promotes an
          opportunity into a bid; once it's here you can log buyer clarifications
          and run the pre-flight gate before submitting.
        </p>
      )}

      {board && board.count > 0 && (
        <>
          {/* Real alerts — the clarification-deadline / gate warnings. This is
              the founding-failure signal: a missed clarification is fatal. */}
          {board.alerts.length > 0 ? (
            <div className="alert-list">
              {board.alerts.map((a, i) => (
                <div key={i} className={`alert-strip${a.level === "warn" ? " warn" : ""}`}>
                  ⚠ {a.text}
                </div>
              ))}
            </div>
          ) : (
            <div className="alert-strip ok-strip">✓ No clarification or gate warnings across live bids.</div>
          )}

          <div className="label">Live bids — clarifications & submission gate</div>
          <div className="manage-grid">
            {board.bids.map((b) => (
              <ManageCard key={b.bid_id} b={b} imminent={imminent}
                          onOpen={() => setSelectedBid(b.bid_id)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function ManageCard({ b, imminent, onOpen }) {
  const clar = deadlineBadge(b.days_to_next_clarification, imminent);
  const sub = deadlineBadge(b.days_to_submission, imminent);
  const ready = b.preflight?.ready;
  const tone = b.submitted ? "go"
    : (b.days_to_next_clarification !== null && b.days_to_next_clarification <= imminent)
      || (b.days_to_submission !== null && b.days_to_submission <= imminent && !ready)
      ? "risk" : "draft";
  return (
    <button className={`kcard t-${tone} manage-card`} onClick={onOpen} title="Open the FOR003 register + pre-flight gate">
      <div className="kt">{b.title}</div>
      <div className="km manage-clar">
        {b.clarifications_open > 0
          ? <span className="tag warn-tag">⚑ {b.clarifications_open} open clarification{b.clarifications_open > 1 ? "s" : ""}</span>
          : <span className="tag">no open clarifications</span>}
        {clar && <span className={`dl dl-${clar.cls}`} title="Nearest clarification deadline">{clar.label}</span>}
      </div>
      <div className="km manage-foot">
        {sub && <span className={`dl dl-${sub.cls}`} title="Submission deadline">▸ closes {sub.label}</span>}
        {b.submitted
          ? <span className="st-pill p-pass">Submitted</span>
          : ready
            ? <span className="st-pill p-pass">Gate clear</span>
            : <span className="st-pill p-fail">Gate: {b.preflight?.blocking_count ?? "—"} to go</span>}
      </div>
    </button>
  );
}

// ---- Per-bid FOR003 register + pre-flight gate detail ----------------------

function ManageDetail({ bidId, ref_, imminent, onBack }) {
  const [payload, setPayload] = useState(null);
  const [clars, setClars] = useState([]);
  const [preflight, setPreflight] = useState([]);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNote, setSavedNote] = useState(null);

  const hydrate = (p) => {
    setPayload(p);
    setClars(p.clarifications || []);
    setPreflight(p.preflight || []);
    setNotes(p.notes || "");
  };

  useEffect(() => {
    setLoading(true);
    getBidManage(bidId)
      .then(hydrate)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [bidId]);

  const setClar = (i, k, val) =>
    setClars((cs) => cs.map((c, j) => (j === i ? { ...c, [k]: val } : c)));
  const addClar = () => setClars((cs) => [...cs, blankClarification()]);
  const removeClar = (i) => setClars((cs) => cs.filter((_, j) => j !== i));

  const setCheck = (key, k, val) =>
    setPreflight((ps) => ps.map((p) => (p.key === key ? { ...p, [k]: val } : p)));

  const save = async (extra = {}) => {
    setSaving(true);
    setError(null);
    setSavedNote(null);
    try {
      const p = await saveBidManage(bidId, {
        clarifications: clars,
        preflight: preflight.map((c) => ({
          key: c.key, status: c.status, note: c.note, expiry_date: c.expiry_date,
        })),
        notes,
        ...extra,
      });
      hydrate(p);
      setSavedNote(extra.submitted === "yes" ? "Submitted — gate cleared." : "Saved.");
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="empty">Loading register…</p>;
  if (error && !payload) return <p className="error">⚠ {error}</p>;
  if (!payload || !ref_) return null;

  const opp = payload.opportunity;
  const gate = payload.preflight_summary;
  const subBadge = deadlineBadge(daysUntil(opp.submission_deadline), imminent);
  const clarRefBadge = deadlineBadge(daysUntil(opp.clarification_deadline), imminent);

  return (
    <div className="plan-detail manage-detail">
      <div className="pd-head">
        <button className="mini-btn ghost" onClick={onBack}>← Board</button>
        <h3>{opp.title}</h3>
        {payload.submitted && <span className="pill p-pass">Submitted</span>}
      </div>

      {/* At-a-glance: the two deadlines that matter, kept distinct on purpose */}
      <div className="pd-facts">
        <div className="stat"><div className="k">Buyer</div><div className="v sm">{opp.buyer_name || "—"}</div></div>
        <div className="stat">
          <div className="k">Submission</div>
          <div className="v sm">{opp.submission_deadline || "—"}</div>
          {subBadge && <div className={`u dl-${subBadge.cls}`}>{subBadge.label}</div>}
        </div>
        <div className={`stat${clarRefBadge ? " stat-warn" : ""}`}>
          <div className="k">⚑ Clarification cut-off</div>
          <div className="v sm">{opp.clarification_deadline || "—"}</div>
          {clarRefBadge && <div className={`u dl-${clarRefBadge.cls}`}>{clarRefBadge.label}</div>}
        </div>
        <div className={`stat${gate.ready ? "" : " stat-warn"}`}>
          <div className="k">Pre-flight gate</div>
          <div className="v sm">{gate.ready ? "Clear ✓" : `${gate.blocking_count} blocking`}</div>
          <div className="u">{gate.passed}/{gate.total} passed{gate.na ? ` · ${gate.na} n/a` : ""}</div>
        </div>
      </div>

      {/* FOR003 clarification register — the step the last bid missed */}
      <section className="tsec">
        <div className="label">Clarification register (FOR003 CQLOG)</div>
        {clars.length === 0 && (
          <p className="empty sm">No clarifications logged. Add each buyer question with an owner, a
          backup, and its deadline — <b>with time and timezone</b>. That captured detail is what was
          lost on G-Cloud 15.</p>
        )}
        {clars.map((c, i) => {
          const badge = deadlineBadge(daysUntil(c.buyer_deadline), imminent);
          const resolved = ref_.resolved_statuses.includes(c.status);
          return (
            <div className={`clar-row${resolved ? " is-resolved" : ""}`} key={i}>
              <div className="clar-main">
                <input className="clar-q" value={c.question} placeholder="Buyer clarification / question"
                       onChange={(e) => setClar(i, "question", e.target.value)} />
                <div className="clar-meta">
                  <input value={c.question_number} placeholder="Ref (CQ01)"
                         onChange={(e) => setClar(i, "question_number", e.target.value)} />
                  <input value={c.channel} placeholder="via portal / email"
                         onChange={(e) => setClar(i, "channel", e.target.value)} />
                  <select value={c.status} onChange={(e) => setClar(i, "status", e.target.value)}>
                    {ref_.clarification_statuses.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <button className="clar-del" title="Remove" onClick={() => removeClar(i)}>✕</button>
                </div>
              </div>
              <div className="clar-owners">
                <label className="mini-fld">Owner
                  <input value={c.owner} placeholder="who owns it"
                         onChange={(e) => setClar(i, "owner", e.target.value)} />
                </label>
                <label className="mini-fld">Backup
                  <input value={c.backup_owner} placeholder="cover"
                         onChange={(e) => setClar(i, "backup_owner", e.target.value)} />
                </label>
                <label className="mini-fld">Buyer deadline
                  <input value={c.buyer_deadline} placeholder="2026-08-14"
                         onChange={(e) => setClar(i, "buyer_deadline", e.target.value)} />
                </label>
                <label className="mini-fld">Time + timezone
                  <input value={c.deadline_note} placeholder="17:00 BST"
                         onChange={(e) => setClar(i, "deadline_note", e.target.value)} />
                </label>
                {badge && !resolved && <span className={`dl dl-${badge.cls} clar-badge`}>{badge.label}</span>}
              </div>
            </div>
          );
        })}
        <button className="mini-btn tonal add-clar" onClick={addClar}>+ Add clarification</button>
      </section>

      {/* Pre-flight submission gate. Auto/expiry items are enforced server-side —
          the checklist can't be talked past. */}
      <section className="tsec">
        <div className="label">Pre-flight — submission gate</div>
        <div className="checklist">
          {preflight.map((c) => {
            const eff = c.status || "";                 // effective status from the server
            const cls = eff === "pass" ? "ok" : eff === "na" ? "na" : "no";
            return (
              <div className={`ck ${cls} preflight-ck`} key={c.key}>
                <span className="box">{eff === "pass" ? "✓" : eff === "na" ? "–" : "!"}</span>
                <span className="ck-label">
                  {c.label}
                  {c.reason && <span className="sub"> — {c.reason}</span>}
                  {c.category && <span className="ck-cat">{c.category}</span>}
                </span>
                {c.expiry && (
                  <input className="ck-expiry" value={c.expiry_date || ""} placeholder="expiry YYYY-MM-DD"
                         onChange={(e) => setCheck(c.key, "expiry_date", e.target.value)} />
                )}
                <select className="ck-status" value={c.status || ""}
                        disabled={c.auto}
                        title={c.auto ? "Derived from the register — resolve the clarifications" : ""}
                        onChange={(e) => setCheck(c.key, "status", e.target.value)}>
                  <option value="">pending</option>
                  <option value="pass">pass</option>
                  <option value="fail">fail</option>
                  <option value="na">n/a</option>
                </select>
              </div>
            );
          })}
        </div>
        <p className="triage-hint">The gate re-checks on save — auto and expiry items are enforced, not ticked.</p>
      </section>

      <section className="tsec">
        <div className="fgrid areas">
          <label className="fld">
            Notes
            <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </label>
        </div>
        <div className="decide manage-actions">
          <button className="mini-btn" disabled={saving} onClick={() => save()}>Save register</button>
          <button className="mini-btn submit-btn"
                  disabled={saving || !gate.ready || payload.submitted}
                  title={gate.ready ? "Mark the bid submitted" : "Clear the pre-flight gate first"}
                  onClick={() => save({ submitted: "yes" })}>
            {payload.submitted ? "Submitted ✓" : "Mark submitted"}
          </button>
          {!gate.ready && !payload.submitted &&
            <span className="triage-hint">Gate blocks submission: {gate.blocking_count} item(s) outstanding.</span>}
          {saving && <span className="triage-hint">Saving…</span>}
          {savedNote && <span className="triage-hint ok">{savedNote}</span>}
          {error && <span className="error">⚠ {error}</span>}
        </div>
      </section>
    </div>
  );
}
