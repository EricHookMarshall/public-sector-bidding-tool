// Journey shell. Frames the whole bidding journey: a sticky top bar, the
// six-stage stepper nav, and the active stage's view. Stage selection lives
// in the URL hash (e.g. #plan) so stages are deep-linkable and the browser
// back button works — no router dependency needed.
import { useEffect, useState } from "react";
import { STAGES, STATE_MAP } from "./journey.js";
import SearchStage from "./stages/SearchStage.jsx";
import TriageStage from "./stages/TriageStage.jsx";
import PlanStage from "./stages/PlanStage.jsx";
import CompleteStage from "./stages/CompleteStage.jsx";
import ManageStage from "./stages/ManageStage.jsx";
import LearnStage from "./stages/LearnStage.jsx";
import StagePlaceholder from "./stages/StagePlaceholder.jsx";

// Which component renders each stage. Only "search" is live; the rest are
// labelled preview screens (see MockStage) until their stage is built.
const VIEWS = {
  search: SearchStage,
  triage: TriageStage,
  plan: PlanStage,
  complete: CompleteStage,
  manage: ManageStage,
  learn: LearnStage,
};

function stageIndexFromHash() {
  const id = window.location.hash.replace(/^#/, "");
  const i = STAGES.findIndex((s) => s.id === id);
  return i === -1 ? 0 : i;
}

export default function App() {
  const [cur, setCur] = useState(stageIndexFromHash);

  // Keep state in sync with the hash (back/forward, manual edits, deep links).
  useEffect(() => {
    const onHash = () => setCur(stageIndexFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = (i) => {
    const next = Math.max(0, Math.min(STAGES.length - 1, i));
    window.location.hash = STAGES[next].id; // drives the hashchange listener
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Left/right arrows step through the journey (ignore while typing in a field).
  useEffect(() => {
    const onKey = (e) => {
      const t = e.target;
      if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
      if (e.key === "ArrowRight") go(cur + 1);
      if (e.key === "ArrowLeft") go(cur - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cur]);

  const stage = STAGES[cur];
  const StageView = VIEWS[stage.component] || (() => <StagePlaceholder stage={stage} />);

  return (
    <>
      <TopBar />
      <nav className="stepper wrap" aria-label="Journey stages">
        {STAGES.map((s, i) => (
          <button
            key={s.id}
            className="step"
            aria-current={i === cur}
            onClick={() => go(i)}
          >
            <span className="n">{s.n}</span>
            <span className="t">{s.t}</span>
            <span className="d">{s.d}</span>
            <span className={`state ${STATE_MAP[s.state][0]}`}>{s.stateLabel}</span>
          </button>
        ))}
      </nav>

      <div className="wrap">
        <div className="stage-head">
          <h2>
            <span className="badge-n">{stage.n}</span> {stage.t} — {stage.d}
          </h2>
          <div className="maps">
            <b>Maps to:</b> {stage.maps}
          </div>
        </div>

        <main className="stage-body">
          <StageView stage={stage} />
        </main>

        <div className="pager">
          <button onClick={() => go(cur - 1)} disabled={cur === 0}>
            <span className="pl">← Previous</span>
            <span className="pn">
              {cur > 0 ? `${STAGES[cur - 1].n} · ${STAGES[cur - 1].t}` : "First stage"}
            </span>
          </button>
          <button
            className="next"
            onClick={() => go(cur + 1)}
            disabled={cur === STAGES.length - 1}
          >
            <span className="pl">Next →</span>
            <span className="pn">
              {cur < STAGES.length - 1
                ? `${STAGES[cur + 1].n} · ${STAGES[cur + 1].t}`
                : "Last stage"}
            </span>
          </button>
        </div>
      </div>
    </>
  );
}

function TopBar() {
  const toggleTheme = () => {
    const root = document.documentElement;
    const isDark =
      root.getAttribute("data-theme") === "dark" ||
      (!root.getAttribute("data-theme") &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);
    root.setAttribute("data-theme", isDark ? "light" : "dark");
  };

  return (
    <header className="top">
      <div className="wrap top-row">
        <div className="brand">
          <div className="mark">B</div>
          <div>
            <b>Bidpath</b>
            <span>Public sector bidding — working name</span>
          </div>
        </div>
        <div className="top-spacer" />
        <button className="ghost-btn" onClick={toggleTheme} aria-label="Toggle colour theme">
          ◐ Theme
        </button>
      </div>
    </header>
  );
}
