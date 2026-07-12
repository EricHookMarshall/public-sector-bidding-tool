// Compliance & Renewals — its own routed view (#compliance), outside the 6-stage
// journey and visible to everyone (not Admin-only). The app-OWNED, ORG-LEVEL
// register of every credential / policy / framework and its renewal status,
// lifting the "expired cert at bid time" failure — the reason this tool exists —
// out of per-bid burial into one screen. Assets are uploaded here (bytes go to a
// gitignored store, SharePoint later) or registered as references; the backend
// derives expired / expiring / ok live against today. A fresh DB is seeded from
// the bid library so the register isn't empty on day one.
import { useEffect, useState } from "react";
import {
  getComplianceBoard, getComplianceReference,
  createComplianceAsset, updateComplianceAsset, deleteComplianceAsset,
  importComplianceFromLibrary, downloadComplianceAsset,
} from "./api.js";

const BLANK = {
  name: "", category: "Company Credentials", expiry_date: "",
  review_frequency: "", owner: "", notes: "",
};

// Expiry colour + human label — mirrors the Complete evidence ledger so the two
// views read identically (var(--crit)/(--warn)/(--good)).
function expiryView(a) {
  const st = a.expiry_status;
  const date = a.effective_expiry || a.expiry_date || "";
  if (st === "expired")
    return { color: "var(--crit)", label: `EXPIRED ${date}`, days: a.days_to_expiry };
  if (st === "expiring_soon")
    return { color: "var(--warn)", label: `${date} · ${a.days_to_expiry}d left`, days: a.days_to_expiry };
  if (date) return { color: "var(--good)", label: `OK ${date}`, days: a.days_to_expiry };
  return { color: "var(--muted)", label: "no renewal date", days: null };
}

export default function ComplianceView() {
  const [board, setBoard] = useState(null);   // { assets, summary, reference, library_available }
  const [ref, setRef] = useState(null);        // { categories, expiring_soon_days }
  const [error, setError] = useState("");
  const [form, setForm] = useState(BLANK);
  const [file, setFile] = useState(null);
  const [editing, setEditing] = useState(null); // asset id being edited, or null
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  const load = () =>
    getComplianceBoard()
      .then(setBoard)
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
    getComplianceReference().then(setRef).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const resetForm = () => { setForm(BLANK); setFile(null); setEditing(null); };

  const onEdit = (a) => {
    setEditing(a.id);
    setForm({
      name: a.name || "", category: a.category || "Company Credentials",
      expiry_date: a.expiry_date || "", review_frequency: a.review_frequency || "",
      owner: a.owner || "", notes: a.notes || "",
    });
    setFile(null);
    setNote("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setError("Name is required."); return; }
    setBusy(true); setError(""); setNote("");
    try {
      if (editing) {
        await updateComplianceAsset(editing, form);
        setNote("Asset updated.");
      } else {
        await createComplianceAsset(form, file);
        setNote(file ? "Asset uploaded." : "Reference registered.");
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async (a) => {
    if (!window.confirm(`Delete "${a.name}"${a.has_file ? " and its stored file" : ""}?`)) return;
    setBusy(true); setError(""); setNote("");
    try {
      await deleteComplianceAsset(a.id);
      if (editing === a.id) resetForm();
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const onImport = async () => {
    setBusy(true); setError(""); setNote("");
    try {
      const r = await importComplianceFromLibrary();
      setNote(r.imported ? `Imported ${r.imported} credential(s) from the bid library.`
                         : "Register already populated — nothing imported.");
      await load();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const onDownload = (a) =>
    downloadComplianceAsset(a.id, a.file_name).catch((err) => setError(err.message));

  const cats = ref?.categories || ["Company Credentials"];
  const s = board?.summary;

  return (
    <div className="wrap compliance">
      <div className="settings-head">
        <button className="link" onClick={() => { window.location.hash = "search"; }}>
          ← Back to journey
        </button>
        <h2>🛡 Compliance &amp; Renewals</h2>
      </div>
      <p className="stage-sub">
        The organisation's compliance register — every credential, policy and framework
        with its renewal date. Expiry is tracked here so a lapsed certificate can never
        surface at bid time. Files upload to a private store; SharePoint later.
      </p>

      {error && <p className="error">⚠ {error}</p>}
      {note && <p className="hint ok">{note}</p>}
      {!board && !error && <p className="empty">Loading…</p>}

      {board && (
        <>
          {/* Summary KPIs — reuse the app's .pd-facts stat grid */}
          <div className="pd-facts comp-stats">
            <div className="stat"><span className="k">Tracked</span><span className="v">{s.total}</span></div>
            <div className="stat" style={s.expired ? { borderColor: "var(--crit)" } : undefined}>
              <span className="k">Expired</span>
              <span className="v" style={{ color: s.expired ? "var(--crit)" : undefined }}>{s.expired}</span>
            </div>
            <div className="stat" style={s.expiring_soon ? { borderColor: "var(--warn)" } : undefined}>
              <span className="k">Expiring ≤{ref?.expiring_soon_days ?? 90}d</span>
              <span className="v" style={{ color: s.expiring_soon ? "var(--warn)" : undefined }}>{s.expiring_soon}</span>
            </div>
            <div className="stat"><span className="k">No date</span><span className="v">{s.none}</span></div>
          </div>

          {(s.expired > 0 || s.expiring_soon > 0) && (
            <p className="alert-strip" style={{ borderColor: s.expired ? "var(--crit)" : "var(--warn)" }}>
              {s.expired > 0 && <b style={{ color: "var(--crit)" }}>{s.expired} expired</b>}
              {s.expired > 0 && s.expiring_soon > 0 && " · "}
              {s.expiring_soon > 0 && <b style={{ color: "var(--warn)" }}>{s.expiring_soon} expiring soon</b>}
              {" — renew before these are needed on a live bid."}
            </p>
          )}

          {/* Add / edit form */}
          <form className="settings-card comp-form" onSubmit={onSubmit}>
            <h3 className="settings-section">{editing ? "Edit asset" : "Add an asset"}</h3>
            <div className="comp-form-grid">
              <label className="fld">Name
                <input value={form.name} onChange={set("name")} placeholder="e.g. ISO 27001 Certificate" />
              </label>
              <label className="fld">Category
                <select value={form.category} onChange={set("category")}>
                  {cats.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
              <label className="fld">Renewal / expiry date
                <input type="date" value={form.expiry_date} onChange={set("expiry_date")} />
              </label>
              <label className="fld">Owner
                <input value={form.owner} onChange={set("owner")} placeholder="who keeps this current" />
              </label>
              <label className="fld">Review frequency
                <input value={form.review_frequency} onChange={set("review_frequency")} placeholder="Annually / As Required" />
              </label>
              <label className="fld">{editing ? "File (re-upload not supported in edit)" : "File (optional)"}
                <input type="file" disabled={!!editing} onChange={(e) => setFile(e.target.files?.[0] || null)} />
              </label>
            </div>
            <label className="fld">Notes
              <textarea value={form.notes} onChange={set("notes")} rows={2}
                placeholder="If no date above, a renewal date mentioned here (e.g. 'expires 31 Oct 2026') is picked up automatically." />
            </label>
            <div className="settings-actions">
              <button className="run-btn" type="submit" disabled={busy}>
                {busy ? "Saving…" : editing ? "Save changes" : file ? "Upload asset" : "Register asset"}
              </button>
              {editing && <button type="button" className="mini-btn" onClick={resetForm} disabled={busy}>Cancel</button>}
            </div>
          </form>

          {/* The register */}
          {board.assets.length === 0 ? (
            <div className="empty comp-empty">
              <p>No compliance assets yet.</p>
              {board.library_available &&
                <button className="mini-btn" onClick={onImport} disabled={busy}>Import from bid library</button>}
            </div>
          ) : (
            <div className="ledger comp-ledger">
              <div className="lh comp-row">
                <span>Asset</span><span>Category</span><span>Owner</span><span>Expiry</span><span>File</span><span></span>
              </div>
              {board.assets.map((a) => {
                const ev = expiryView(a);
                return (
                  <div className="lr comp-row" key={a.id}>
                    <span className="comp-name">{a.name}</span>
                    <span className="comp-cat">{a.category}</span>
                    <span>{a.owner || "—"}</span>
                    <span className="st" style={{ color: ev.color }}>{ev.label}</span>
                    <span>
                      {a.has_file
                        ? <button className="link" onClick={() => onDownload(a)} title={a.file_name}>⬇ {a.file_name || "download"}</button>
                        : <span className="comp-noref">{a.source === "seed:library" ? "reference" : "—"}</span>}
                    </span>
                    <span className="comp-actions">
                      <button className="mini-btn" onClick={() => onEdit(a)}>Edit</button>
                      <button className="mini-btn danger" onClick={() => onDelete(a)}>Delete</button>
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
