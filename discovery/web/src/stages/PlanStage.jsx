// Stage 03 — Plan. Pipeline board + team capacity, ported from the approved
// mockup. This is the highest-value new piece (nothing exists yet).
// Illustrative data.
import { MockStage } from "./MockStage.jsx";

const COLUMNS = [
  { h: "Qualifying", cards: [
    ["draft", "Leeds CC — Power Platform", "KS", "22d", "£120k"],
    ["risk", "Home Office — Copilot PoV", "—", "8d", "£90k"],
  ]},
  { h: "Drafting", cards: [
    ["draft", "NHS GM — Cloud support", "EH", "37d", "£250k"],
  ]},
  { h: "In review", cards: [
    ["go", "DHSC — M365 rollout", "EH", "12d", "£180k"],
  ]},
  { h: "Submitted", cards: [
    ["go", "Gov Digital — Azure AI", "KS", "—", "£210k"],
  ]},
];

function KCard({ t, ttl, who, dl, val }) {
  const dlStyle = dl === "8d" ? { color: "var(--crit)", fontWeight: 700 }
    : dl === "12d" || dl === "22d" ? { color: "var(--warn)" } : undefined;
  return (
    <div className={`kcard t-${t}`}>
      <div className="kt">{ttl}</div>
      <div className="km">
        {who === "—"
          ? <span className="who" style={{ background: "var(--crit-soft)", color: "var(--crit)" }}>?</span>
          : <span className="who">{who}</span>}
        <span className="tag val">{val}</span>
        {dl !== "—" && <span className="mono" style={dlStyle}>{dl}</span>}
      </div>
    </div>
  );
}

export default function PlanStage({ stage }) {
  return (
    <MockStage stage={stage} addr="bidpath · pipeline">
      <div className="alert-strip">
        ⚠ 2 clarification deadlines this week · Home Office closes in 8 days and has no writer assigned
      </div>
      <div className="board">
        {COLUMNS.map((col) => (
          <div className="col" key={col.h}>
            <div className="col-h"><span>{col.h}</span><span className="c">{col.cards.length}</span></div>
            {col.cards.map((c) => <KCard key={c[1]} t={c[0]} ttl={c[1]} who={c[2]} dl={c[3]} val={c[4]} />)}
          </div>
        ))}
      </div>
      <div className="cap">
        <div className="col-h" style={{ margin: 0 }}>
          <span>Team capacity — next 3 weeks</span><span className="c">18.5 / 15 days</span>
        </div>
        <div className="bar over"><i style={{ width: "100%" }} /></div>
        <div style={{ fontSize: "11.5px", color: "var(--faint)", marginTop: 6 }}>
          Over-committed by 3.5 days — something has to give. Drop Home Office, or find a writer.
        </div>
      </div>
    </MockStage>
  );
}
