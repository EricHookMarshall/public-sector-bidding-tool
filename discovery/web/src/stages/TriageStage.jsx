// Stage 02 — Triage. Qualification gates + bid economics, ported from the
// approved mockup (skill B01). Illustrative data.
import { MockStage } from "./MockStage.jsx";

const GATES = [
  ["fail", "Fails", "Economic & financial standing (EFS)", "FWF standalone accounts fall short — needs the Arobs parent company guarantee attached"],
  ["pass", "Pass", "Capability & framework fit", "Microsoft Practice maps to Cloud Support; deliverable by Romanian delivery team"],
  ["unk", "Unknown", "Bid capacity by deadline", "No owner assigned yet — who writes & reviews before 14 Aug?"],
  ["pass", "Pass", "Evidence availability", "Case studies + Cyber Essentials on file; social value evidence thin"],
];

const ECON = [
  ["Est. effort", "6.5", "person-days"],
  ["Contract value", "£250k+", "over 48 months"],
  ["Win probability", "45%", "manual estimate"],
];

export default function TriageStage({ stage }) {
  return (
    <MockStage stage={stage} addr="bidpath · triage · NHS GM ICB">
      <div className="label">Qualification gates — unknown blocks, it never passes by omission</div>
      <div className="gates">
        {GATES.map(([kind, pill, title, note]) => (
          <div className="gate" key={title}>
            <span className={`pill ${kind === "pass" ? "p-pass" : kind === "fail" ? "p-fail" : "p-unk"}`}>{pill}</span>
            <div className="g-txt"><b>{title}</b> <span className="g-note">— {note}</span></div>
          </div>
        ))}
      </div>
      <div className="label" style={{ marginTop: 4 }}>Bid economics</div>
      <div className="econ">
        {ECON.map(([k, v, u]) => (
          <div className="stat" key={k}>
            <div className="k">{k}</div><div className="v">{v}</div><div className="u">{u}</div>
          </div>
        ))}
      </div>
      <div className="decide">
        <button className="mini-btn">▲ Recommend BID</button>
        <button className="mini-btn ghost">No-bid</button>
        <button className="mini-btn tonal">Needs review</button>
      </div>
    </MockStage>
  );
}
