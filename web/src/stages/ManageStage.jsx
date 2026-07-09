// Stage 05 — Manage. Clarification register + pre-flight gate, ported from the
// approved mockup (skills B05–B06). This encodes the exact failure that lost
// G-Cloud 15: a missed clarification is fatal. Illustrative data.
import { MockStage } from "./MockStage.jsx";

const CHECKS = [
  [true, "All mandatory questions answered & approved", "5 / 5"],
  [true, "Arobs parent company guarantee attached", "Schedule 5"],
  [false, "Carbon Reduction Plan — in date", "Expired 06/26"],
  [true, "Deadline captured with time + timezone", "14 Aug 17:00"],
];

export default function ManageStage({ stage }) {
  return (
    <MockStage stage={stage} addr="bidpath · clarifications & preflight">
      <div className="label">Clarification register — the step the last bid missed</div>
      <div className="reg">
        <div className="reg-row h"><span>Question / buyer</span><span>Owner</span><span>Buyer deadline</span><span>Status</span></div>
        <div className="reg-row">
          <span className="q">Confirm parent guarantee wording<div className="sub">via portal · NHS GM</div></span>
          <span>EH <span className="sub">/ KS backup</span></span>
          <span className="mono">14 Aug 17:00 BST</span>
          <span><span className="st-pill p-unk">Drafting</span></span>
        </div>
        <div className="reg-row" style={{ background: "var(--crit-soft)" }}>
          <span className="q">Provide 3 years’ accounts<div className="sub">via email · Home Office</div></span>
          <span>— <span className="sub">unassigned</span></span>
          <span className="mono" style={{ color: "var(--crit)" }}>Tomorrow 12:00</span>
          <span><span className="st-pill p-fail">Overdue soon</span></span>
        </div>
      </div>
      <div className="label" style={{ marginTop: 4 }}>Pre-flight — submission gate</div>
      <div className="checklist">
        {CHECKS.map(([ok, txt, note]) => (
          <div className={`ck ${ok ? "ok" : "no"}`} key={txt}>
            <span className="box">{ok ? "✓" : "!"}</span>
            <span>{txt}</span>
            <span className="cnote">{note}</span>
          </div>
        ))}
      </div>
    </MockStage>
  );
}
