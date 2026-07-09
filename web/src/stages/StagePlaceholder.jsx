// Placeholder view for the not-yet-built stages (Triage → Learn). It is an
// honest scaffold, not a fake screen: it shows the approved scope for the
// stage — what the user does, where AI helps, where a human decides, what's
// in vs out of a first version — plus a truthful build-status note. As each
// stage is built for real, swap its `component` in journey.js to a live view.
import { STATE_MAP } from "../journey.js";

export default function StagePlaceholder({ stage }) {
  const { scope, asset, state } = stage;
  return (
    <div className="split">
      <div className="placeholder-main">
        <div className="ph-banner">
          <span className={`st-dot ${STATE_MAP[state][1]}`} />
          <span dangerouslySetInnerHTML={{ __html: asset.txt }} />
        </div>
        <p className="ph-lead">
          Not built yet — this is the agreed scope for the <b>{stage.t}</b> stage,
          carried over from the approved journey mockup. It defines what gets
          built here next.
        </p>
      </div>

      <aside className="scope">
        <div className="scard">
          <div className="scard-h">
            <span className="label">Scope of this stage</span>
            <h3>{stage.t}</h3>
          </div>
          <div className="scard-b">
            <ScopeRow icon="👤" k="What the user does" v={scope.does} />
            <ScopeRow icon="✦" k="Where AI helps" v={scope.ai} />
            <ScopeRow icon="✋" k="Human must decide" v={scope.human} />
          </div>
          <div className="scope-io">
            <div className="in">
              <span className="label">In · v1</span>
              <ul>{scope.inn.map((x) => <li key={x}>{x}</li>)}</ul>
            </div>
            <div className="out">
              <span className="label">Out · later</span>
              <ul>{scope.out.map((x) => <li key={x}>{x}</li>)}</ul>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

// Scope text carries approved inline markup (e.g. <b>Bid</b>), so render as HTML.
function ScopeRow({ icon, k, v }) {
  return (
    <div className="srow">
      <span className="si">{icon}</span>
      <div>
        <div className="sk">{k}</div>
        <div className="sv" dangerouslySetInnerHTML={{ __html: v }} />
      </div>
    </div>
  );
}
