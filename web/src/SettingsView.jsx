// Settings — LLM config. Its own routed view (#settings), outside the 6-stage
// journey. Lets a novice pick provider + model and set the API key without
// hand-editing discovery/.env. The key is write-only: it's saved server-side to
// the git-ignored .env and never sent back here (the screen shows only whether
// one is set + its last 4 chars).
import { useEffect, useState } from "react";
import { getConfig, saveConfig, testConfig, getDayRates, saveDayRates } from "./api.js";

export default function SettingsView() {
  const [cfg, setCfg] = useState(null);
  const [provider, setProvider] = useState("anthropic");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [test, setTest] = useState(null);   // { ok, ... } | { error }

  // Bid day rates (per FOR001 role) — the "cost to chase" inputs.
  const [dr, setDr] = useState(null);        // { roles, rates, default_rate, note }
  const [rates, setRates] = useState({});    // editable {role: £/day}
  const [drSaving, setDrSaving] = useState(false);
  const [drSaved, setDrSaved] = useState(false);

  const load = () =>
    getConfig()
      .then((c) => {
        setCfg(c);
        setProvider(c.provider);
        setModel(c.model);
      })
      .catch((e) => setError(e.message));

  const loadRates = () =>
    getDayRates()
      .then((d) => { setDr(d); setRates(d.rates); })
      .catch((e) => setError(e.message));

  useEffect(() => { load(); loadRates(); }, []);

  const onSaveRates = async () => {
    setDrSaving(true);
    setError(null);
    setDrSaved(false);
    try {
      // Send numbers, not the raw input strings the fields hold.
      const numeric = Object.fromEntries(
        Object.entries(rates).map(([role, v]) => [role, Number(v)]));
      const d = await saveDayRates(numeric);
      setDr(d);
      setRates(d.rates);
      setDrSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setDrSaving(false);
    }
  };

  const onSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    setTest(null);
    try {
      const body = { provider, model };
      if (apiKey.trim()) body.api_key = apiKey.trim();
      const c = await saveConfig(body);
      setCfg(c);
      setApiKey("");           // never keep the secret in the field
      setSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onTest = async () => {
    setTesting(true);
    setTest(null);
    try {
      const r = await testConfig();
      setTest({ ok: true, ...r });
    } catch (e) {
      setTest({ error: e.message });
    } finally {
      setTesting(false);
    }
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

      {cfg && (
        <div className="settings-card">
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
              Stored locally in <code>discovery/.env</code> (never committed). Write-only —
              it isn't sent back to this screen.
            </span>
          </label>

          <div className="settings-actions">
            <button className="run-btn" onClick={onSave} disabled={saving}>
              {saving ? "Saving…" : "Save settings"}
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
            The £/day charged for each bid-writing role. These drive the “cost to
            chase” a bid — sum of effort-days × rate, per FOR001 complexity.
            Default is £{dr.default_rate}/day for every role.
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
  );
}
