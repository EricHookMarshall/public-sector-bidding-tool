// Framework radar (G2) — its own routed view (#frameworks), outside the journey
// and open to everyone. Which GCA agreements should FWF join? Each candidate is
// scored live against today (act / pursue / prepare / maintain / watch / skip) so
// an expired framework or an open re-entry window shows the moment it changes —
// the antidote to the RM6263 "still listed after it expired" failure. Curated +
// re-verifiable: every card links its GCA source and flags projected dates.
import { useEffect, useState } from "react";
import { getFrameworksRadar } from "./api.js";
import { fmtDate } from "./format.js";

// Recommendation → colour + label. Ordered by urgency in the radar itself.
const REC = {
  act:      { color: "var(--crit)", label: "Act now" },
  pursue:   { color: "var(--good)", label: "Pursue" },
  prepare:  { color: "var(--warn)", label: "Prepare" },
  watch:    { color: "var(--muted)", label: "Watch" },
  maintain: { color: "var(--good)", label: "Maintain" },
  skip:     { color: "var(--faint)", label: "Skip" },
};

const LIFECYCLE = {
  live: "Live", upcoming: "Upcoming", expiring: "Expiring", expired: "Expired", unknown: "TBC",
};

export default function FrameworksView() {
  const [radar, setRadar] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getFrameworksRadar().then(setRadar).catch((e) => setError(e.message));
  }, []);

  // A date, tagged "(projected)" when the agreement flags it as an estimate.
  const dateCell = (a, field, value) =>
    value
      ? `${fmtDate(value)}${(a.projection_dates || []).includes(field) ? " (projected)" : ""}`
      : "—";

  return (
    <div className="wrap frameworks">
      <div className="settings-head">
        <button className="link" onClick={() => { window.location.hash = "search"; }}>
          ← Back to journey
        </button>
        <h2>📡 Framework radar</h2>
      </div>
      <p className="stage-sub">
        Which public-sector agreements FWF should join — scored live against today, so
        an expired framework or an open re-entry window never slips by unnoticed.
      </p>

      {error && <p className="error">⚠ {error}</p>}
      {!radar && !error && <p className="empty">Loading…</p>}

      {radar && (
        <>
          <p className="hint fr-disclaimer">ⓘ {radar.disclaimer}</p>

          {/* Recommendation summary chips */}
          <div className="fr-summary">
            {Object.entries(radar.summary).map(([rec, n]) => (
              <span className="fr-chip" key={rec} style={{ borderColor: REC[rec]?.color }}>
                <b style={{ color: REC[rec]?.color }}>{n}</b> {REC[rec]?.label || rec}
              </span>
            ))}
          </div>

          <div className="fr-list">
            {radar.agreements.map((a) => {
              const rec = REC[a.recommendation] || { color: "var(--muted)", label: a.recommendation };
              const dimmed = a.recommendation === "skip";
              return (
                <article className={`settings-card fr-card${dimmed ? " fr-dim" : ""}`} key={a.id}
                  style={{ borderLeft: `3px solid ${rec.color}` }}>
                  <div className="fr-top">
                    <div>
                      <h4>{a.name} <span className="fr-code">{a.id}</span></h4>
                      <span className="fr-cat">{a.category} · {LIFECYCLE[a.lifecycle] || a.lifecycle}</span>
                    </div>
                    <span className="fr-rec" style={{ background: rec.color }}>{rec.label}</span>
                  </div>

                  <p className="fr-fit">{a.fit}</p>

                  <div className="fr-dates">
                    <span><b>Live from:</b> {dateCell(a, "live_from", a.live_from)}</span>
                    <span><b>Expires:</b> {dateCell(a, "expires", a.expires)}</span>
                    {a.entry_window && (
                      <span><b>Entry window:</b> {dateCell(a, "entry_window", a.entry_window.opens)} → {fmtDate(a.entry_window.closes)} ({a.entry_window_state})</span>
                    )}
                  </div>

                  <ul className="fr-reasons">
                    {a.reasons.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>

                  <div className="fr-foot">
                    <span className="fr-member">{
                      a.fwf_status === "member" ? "FWF: member" :
                      a.fwf_status === "not_member" ? "FWF: not a member" : "FWF: membership TBC"
                    }</span>
                    <a className="link" href={a.source.url} target="_blank" rel="noreferrer">{a.source.label} ↗</a>
                  </div>
                </article>
              );
            })}
          </div>

          <p className="supply-verified">Scored as at {radar.as_of} · facts verified {radar.verified} — re-check the linked GCA pages before acting.</p>
        </>
      )}
    </div>
  );
}
