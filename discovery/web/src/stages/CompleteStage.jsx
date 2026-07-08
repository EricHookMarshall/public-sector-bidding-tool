// Stage 04 — Complete. Compliance matrix + AI-drafted answer + evidence
// ledger, ported from the approved mockup (skills B02–B04). Illustrative data.
import { MockStage } from "./MockStage.jsx";

const QUESTIONS = [
  ["appr", "Q1", "Social value", true],
  ["review", "Q2", "Technical approach", false],
  ["drafted", "Q3", "Security & data", false],
  ["todo", "Q4", "Pricing schedule", false],
  ["todo", "Q5", "Implementation plan", false],
];

const LEDGER = [
  ["Cyber Essentials Plus", "Certificate (SharePoint)", "EXP 09/26", "var(--warn)"],
  ["ISO 27001 aligned ISMS", "Policy + audit", "OK", "var(--good)"],
  ["UK data residency", "Azure config", "OK", "var(--good)"],
];

export default function CompleteStage({ stage }) {
  return (
    <MockStage stage={stage} addr="bidpath · workspace · NHS GM ICB">
      <div className="ws">
        <div className="qlist">
          <div className="label" style={{ marginBottom: 2 }}>Compliance matrix</div>
          {QUESTIONS.map(([st, qn, label, sel]) => (
            <div className={`qi ${sel ? "sel" : ""}`} key={qn}>
              <div className="qs"><span className={`dotp d-${st}`} /><span className="qn">{qn}</span></div>
              <span style={{ color: "var(--muted)" }}>{label}</span>
            </div>
          ))}
        </div>
        <div className="draft">
          <div className="draft-h">
            <b style={{ fontSize: "12.5px" }}>Q3 — Security &amp; data handling</b>
            <span className="ai-flag">✦ AI-drafted</span>
          </div>
          <div className="draft-body">
            <p>
              FWF operates an ISO 27001-aligned information security management system. All data is
              processed within UK/EU regions under Microsoft Azure, with role-based access control and
              encryption in transit and at rest…
            </p>
            <div className="src-note">
              ◆ Drafted from <b>3 matches</b> in the Approved Answer Bank — 2 from won bids (DHSC, Leeds
              CC). Freshness OK; one certificate expiring.
            </div>
            <div className="ledger">
              <div className="lh"><span>Claim</span><span>Evidence</span><span>Status</span></div>
              {LEDGER.map(([claim, ev, st, color]) => (
                <div className="lr" key={claim}>
                  <span>{claim}</span><span>{ev}</span>
                  <span className="st" style={{ color }}>{st}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </MockStage>
  );
}
