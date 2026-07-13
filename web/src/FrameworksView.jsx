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

// FWF's own position, from the bid library. The ladder deliberately stops at "response
// drafted": a folder proves work, never membership or submission (see
// src/framework_positions.py). Don't add a "Member" label here — it isn't knowable.
const POSITION = {
  planned: "Planned (empty folder)",
  preparing: "Preparing",
  response_drafted: "Response drafted",
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

                  {/* What the bid library says we're ACTUALLY doing. When that contradicts
                      the curated status (radar: "prepare for G-Cloud 15" / library: a
                      drafted response), say so loudly — a prioritiser that tells you to
                      start what you've half-finished is worse than useless. */}
                  {a.our_position && (
                    <p className={`fr-position${a.contradicts_radar ? " fr-position-warn" : ""}`}>
                      {a.contradicts_radar && <b>⚠ Already in flight — </b>}
                      Bid library: <b>{POSITION[a.our_position.status] || a.our_position.status}</b>
                      {" · "}{a.our_position.file_count} files
                      {a.our_position.last_activity && ` · last touched ${fmtDate(a.our_position.last_activity)}`}
                    </p>
                  )}

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

          {/* Agreements FWF is actually working on that the curated radar has never heard
              of — Bluelight, DDaT-NSW, KCC, the DPSs. Without this the radar quietly
              understates what's already in flight. */}
          {radar.not_on_radar?.length > 0 && (
            <section className="fr-offradar">
              <h3>Also in flight — not on the radar</h3>
              <p className="muted">
                From FWF's bid library. These aren't in the curated GCA list, so the radar
                doesn't score them — but work exists.
              </p>
              <ul className="fr-offradar-list">
                {radar.not_on_radar.map((p) => (
                  <li key={p.name}>
                    <span className={`fr-pos-badge fr-pos-${p.status}`}>
                      {POSITION[p.status] || p.status}
                    </span>
                    <b>{p.name}</b>
                    <span className="fr-cat"> {p.kind}{p.agreement_id ? ` · ${p.agreement_id}` : ""}</span>
                    <span className="muted">
                      {" "}· {p.file_count} files
                      {p.last_activity ? ` · last touched ${fmtDate(p.last_activity)}` : " · no activity yet"}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {radar.positions_caveat && (
            <p className="supply-verified">{radar.positions_caveat}</p>
          )}
          <p className="supply-verified">Scored as at {radar.as_of} · facts verified {radar.verified} — re-check the linked GCA pages before acting.</p>
        </>
      )}
    </div>
  );
}
