// How to Supply (G3) — its own routed view (#supply), outside the 6-stage
// journey and open to everyone. A novice-facing reference on the UK public-sector
// routes to market: what a Framework / Dynamic Market / DPS / Catalogue is, how to
// find opportunities, and a getting-started path. Content is curated + read-only
// (served from supply_reference.py) with a verified date and source links so it
// stays honestly re-verifiable — which agreements FWF should actually pursue is a
// separate (G2) job and deliberately not here.
import { useEffect, useState } from "react";
import { getSupplyReference } from "./api.js";

export default function SupplyGuideView() {
  const [ref, setRef] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getSupplyReference().then(setRef).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="wrap supply-guide">
      <div className="settings-head">
        <button className="link" onClick={() => { window.location.hash = "search"; }}>
          ← Back to journey
        </button>
        <h2>📘 How to supply</h2>
      </div>
      <p className="stage-sub">
        The routes to market for UK public-sector work — how buyers buy, and how you
        get in front of them. Written for someone new to bidding.
      </p>

      {error && <p className="error">⚠ {error}</p>}
      {!ref && !error && <p className="empty">Loading…</p>}

      {ref && (
        <>
          <p className="hint supply-disclaimer">ⓘ {ref.disclaimer}</p>

          {/* Getting started — the novice on-ramp, numbered */}
          <section className="settings-card supply-card">
            <h3 className="settings-section">Getting started</h3>
            <ol className="supply-steps">
              {ref.getting_started.map((step, i) => <li key={i}>{step}</li>)}
            </ol>
          </section>

          {/* The routes to market */}
          <h3 className="supply-routes-head">Routes to market</h3>
          <div className="supply-routes">
            {ref.routes.map((r) => (
              <article className="settings-card supply-route" key={r.id}>
                <h4>{r.title}</h4>
                <p className="supply-summary">{r.summary}</p>
                <ul className="supply-points">
                  {r.key_points.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
                {r.example && (
                  <p className="supply-example"><b>Example:</b> {r.example}</p>
                )}
                <a className="link supply-src" href={r.source.url} target="_blank" rel="noreferrer">
                  {r.source.label} ↗
                </a>
              </article>
            ))}
          </div>

          {/* Help resources */}
          <section className="settings-card supply-card">
            <h3 className="settings-section">Help &amp; where to register</h3>
            <ul className="supply-links">
              {ref.help_links.map((l) => (
                <li key={l.url}>
                  <a className="link" href={l.url} target="_blank" rel="noreferrer">{l.label} ↗</a>
                </li>
              ))}
            </ul>
          </section>

          <p className="supply-verified">Facts verified as at {ref.verified} — re-check the linked sources before relying on a specific agreement.</p>
        </>
      )}
    </div>
  );
}
