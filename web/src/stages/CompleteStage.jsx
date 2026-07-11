// Stage 04 — Complete. The FOR006 tender-response matrix + AI pre-fill from the
// real bid library, wired to data. Every live bid shows its compliance matrix (one
// row per tender question) with a completion bar and a live word-count check — the
// hard compliance gate on UK tenders. Open a bid to work its matrix: draft each
// answer (AI-drafts from FWF's real Approved Answer Bank, grounded in retrieved
// evidence), edit, set a status, and watch the evidence ledger flag any credential
// that has expired. Nothing auto-approves; a person approves each answer.
//
// The library is read live through the LocalMirror provider seam (the real
// gitignored export). If it isn't connected, the workspace says so honestly rather
// than faking content — and GraphSharePoint swaps in behind the same seam later.
import { useEffect, useState } from "react";
import {
  getCompleteReference, getCompleteBoard, getBidResponses,
  saveBidResponses, aiDraftResponse,
} from "../api.js";
import { deadlineBadge } from "../format.js";

function pct(n, d) { return d ? Math.round((100 * n) / d) : 0; }

// Library provider status → an honest connection strip.
function ProviderStrip({ lib }) {
  if (!lib) return null;
  if (!lib.available) {
    return (
      <div className="alert-strip warn lib-strip">
        ⚠ Bid library not connected ({lib.source}). The matrix works, but AI pre-fill and the evidence
        ledger need the export present. GraphSharePoint drops in behind the same seam later.
      </div>
    );
  }
  return (
    <div className="alert-strip ok-strip lib-strip">
      ✓ Library connected — <b>{lib.count}</b> items via {lib.source}. AI drafts from this, grounded in real evidence.
    </div>
  );
}

export default function CompleteStage() {
  const [ref, setRef] = useState(null);
  const [board, setBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBid, setSelectedBid] = useState(null);

  useEffect(() => {
    getCompleteReference().then(setRef).catch((e) => setError(e.message));
  }, []);

  const loadBoard = () => {
    setLoading(true);
    setError(null);
    return getCompleteBoard()
      .then(setBoard)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (selectedBid) return;
    loadBoard();
  }, [selectedBid]);

  if (selectedBid) {
    return <CompleteDetail bidId={selectedBid} ref_={ref} onBack={() => setSelectedBid(null)} />;
  }

  return (
    <div className="complete">
      {error && <p className="error">⚠ {error}</p>}
      {loading && !board && <p className="empty">Loading matrix…</p>}

      {board && (
        <>
          <ProviderStrip lib={board.library} />
          {board.count === 0 ? (
            <p className="empty">
              No live bids to complete yet. A <b>Go</b> in Triage promotes an opportunity into a bid;
              once it's here you can build its FOR006 compliance matrix and draft each answer.
            </p>
          ) : (
            <>
              <div className="label">Live bids — tender-response matrix</div>
              <div className="manage-grid">
                {board.bids.map((b) => (
                  <CompleteCard key={b.bid_id} b={b} imminent={ref?.imminent_days ?? 7}
                    onOpen={() => setSelectedBid(b.bid_id)} />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function CompleteCard({ b, imminent, onOpen }) {
  const s = b.summary;
  const sub = deadlineBadge(b.days_to_submission, imminent);
  const tone = s.ready ? "go" : s.over_word_limit > 0 ? "risk" : "draft";
  return (
    <button className={`kcard t-${tone} manage-card`} onClick={onOpen} title="Open the FOR006 matrix + AI pre-fill">
      <div className="kt">{b.title}</div>
      <div className="km">
        <span className="tag">{b.started ? `${s.approved}/${s.total} approved` : "not started"}</span>
        {s.over_word_limit > 0 && <span className="tag warn-tag">⚑ {s.over_word_limit} over limit</span>}
      </div>
      <div className="bar" style={{ marginTop: 8 }} title={`${s.pct_complete}% approved`}>
        <i style={{ width: `${s.pct_complete}%` }} />
      </div>
      <div className="km manage-foot">
        {sub && <span className={`dl dl-${sub.cls}`} title="Submission deadline">▸ closes {sub.label}</span>}
        {s.ready
          ? <span className="st-pill p-pass">Ready</span>
          : <span className="st-pill p-wait">{s.answered}/{s.total} answered</span>}
      </div>
    </button>
  );
}

// ---- Per-bid FOR006 matrix workspace ---------------------------------------

function CompleteDetail({ bidId, ref_, onBack }) {
  const [payload, setPayload] = useState(null);
  const [items, setItems] = useState([]);
  const [sel, setSel] = useState(0);
  const [aiByIdx, setAiByIdx] = useState({});     // index → {matches, meta}
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [error, setError] = useState(null);
  const [savedNote, setSavedNote] = useState(null);

  const hydrate = (p) => {
    setPayload(p);
    setItems(p.items || []);
  };

  useEffect(() => {
    setLoading(true);
    getBidResponses(bidId).then(hydrate).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [bidId]);

  const setItem = (i, k, val) =>
    setItems((its) => its.map((it, j) => (j === i ? { ...it, [k]: val } : it)));

  const save = async () => {
    setSaving(true); setError(null); setSavedNote(null);
    try {
      const p = await saveBidResponses(bidId, { items });
      hydrate(p);
      setSavedNote("Saved.");
    } catch (e) { setError(e.message); } finally { setSaving(false); }
  };

  const aiDraft = async (i) => {
    setDrafting(true); setError(null); setSavedNote(null);
    try {
      const r = await aiDraftResponse(bidId, i);
      setItems((its) => its.map((it, j) => (j === i
        ? { ...it, supplier_response: r.draft.supplier_response, status: it.status === "To do" ? "Drafted" : it.status }
        : it)));
      setAiByIdx((m) => ({ ...m, [i]: { matches: r.matches, meta: r.meta } }));
    } catch (e) { setError(e.message); } finally { setDrafting(false); }
  };

  if (loading) return <p className="empty">Loading matrix…</p>;
  if (error && !payload) return <p className="error">⚠ {error}</p>;
  if (!payload || !ref_) return null;

  const opp = payload.opportunity;
  const lib = payload.library;
  // Live completion summary from the edited items (word count computed client-side).
  const wc = (t) => (t ? (String(t).match(/\S+/g) || []).length : 0);
  const approved = items.filter((it) => it.status === "Approved").length;
  const over = items.filter((it) => it.word_count_limit && wc(it.supplier_response) > it.word_count_limit);
  const sub = deadlineBadge(payload.summary?.days_to_submission, ref_?.imminent_days ?? 7);

  const q = items[sel] || null;
  const ai = aiByIdx[sel];

  return (
    <div className="plan-detail complete-detail">
      <div className="pd-head">
        <button className="mini-btn ghost" onClick={onBack}>← Board</button>
        <h3>{opp.title}</h3>
        {lib?.available
          ? <span className="pill p-pass" title={lib.source}>Library ✓</span>
          : <span className="pill p-fail" title={lib?.source}>No library</span>}
      </div>

      <div className="pd-facts">
        <div className="stat"><div className="k">Buyer</div><div className="v sm">{opp.buyer_name || "—"}</div></div>
        <div className="stat">
          <div className="k">Submission</div>
          <div className="v sm">{opp.submission_deadline ? String(opp.submission_deadline).slice(0, 10) : "—"}</div>
        </div>
        <div className="stat">
          <div className="k">Approved</div>
          <div className="v">{approved}<span className="v-sub">/{items.length}</span></div>
          <div className="u">{pct(approved, items.length)}% complete</div>
        </div>
        <div className={`stat${over.length ? " stat-warn" : ""}`}>
          <div className="k">Word-count</div>
          <div className="v sm">{over.length ? `${over.length} over limit` : "all within ✓"}</div>
        </div>
      </div>

      {/* Two-pane workspace: the compliance matrix + the selected question's draft */}
      <div className="ws complete-ws">
        <div className="qlist">
          <div className="label" style={{ marginBottom: 2 }}>Compliance matrix (FOR006)</div>
          {items.map((it, i) => {
            const words = wc(it.supplier_response);
            const isOver = it.word_count_limit && words > it.word_count_limit;
            const dot = ref_.status_dot?.[it.status] || "todo";
            return (
              <button className={`qi ${i === sel ? "sel" : ""}`} key={i} onClick={() => setSel(i)}>
                <div className="qs">
                  <span className={`dotp d-${dot}`} />
                  <span className="qn">{it.section ? `${it.section} · ` : ""}{it.question_ref || `Q${i + 1}`}</span>
                  {isOver && <span className="dl dl-crit qi-wc" title="Over word limit">{words}/{it.word_count_limit}</span>}
                </div>
                <span style={{ color: "var(--muted)" }}>
                  {(it.question_text || "").slice(0, 46) || "—"}{(it.question_text || "").length > 46 ? "…" : ""}
                </span>
              </button>
            );
          })}
        </div>

        {q && (
          <div className="draft">
            <div className="draft-h">
              <b style={{ fontSize: "12.5px" }}>
                {q.section ? `${q.section} · ` : ""}{q.question_ref}
                {q.weighting_pct ? ` — ${q.weighting_pct}%` : ""}
              </b>
              <button className="mini-btn tonal" disabled={drafting || !lib?.available}
                      title={lib?.available ? "AI-draft from the library" : "Library not connected"}
                      onClick={() => aiDraft(sel)}>
                {drafting ? "Drafting…" : "✦ AI draft"}
              </button>
            </div>
            <div className="draft-body">
              {q.question_text && <p style={{ fontWeight: 600 }}>{q.question_text}</p>}

              <textarea rows={9} className="resp-text" value={q.supplier_response || ""}
                        placeholder="Draft the answer here, or use AI draft to start from the library."
                        onChange={(e) => setItem(sel, "supplier_response", e.target.value)} />

              <div className="resp-foot">
                <span className={`dl ${q.word_count_limit && wc(q.supplier_response) > q.word_count_limit ? "dl-crit" : "dl-ok"}`}>
                  {wc(q.supplier_response)}{q.word_count_limit ? ` / ${q.word_count_limit}` : ""} words
                </span>
                <label className="mini-fld inline">Status
                  <select value={q.status} onChange={(e) => setItem(sel, "status", e.target.value)}>
                    {ref_.statuses.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </label>
                <input className="owner-inp" value={q.owner || ""} placeholder="owner"
                       onChange={(e) => setItem(sel, "owner", e.target.value)} />
              </div>

              {ai && (
                <div className="ai-meta">
                  <div className="ai-flag">✦ AI-drafted from {ai.matches.length} library match{ai.matches.length !== 1 ? "es" : ""}</div>
                  {ai.meta?.win_themes && <p><b>Win themes:</b> {ai.meta.win_themes}</p>}
                  {ai.meta?.evidence_used?.length > 0 && (
                    <p><b>Evidence used:</b> {ai.meta.evidence_used.join("; ")}</p>)}
                  {ai.meta?.gaps && <p className="ai-gaps"><b>⚠ Gaps to check:</b> {ai.meta.gaps}</p>}
                  <div className="src-note">
                    ◆ Drafted from FWF's real library. Review, add win themes, and <b>approve</b> — nothing is
                    submitted as-is.
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Evidence ledger — the compliance-asset register, expiry surfaced */}
      <section className="tsec">
        <div className="label">Evidence ledger — credentials &amp; expiry</div>
        {(!payload.evidence || payload.evidence.length === 0) ? (
          <p className="empty sm">No evidence items — the library isn't connected, or none carry a category/expiry.</p>
        ) : (
          <div className="ledger">
            <div className="lh"><span>Item</span><span>Category</span><span>Expiry</span></div>
            {payload.evidence.slice(0, 8).map((e, i) => {
              const st = e.expiry_status;
              const color = st === "expired" ? "var(--crit)" : st === "expiring_soon" ? "var(--warn)" : "var(--good)";
              const label = st === "expired" ? `EXPIRED ${e.expiry_date}`
                : st === "expiring_soon" ? `${e.expiry_date} (${e.days_to_expiry}d)`
                : e.expiry_date ? `OK ${e.expiry_date}` : "—";
              return (
                <div className="lr" key={i}>
                  <span>{e.item}</span><span>{e.category}</span>
                  <span className="st" style={{ color }}>{label}</span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <div className="decide manage-actions">
        <button className="mini-btn" disabled={saving} onClick={save}>Save matrix</button>
        {saving && <span className="triage-hint">Saving…</span>}
        {savedNote && <span className="triage-hint ok">{savedNote}</span>}
        {error && <span className="error">⚠ {error}</span>}
      </div>
    </div>
  );
}
