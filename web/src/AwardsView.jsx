// Our Contracts (G1) — its own routed view (#awards), outside the 6-stage journey
// and open to everyone. FWF's OWN public-sector awards, pulled from the OCDS award
// packages (Find a Tender + Contracts Finder) and matched to FWF by its Companies
// House number — the one unambiguous identifier, so we never record a contract that
// isn't ours. The CH number is app config (never hardcoded); until it's set the
// view prompts for it. "Refresh" re-pulls from the live APIs (Admin).
import { useEffect, useState } from "react";
import { getAwardsBoard, saveOwnOrg, refreshAwards } from "./api.js";
import { fmtMoney, fmtDate } from "./format.js";

export default function AwardsView() {
  const [board, setBoard] = useState(null);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [chNumber, setChNumber] = useState("");
  const [legalName, setLegalName] = useState("");

  const load = () =>
    getAwardsBoard()
      .then((b) => {
        setBoard(b);
        setChNumber(b.own_org?.companies_house_number || "");
        setLegalName(b.own_org?.legal_name || "");
      })
      .catch((e) => setError(e.message));

  useEffect(() => { load(); }, []);

  const onSaveOrg = async (e) => {
    e.preventDefault();
    setBusy(true); setError(""); setNote("");
    try {
      await saveOwnOrg({ companies_house_number: chNumber, legal_name: legalName });
      setNote("Saved. Now refresh to pull our awards.");
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const onRefresh = async () => {
    setBusy(true); setError(""); setNote("");
    try {
      const r = await refreshAwards();
      let msg = `Scanned ${r.scanned} award notices — ${r.inserted} new, ${r.updated} updated.`;
      if (r.incomplete) msg += ` ⚠ ${r.failed_sources} source(s) unavailable.`;
      setNote(msg);
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const s = board?.summary;
  const configured = board?.configured;

  return (
    <div className="wrap awards">
      <div className="settings-head">
        <button className="link" onClick={() => { window.location.hash = "search"; }}>
          ← Back to journey
        </button>
        <h2>🏆 Our contracts</h2>
      </div>
      <p className="stage-sub">
        Public-sector contracts FWF has been awarded, pulled from the official award
        notices and matched to us by Companies House number — our public track record.
      </p>

      {error && <p className="error">⚠ {error}</p>}
      {note && <p className="hint ok">{note}</p>}
      {!board && !error && <p className="empty">Loading…</p>}

      {board && (
        <>
          {/* Identity config — the CH number that drives matching. */}
          <form className="settings-card awards-org" onSubmit={onSaveOrg}>
            <h3 className="settings-section">Our organisation</h3>
            <p className="fld-help">
              Matching is by Companies House number so we never record a contract that
              isn't ours. {configured ? "" : "Set it below to begin."}
            </p>
            <div className="awards-org-grid">
              <label className="fld">Companies House number
                <input value={chNumber} onChange={(e) => setChNumber(e.target.value)}
                  placeholder="e.g. 11934102" />
              </label>
              <label className="fld">Legal name (optional)
                <input value={legalName} onChange={(e) => setLegalName(e.target.value)}
                  placeholder="Future Workforce UK Ltd" />
              </label>
            </div>
            <div className="settings-actions">
              <button className="mini-btn" type="submit" disabled={busy}>Save</button>
              <button className="run-btn" type="button" onClick={onRefresh}
                disabled={busy || !configured}
                title={configured ? "Pull awards from the live OCDS APIs" : "Set the CH number first"}>
                {busy ? "Working…" : "↻ Refresh from award notices"}
              </button>
            </div>
          </form>

          {/* Summary KPIs */}
          {configured && (
            <div className="pd-facts awards-stats">
              <div className="stat"><span className="k">Awards</span><span className="v">{s.total}</span></div>
              <div className="stat"><span className="k">Total value</span><span className="v">{fmtMoney(s.total_value)}</span></div>
              <div className="stat"><span className="k">Latest</span><span className="v">{s.latest_award_date ? fmtDate(s.latest_award_date) : "—"}</span></div>
              <div className="stat"><span className="k">Sources</span><span className="v">{Object.keys(s.by_source || {}).length}</span></div>
            </div>
          )}

          {/* The awards */}
          {board.awards.length === 0 ? (
            <div className="empty awards-empty">
              <p>{configured
                ? "No awards recorded yet — hit Refresh to search the award notices for our Companies House number."
                : "Set our Companies House number above, then refresh."}</p>
            </div>
          ) : (
            <div className="awards-list">
              {board.awards.map((a) => (
                <article className="settings-card award-card" key={`${a.source}:${a.award_id}`}>
                  <div className="award-top">
                    <h4>{a.title}</h4>
                    <span className="award-value">{fmtMoney(a.value_amount, a.currency)}</span>
                  </div>
                  <div className="award-meta">
                    <span><b>Buyer:</b> {a.buyer_name || "—"}</span>
                    <span><b>Awarded:</b> {fmtDate(a.award_date)}</span>
                    {(a.contract_start || a.contract_end) && (
                      <span><b>Term:</b> {fmtDate(a.contract_start)} → {fmtDate(a.contract_end)}</span>
                    )}
                  </div>
                  <div className="award-foot">
                    <span className="award-src">{a.source}</span>
                    {a.url && <a className="link" href={a.url} target="_blank" rel="noreferrer">View notice ↗</a>}
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
