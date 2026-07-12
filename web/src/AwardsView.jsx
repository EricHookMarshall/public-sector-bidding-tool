// Our Contracts (G1) — its own routed view (#awards), outside the 6-stage journey
// and open to everyone. FWF's OWN public-sector awards, pulled from the OCDS award
// packages (Find a Tender + Contracts Finder) and matched to FWF by its Companies
// House number — the one unambiguous identifier, so we never record a contract that
// isn't ours. The CH number is app config (never hardcoded); until it's set the
// view prompts for it. "Refresh" re-pulls from the live APIs (Admin).
import { useEffect, useState } from "react";
import { getAwardsBoard, saveOwnOrg, refreshAwards, addManualAward, deleteAward } from "./api.js";
import { fmtMoney, fmtDate } from "./format.js";

// Awards recorded by hand (a genuine win public OCDS can't surface) carry this
// source — kept in step with api.py MANUAL_AWARD_SOURCE. Used to badge the card
// honestly and to show the delete/correct control only on manual entries.
const MANUAL_SOURCE = "Internal record (manual)";
const EMPTY_MANUAL = {
  title: "", buyer_name: "", supplier_name: "", award_date: "",
  contract_start: "", contract_end: "", value_amount: "", note: "",
};

export default function AwardsView() {
  const [board, setBoard] = useState(null);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [chNumber, setChNumber] = useState("");
  const [legalName, setLegalName] = useState("");
  const [showManual, setShowManual] = useState(false);
  const [manual, setManual] = useState(EMPTY_MANUAL);

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

  const onAddManual = async (e) => {
    e.preventDefault();
    setBusy(true); setError(""); setNote("");
    try {
      const body = { ...manual };
      // value_amount is a text input — send a number or omit it entirely.
      body.value_amount = manual.value_amount === "" ? null : Number(manual.value_amount);
      await addManualAward(body);
      setNote("Recorded as an internal award. Marked ‘unverified’ — it isn't a public OCDS match.");
      setManual(EMPTY_MANUAL);
      setShowManual(false);
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const onDeleteAward = async (id) => {
    if (!window.confirm("Remove this recorded award?")) return;
    setBusy(true); setError(""); setNote("");
    try {
      await deleteAward(id);
      setNote("Award removed.");
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const setM = (k) => (e) => setManual((m) => ({ ...m, [k]: e.target.value }));

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

          {/* Add a known award by hand — for a genuine win public OCDS can't
              surface (named-only notice / sub-threshold / subcontract). */}
          <div className="settings-card awards-manual">
            <div className="settings-head-row">
              <h3 className="settings-section">Record a known award</h3>
              <button className="mini-btn" type="button"
                onClick={() => { setShowManual((v) => !v); setError(""); setNote(""); }}>
                {showManual ? "Cancel" : "+ Add by hand"}
              </button>
            </div>
            <p className="fld-help">
              For a contract we won that the public award notices don’t show — recorded as an
              internal record and marked <b>unverified</b>, never dressed up as a public match.
              Capture what’s known; leave the rest blank.
            </p>
            {showManual && (
              <form className="awards-manual-grid" onSubmit={onAddManual}>
                <label className="fld awards-manual-wide">Title / service
                  <input value={manual.title} onChange={setM("title")}
                    placeholder="e.g. Workforce transformation support" />
                </label>
                <label className="fld">Buyer
                  <input value={manual.buyer_name} onChange={setM("buyer_name")}
                    placeholder="e.g. NHS Barnsley" />
                </label>
                <label className="fld">Supplier
                  <input value={manual.supplier_name} onChange={setM("supplier_name")}
                    placeholder={legalName || "Future Work Force Limited"} />
                </label>
                <label className="fld">Award date
                  <input value={manual.award_date} onChange={setM("award_date")}
                    placeholder="YYYY-MM-DD (approx ok)" />
                </label>
                <label className="fld">Value (£)
                  <input value={manual.value_amount} onChange={setM("value_amount")}
                    inputMode="decimal" placeholder="e.g. 45000" />
                </label>
                <label className="fld">Contract start
                  <input value={manual.contract_start} onChange={setM("contract_start")}
                    placeholder="YYYY-MM-DD" />
                </label>
                <label className="fld">Contract end
                  <input value={manual.contract_end} onChange={setM("contract_end")}
                    placeholder="YYYY-MM-DD" />
                </label>
                <label className="fld awards-manual-wide">Note (where this came from)
                  <input value={manual.note} onChange={setM("note")}
                    placeholder="e.g. original notice not locatable; from internal records" />
                </label>
                <div className="settings-actions awards-manual-wide">
                  <button className="run-btn" type="submit" disabled={busy}>
                    {busy ? "Saving…" : "Record award"}
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Summary KPIs */}
          {(configured || board.awards.length > 0) && (
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
              {board.awards.map((a) => {
                const isManual = a.source === MANUAL_SOURCE;
                return (
                <article className="settings-card award-card" key={`${a.source}:${a.award_id}`}>
                  <div className="award-top">
                    <h4>{a.title}
                      {isManual && <span className="award-badge" title="Recorded by hand — not a verified public OCDS match">unverified</span>}
                    </h4>
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
                    {isManual && (
                      <button className="link award-del" type="button"
                        onClick={() => onDeleteAward(a.id)} disabled={busy}>Remove</button>
                    )}
                  </div>
                </article>
              );})}
            </div>
          )}
        </>
      )}
    </div>
  );
}
