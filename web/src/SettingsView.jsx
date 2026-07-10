// Settings — its own routed view (#settings), outside the 6-stage journey, and
// Admin-only. Three cards laid out two-up: AI connection (provider/model/key) and
// Bid day rates on the left, the editable AI prompts on the right. Lets a novice
// run the tool without hand-editing .env or the code:
//  - the API key is write-only (saved to the git-ignored .env, never sent back);
//  - day rates + AI prompts persist in bids.db (app_settings), so they travel
//    with the data and stay editable on Azure.
import { useEffect, useState } from "react";
import {
  getConfig, saveConfig, testConfig,
  getDayRates, saveDayRates,
  getAiPrompts, saveAiPrompts,
} from "./api.js";

export default function SettingsView() {
  // --- AI connection ---
  const [cfg, setCfg] = useState(null);
  const [provider, setProvider] = useState("anthropic");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [test, setTest] = useState(null);   // { ok, ... } | { error }

  // --- Bid day rates ---
  const [dr, setDr] = useState(null);        // { roles, rates, default_rate, note }
  const [rates, setRates] = useState({});    // editable {role: £/day}
  const [drSaving, setDrSaving] = useState(false);
  const [drSaved, setDrSaved] = useState(false);

  // --- AI prompts ---
  const [ap, setAp] = useState(null);        // { profile_default, note, ... }
  const [profile, setProfile] = useState("");
  const [triageGuidance, setTriageGuidance] = useState("");
  const [completeGuidance, setCompleteGuidance] = useState("");
  const [apSaving, setApSaving] = useState(false);
  const [apSaved, setApSaved] = useState(false);

  const [error, setError] = useState(null);

  useEffect(() => {
    getConfig()
      .then((c) => { setCfg(c); setProvider(c.provider); setModel(c.model); })
      .catch((e) => setError(e.message));
    getDayRates()
      .then((d) => { setDr(d); setRates(d.rates); })
      .catch((e) => setError(e.message));
    getAiPrompts()
      .then((p) => {
        setAp(p);
        setProfile(p.profile);
        setTriageGuidance(p.triage_guidance);
        setCompleteGuidance(p.complete_guidance);
      })
      .catch((e) => setError(e.message));
  }, []);

  const onSave = async () => {
    setSaving(true); setError(null); setSaved(false); setTest(null);
    try {
      const body = { provider, model };
      if (apiKey.trim()) body.api_key = apiKey.trim();
      const c = await saveConfig(body);
      setCfg(c);
      setApiKey("");           // never keep the secret in the field
      setSaved(true);
    } catch (e) { setError(e.message); } finally { setSaving(false); }
  };

  const onTest = async () => {
    setTesting(true); setTest(null);
    try {
      const r = await testConfig();
      setTest({ ok: true, ...r });
    } catch (e) { setTest({ error: e.message }); } finally { setTesting(false); }
  };

  const onSaveRates = async () => {
    setDrSaving(true); setError(null); setDrSaved(false);
    try {
      const numeric = Object.fromEntries(
        Object.entries(rates).map(([role, v]) => [role, Number(v)]));
      const d = await saveDayRates(numeric);
      setDr(d); setRates(d.rates); setDrSaved(true);
    } catch (e) { setError(e.message); } finally { setDrSaving(false); }
  };

  const onSavePrompts = async () => {
    setApSaving(true); setError(null); setApSaved(false);
    try {
      const p = await saveAiPrompts({
        profile,
        triage_guidance: triageGuidance,
        complete_guidance: completeGuidance,
      });
      setAp(p);
      setProfile(p.profile);
      setTriageGuidance(p.triage_guidance);
      setCompleteGuidance(p.complete_guidance);
      setApSaved(true);
    } catch (e) { setError(e.message); } finally { setApSaving(false); }
  };

  const ks = cfg?.key_status;

  return (
    <div className="wrap settings">
      <div className="settings-head">
        <button className="link" onClick={() => { window.location.hash = "search"; }}>
          ← Back to journey
        </button>
        <h2>Settings</h2>
      </div>

      {error && <p className="error">⚠ {error}</p>}
      {!cfg && !error && <p className="empty">Loading…</p>}

      <div className="settings-grid">
        <div className="settings-col">
          {cfg && (
            <div className="settings-card">
              <h3 className="settings-section">AI connection</h3>
              <label className="fld">
                Provider
                <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                  {cfg.providers.map((p) => (
                    <option key={p.id} value={p.id} disabled={!p.available}>
                      {p.label}{p.available ? "" : ` — ${p.note || "unavailable"}`}
                    </option>
                  ))}
                </select>
              </label>

              <label className="fld">
                Model
                <select value={model} onChange={(e) => setModel(e.target.value)}>
                  {cfg.models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label} — {m.note}{m.default ? " (default)" : ""}
                    </option>
                  ))}
                </select>
              </label>

              <label className="fld">
                Anthropic API key
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={ks?.set ? `configured ••••${ks.last4 || ""} — leave blank to keep` : "not set — paste your key"}
                  autoComplete="off"
                />
                <span className="fld-help">
                  Stored locally in <code>src/.env</code> (never committed). Write-only —
                  it isn't sent back to this screen.
                </span>
              </label>

              <div className="settings-actions">
                <button className="run-btn" onClick={onSave} disabled={saving}>
                  {saving ? "Saving…" : "Save connection"}
                </button>
                <button className="mini-btn tonal" onClick={onTest} disabled={testing || !ks?.set}
                        title={ks?.set ? "Do a cheap live call to verify the key + model" : "Set a key first"}>
                  {testing ? "Testing…" : "Test connection"}
                </button>
                {saved && <span className="triage-hint ok">Saved.</span>}
              </div>

              {test && (
                <div className={`test-result ${test.ok ? "ok" : "bad"}`}>
                  {test.ok
                    ? `✓ Connected — ${test.provider} · ${test.model} replied “${test.reply}”.`
                    : `✗ ${test.error}`}
                </div>
              )}
            </div>
          )}

          {dr && (
            <div className="settings-card">
              <h3 className="settings-section">Bid day rates</h3>
              <p className="fld-help" style={{ marginTop: 0 }}>
                The £/day for each bid-writing role. These drive the “cost to chase”
                a bid — effort-days × rate, per FOR001 complexity. Default is
                £{dr.default_rate}/day for every role.
              </p>
              <div className="rate-grid">
                {dr.roles.map((role) => (
                  <label className="fld" key={role}>
                    {role}
                    <input
                      type="number" min="1" step="10"
                      value={rates[role] ?? ""}
                      onChange={(e) => setRates((r) => ({ ...r, [role]: e.target.value }))}
                    />
                  </label>
                ))}
              </div>
              <div className="settings-actions">
                <button className="run-btn" onClick={onSaveRates} disabled={drSaving}>
                  {drSaving ? "Saving…" : "Save day rates"}
                </button>
                {drSaved && <span className="triage-hint ok">Saved.</span>}
              </div>
              <span className="fld-help">{dr.note}</span>
            </div>
          )}
        </div>

        <div className="settings-col">
          {ap && (
            <div className="settings-card">
              <h3 className="settings-section">AI prompts</h3>
              <p className="fld-help" style={{ marginTop: 0 }}>{ap.note}</p>

              <label className="fld">
                <span className="fld-row">
                  Company / AI profile
                  <button type="button" className="link sm"
                          onClick={() => setProfile(ap.profile_default)}>
                    Insert default
                  </button>
                </span>
                <textarea
                  rows={9}
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  placeholder="Leave blank to use the built-in FWF profile."
                />
                <span className="fld-help">
                  The AI’s context for both Triage and Complete drafts. Blank = the
                  built-in default. Facts decay — keep this current.
                </span>
              </label>

              <label className="fld">
                Triage drafting guidance <span className="fld-opt">(optional)</span>
                <textarea
                  rows={3}
                  value={triageGuidance}
                  onChange={(e) => setTriageGuidance(e.target.value)}
                  placeholder="Extra house-style for the Triage qualification draft."
                />
              </label>

              <label className="fld">
                Complete drafting guidance <span className="fld-opt">(optional)</span>
                <textarea
                  rows={3}
                  value={completeGuidance}
                  onChange={(e) => setCompleteGuidance(e.target.value)}
                  placeholder="Extra house-style for the Complete tender-answer draft."
                />
              </label>

              <div className="settings-actions">
                <button className="run-btn" onClick={onSavePrompts} disabled={apSaving}>
                  {apSaving ? "Saving…" : "Save prompts"}
                </button>
                {apSaved && <span className="triage-hint ok">Saved.</span>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
