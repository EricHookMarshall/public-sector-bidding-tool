// Stage 06 — Learn. Outcome capture + suggested library updates that feed back
// into Stage 4, ported from the approved mockup (skill B07). Illustrative data.
import { MockStage } from "./MockStage.jsx";

const ACTIONS = [
  ["up", "Promote 4 answers to the Approved Answer Bank", "Technical approach & social value scored highest — reuse them"],
  ["ref", "Refresh 2 evidence items", "Cyber Essentials + insurance certificates expire within 90 days"],
  ["down", "Retire 1 answer — do not reuse", "Pricing narrative the evaluator flagged as unclear"],
];

const GLYPH = { up: "▲", down: "▼", ref: "↻" };

export default function LearnStage({ stage }) {
  return (
    <MockStage stage={stage} addr="bidpath · outcome · DHSC M365">
      <div className="outcome-head">
        <span className="res">● Won</span>
        <span style={{ fontSize: "12.5px", color: "var(--muted)" }}>
          DHSC — M365 rollout · scored <b>88 / 100</b> · “strong technical response, clear social value”
        </span>
      </div>
      <div className="label" style={{ marginTop: 4 }}>Suggested library updates — you approve each</div>
      <div className="actions-l">
        {ACTIONS.map(([kind, t, s]) => (
          <div className="lib-act" key={t}>
            <span className={`ic ic-${kind}`}>{GLYPH[kind]}</span>
            <div><div className="la-t">{t}</div><div className="la-s">{s}</div></div>
          </div>
        ))}
      </div>
      <div className="src-note" style={{ background: "var(--accent-soft)", borderColor: "transparent", color: "var(--accent)" }}>
        ◆ Approved updates flow straight into Stage 4, so the next bid drafts from better material.
      </div>
    </MockStage>
  );
}
