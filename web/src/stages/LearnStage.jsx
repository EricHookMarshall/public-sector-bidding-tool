// Stage 06 — Learn. The B07 outcome capture + Lessons Learned + library-feedback
// loop, wired to real data. This is the stage that closes the journey: what a bid
// actually did (won/lost, score, evaluator feedback) becomes concrete suggestions
// to promote / refresh / retire content in the Stage-4 library, so the next bid
// drafts from better material. The win-rate is tracked bid-by-bid — the metric
// the framework doc explicitly asks for. Click a bid to record its outcome.
//
// Honest boundary: the suggested library updates are derived and captured for a
// human to approve, but WRITING them into the real reusable library needs the
// SharePoint/MS-Graph connection Stage 4 is blocked on — so nothing here mutates
// the library; it proposes and records the sign-off.
import { useEffect, useState } from "react";
import {
  getLearnReference, getLearnBoard, getBidOutcome, saveBidOutcome,
} from "../api.js";

// result → kcard tone class (from outcome.RESULT_TONE). "neutral" keeps the base.
const TONE_CLASS = { go: "t-go", risk: "t-risk", draft: "t-draft", neutral: "" };

// result → the pill that reads its meaning at a glance.
function resultPill(result) {
  if (result === "Won") return "p-pass";
  if (result === "Not Won") return "p-fail";
  if (result === "Withdrawn") return "p-unk";
  return "p-wait"; // Awaiting
}

// A library-suggestion action → the glyph the mockup used (promote/refresh/retire).
const ACTION_GLYPH = { promote: "▲", refresh: "↻", retire: "▼" };
const ACTION_IC = { promote: "ic-up", refresh: "ic-ref", retire: "ic-down" };

// A blank Lessons Learned row — matches outcome.default_lesson.
const blankLesson = () => ({ category: "", note: "", action: "" });

export default function LearnStage() {
  const [ref, setRef] = useState(null);
  const [board, setBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBid, setSelectedBid] = useState(null);   // null → board view

  useEffect(() => {
    getLearnReference().then(setRef).catch((e) => setError(e.message));
  }, []);

  const loadBoard = () => {
    setLoading(true);
    setError(null);
    return getLearnBoard()
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
      <LearnDetail
        bidId={selectedBid}
        ref_={ref}
        onBack={() => setSelectedBid(null)}
      />
    );
  }

  return (
    <div className="learn">
      {error && <p className="error">⚠ {error}</p>}
      {loading && !board && <p className="empty">Loading outcomes…</p>}

      {board && board.count === 0 && (
        <p className="empty">
          No bids to learn from yet. A <b>Go</b> in Triage promotes an opportunity
          into a bid; once it's been through Manage you can record its outcome here
          and feed the lessons back into the library.
        </p>
      )}

      {board && board.count > 0 && (
        <>
          <WinRate wr={board.winrate} />

          {/* Loop-closing nudges — submitted-but-unrecorded / unapproved suggestions */}
          {board.alerts.length > 0 ? (
            <div className="alert-list">
              {board.alerts.map((a, i) => (
                <div key={i} className={`alert-strip${a.level === "warn" ? " warn" : ""}`}>
                  ⚠ {a.text}
                </div>
              ))}
            </div>
          ) : (
            <div className="alert-strip ok-strip">✓ Every submitted bid has an outcome recorded.</div>
          )}

          <div className="label">Bids — outcomes & library feedback</div>
          <div className="manage-grid">
            {board.bids.map((b) => (
              <LearnCard key={b.bid_id} b={b} onOpen={() => setSelectedBid(b.bid_id)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// The win-rate readout — "target win rate, tracked bid by bid". The meter shows
// won / competitive; withdrawals are excluded from the rate (not a competitive loss).
function WinRate({ wr }) {
  const rate = wr.win_rate;
  const hasRate = rate !== null && rate !== undefined;
  return (
    <div className="cap winrate">
      <div className="pd-facts wr-facts">
        <div className="stat">
          <div className="k">Win rate</div>
          <div className="v">{hasRate ? `${rate}%` : "—"}</div>
          <div className="u">{wr.won} won / {wr.competitive} competitive</div>
        </div>
        <div className="stat">
          <div className="k">Recorded</div>
          <div className="v">{wr.recorded}</div>
          <div className="u">{wr.awaiting} awaiting an outcome</div>
        </div>
        <div className="stat">
          <div className="k">Avg score</div>
          <div className="v">{wr.avg_score !== null && wr.avg_score !== undefined ? `${wr.avg_score}%` : "—"}</div>
          <div className="u">across scored bids</div>
        </div>
        <div className="stat">
          <div className="k">Results</div>
          <div className="v sm">{wr.won}W · {wr.not_won}L · {wr.withdrawn}WD</div>
          <div className="u">won · lost · withdrawn</div>
        </div>
      </div>
      {hasRate && (
        <div className="bar" title={`${rate}% win rate`}>
          <i style={{ width: `${rate}%` }} />
        </div>
      )}
    </div>
  );
}

function LearnCard({ b, onOpen }) {
  const tone = TONE_CLASS[b.result_tone] || "";
  return (
    <button className={`kcard ${tone} manage-card`} onClick={onOpen} title="Record the outcome + library feedback">
      <div className="kt">{b.title}</div>
      <div className="km">
        <span className={`st-pill ${resultPill(b.result)}`}>{b.result}</span>
        {b.score_pct !== null && b.score_pct !== undefined &&
          <span className="dl dl-ok" title="Evaluator score">{b.score_pct}%</span>}
        {!b.saved && b.submitted &&
          <span className="tag warn-tag">⚑ outcome not recorded</span>}
      </div>
      <div className="km manage-foot">
        {b.winner && <span className="km-sub">lost to {b.winner}</span>}
        {b.suggestions_count > 0 &&
          <span className="st-pill p-pass" title="Suggested library updates">
            {b.suggestions_count} library update{b.suggestions_count > 1 ? "s" : ""}
            {b.library_approved ? " ✓" : ""}
          </span>}
      </div>
    </button>
  );
}

// ---- Per-bid B07 outcome + Lessons Learned + library feedback detail --------

function LearnDetail({ bidId, ref_, onBack }) {
  const [payload, setPayload] = useState(null);
  const [form, setForm] = useState(null);       // the editable outcome scalars
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNote, setSavedNote] = useState(null);

  const hydrate = (p) => {
    setPayload(p);
    const o = p.outcome || {};
    setForm({
      result: o.result || "Awaiting",
      score_received: o.score_received || "",
      max_score: o.max_score || "",
      winner: o.winner || "",
      award_date: o.award_date || "",
      debrief_date: o.debrief_date || "",
      feedback: o.feedback || "",
      library_approved: o.library_approved || "",
      notes: o.notes || "",
    });
    setLessons(o.lessons || []);
  };

  useEffect(() => {
    setLoading(true);
    getBidOutcome(bidId)
      .then(hydrate)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [bidId]);

  const setField = (k, val) => setForm((f) => ({ ...f, [k]: val }));
  const setLesson = (i, k, val) =>
    setLessons((ls) => ls.map((l, j) => (j === i ? { ...l, [k]: val } : l)));
  const addLesson = () => setLessons((ls) => [...ls, blankLesson()]);
  const removeLesson = (i) => setLessons((ls) => ls.filter((_, j) => j !== i));

  const save = async (extra = {}) => {
    setSaving(true);
    setError(null);
    setSavedNote(null);
    try {
      const p = await saveBidOutcome(bidId, { ...form, lessons, ...extra });
      hydrate(p);
      setSavedNote(extra.library_approved === "yes" ? "Saved — library updates approved." : "Saved.");
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="empty">Loading outcome…</p>;
  if (error && !payload) return <p className="error">⚠ {error}</p>;
  if (!payload || !ref_ || !form) return null;

  const opp = payload.opportunity;
  const suggestions = payload.suggestions || [];
  const decided = ref_.decided.includes(form.result);
  const approved = form.library_approved === "yes";

  return (
    <div className="plan-detail learn-detail">
      <div className="pd-head">
        <button className="mini-btn ghost" onClick={onBack}>← Board</button>
        <h3>{opp.title}</h3>
        <span className={`st-pill ${resultPill(form.result)}`}>{form.result}</span>
      </div>

      {/* At-a-glance: buyer, when it closed, the result and score */}
      <div className="pd-facts">
        <div className="stat"><div className="k">Buyer</div><div className="v sm">{opp.buyer_name || "—"}</div></div>
        <div className="stat">
          <div className="k">Submission closed</div>
          <div className="v sm">{opp.submission_deadline || "—"}</div>
          <div className="u">{payload.submitted ? "submitted ✓" : "not marked submitted"}</div>
        </div>
        <div className="stat">
          <div className="k">Result</div>
          <div className="v sm">{form.result}</div>
        </div>
        <div className="stat">
          <div className="k">Score</div>
          <div className="v sm">{payload.score_pct !== null && payload.score_pct !== undefined ? `${payload.score_pct}%` : "—"}</div>
          {form.winner && <div className="u">won by {form.winner}</div>}
        </div>
      </div>

      {/* Outcome — the pipeline Review sheet */}
      <section className="tsec">
        <div className="label">Outcome (pipeline Review)</div>
        <div className="fgrid">
          <label className="fld">Result
            <select value={form.result} onChange={(e) => setField("result", e.target.value)}>
              {ref_.results.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </label>
          <label className="fld">Score received
            <input value={form.score_received} placeholder="88 or 88/100"
                   onChange={(e) => setField("score_received", e.target.value)} />
          </label>
          <label className="fld">Out of
            <input value={form.max_score} placeholder="100"
                   onChange={(e) => setField("max_score", e.target.value)} />
          </label>
          <label className="fld">Winner (if not won)
            <input value={form.winner} placeholder="who won"
                   onChange={(e) => setField("winner", e.target.value)} />
          </label>
          <label className="fld">Award date
            <input value={form.award_date} placeholder="2026-08-01"
                   onChange={(e) => setField("award_date", e.target.value)} />
          </label>
          <label className="fld">Debrief date
            <input value={form.debrief_date} placeholder="2026-08-08"
                   onChange={(e) => setField("debrief_date", e.target.value)} />
          </label>
        </div>
        <label className="fld">Buyer / evaluator feedback
          <textarea rows={2} value={form.feedback} placeholder="What the evaluator said — strengths and weaknesses"
                    onChange={(e) => setField("feedback", e.target.value)} />
        </label>
      </section>

      {/* Lessons Learned Log — categorised notes, each optionally tagged with a
          library action that becomes a suggested update below */}
      <section className="tsec">
        <div className="label">Lessons Learned</div>
        {lessons.length === 0 && (
          <p className="empty sm">No lessons logged. Add what to carry forward — tag a lesson with a
          <b> library action</b> (promote / refresh / retire) to feed it back into the Stage-4 library.</p>
        )}
        {lessons.map((l, i) => (
          <div className="lesson-row" key={i}>
            <select value={l.category} onChange={(e) => setLesson(i, "category", e.target.value)}>
              <option value="">— category —</option>
              {ref_.lesson_categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <input className="lesson-note" value={l.note} placeholder="What we learned"
                   onChange={(e) => setLesson(i, "note", e.target.value)} />
            <select value={l.action} title="Library action this lesson implies"
                    onChange={(e) => setLesson(i, "action", e.target.value)}>
              <option value="">no library action</option>
              <option value="promote">promote ▲</option>
              <option value="refresh">refresh ↻</option>
              <option value="retire">retire ▼</option>
            </select>
            <button className="clar-del" title="Remove" onClick={() => removeLesson(i)}>✕</button>
          </div>
        ))}
        <button className="mini-btn tonal add-clar" onClick={addLesson}>+ Add lesson</button>
      </section>

      {/* Suggested library updates — derived from the result + tagged lessons.
          Read-only: applying them into the real library needs the SharePoint
          connection Stage 4 is blocked on. The human signs off here. */}
      <section className="tsec">
        <div className="label">Suggested library updates — you approve each</div>
        {suggestions.length === 0 ? (
          <p className="empty sm">No library updates suggested yet. A won or lost result, or a lesson
          tagged with an action, proposes updates here after you save.</p>
        ) : (
          <div className="actions-l">
            {suggestions.map((s, i) => (
              <div className="lib-act" key={i}>
                <span className={`ic ${ACTION_IC[s.action] || "ic-ref"}`}>{ACTION_GLYPH[s.action] || "◆"}</span>
                <div>
                  <div className="la-t">{s.title}</div>
                  {s.detail && <div className="la-s">{s.detail}</div>}
                </div>
                {s.auto && <span className="tag" title="Derived from the result">auto</span>}
              </div>
            ))}
          </div>
        )}
        <div className="src-note">
          ◆ Approved updates flow into the Stage-4 library once the SharePoint connection is stood up
          (Phase 3). Nothing is written to the library from here — the tool proposes; you confirm.
        </div>
      </section>

      <section className="tsec">
        <label className="fld">Notes
          <textarea rows={2} value={form.notes} onChange={(e) => setField("notes", e.target.value)} />
        </label>
        <div className="decide manage-actions">
          <button className="mini-btn" disabled={saving} onClick={() => save()}>Save outcome</button>
          <button className="mini-btn submit-btn"
                  disabled={saving || suggestions.length === 0 || approved}
                  title={suggestions.length === 0 ? "Save an outcome with library suggestions first" : "Sign off the suggested library updates"}
                  onClick={() => save({ library_approved: "yes" })}>
            {approved ? "Library updates approved ✓" : "Approve library updates"}
          </button>
          {!decided && form.result === "Awaiting" &&
            <span className="triage-hint">Set the result to Won / Not Won / Withdrawn to close the loop.</span>}
          {saving && <span className="triage-hint">Saving…</span>}
          {savedNote && <span className="triage-hint ok">{savedNote}</span>}
          {error && <span className="error">⚠ {error}</span>}
        </div>
      </section>
    </div>
  );
}
