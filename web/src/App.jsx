// Journey shell. Frames the whole bidding journey: a sticky top bar, the
// six-stage stepper nav, and the active stage's view. Stage selection lives
// in the URL hash (e.g. #plan) so stages are deep-linkable and the browser
// back button works — no router dependency needed.
import { useEffect, useState } from "react";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { isAadConfigured, apiScopes } from "./authConfig.js";
import { getAuthMe } from "./api.js";
import { STAGES, STATE_MAP } from "./journey.js";
import SearchStage from "./stages/SearchStage.jsx";
import TriageStage from "./stages/TriageStage.jsx";
import PlanStage from "./stages/PlanStage.jsx";
import CompleteStage from "./stages/CompleteStage.jsx";
import ManageStage from "./stages/ManageStage.jsx";
import LearnStage from "./stages/LearnStage.jsx";
import SettingsView from "./SettingsView.jsx";

// Which component renders each stage. All six stages are live, wired to bids.db.
const VIEWS = {
  search: SearchStage,
  triage: TriageStage,
  plan: PlanStage,
  complete: CompleteStage,
  manage: ManageStage,
  learn: LearnStage,
};

function hashId() {
  return window.location.hash.replace(/^#/, "");
}

function stageIndexFromHash() {
  const i = STAGES.findIndex((s) => s.id === hashId());
  return i === -1 ? 0 : i;
}

export default function App() {
  const [cur, setCur] = useState(stageIndexFromHash);
  // "settings" is a route outside the 6-stage journey (its own #settings view).
  const [route, setRoute] = useState(() => (hashId() === "settings" ? "settings" : "journey"));

  // Keep state in sync with the hash (back/forward, manual edits, deep links).
  useEffect(() => {
    const onHash = () => {
      setRoute(hashId() === "settings" ? "settings" : "journey");
      setCur(stageIndexFromHash());
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = (i) => {
    const next = Math.max(0, Math.min(STAGES.length - 1, i));
    window.location.hash = STAGES[next].id; // drives the hashchange listener
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Left/right arrows step through the journey (ignore while typing in a field,
  // and while on the Settings view — arrows there shouldn't jump to a stage).
  useEffect(() => {
    const onKey = (e) => {
      if (hashId() === "settings") return;
      const t = e.target;
      if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
      if (e.key === "ArrowRight") go(cur + 1);
      if (e.key === "ArrowLeft") go(cur - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cur]);

  // Entra sign-in gate (Phase C). The msal-react hooks are safe to call even
  // when the app isn't wrapped in an MsalProvider (default context → false), so
  // when Entra isn't configured (local dev) isAuthenticated stays false and the
  // gate below is skipped via isAadConfigured. When it IS configured, an
  // unauthenticated visitor sees the sign-in screen before any stage renders.
  const isAuthenticated = useIsAuthenticated();
  const { instance } = useMsal();

  // The signed-in caller's role, so the UI can hide the Admin-only Settings gear.
  // The API enforces the gate regardless (defence in depth) — this is presentation
  // only. null while loading; fetched once auth is settled (or immediately in
  // local/bypass dev, where auth isn't configured).
  const [role, setRole] = useState(null);
  const authReady = !isAadConfigured || isAuthenticated;
  useEffect(() => {
    if (!authReady) return;
    let live = true;
    getAuthMe()
      .then((me) => live && setRole(me.role))
      .catch(() => live && setRole(null));
    return () => { live = false; };
  }, [authReady]);
  const isAdmin = role === "Admin";

  const stage = STAGES[cur];
  // Every journey stage maps to a live view; the fallback only guards against a
  // mistyped `component` slug in journey.js — it should never render in practice.
  const StageView =
    VIEWS[stage.component] || (() => <p>Stage “{stage.component}” has no view.</p>);

  if (isAadConfigured && !isAuthenticated) {
    return <SignInScreen onSignIn={() => instance.loginRedirect({ scopes: apiScopes })} />;
  }

  // Settings is Admin-only. A non-Admin who deep-links #settings falls through to
  // the journey (gear hidden anyway). Only enter Settings once we know the caller
  // is an Admin — so an Admin reload on #settings still lands there after the role
  // resolves.
  if (route === "settings" && isAdmin) {
    return (
      <>
        <TopBar isAdmin={isAdmin} />
        <SettingsView />
      </>
    );
  }

  return (
    <>
      <TopBar isAdmin={isAdmin} />
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
            <span className={`state ${STATE_MAP[s.state]}`}>{s.stateLabel}</span>
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

// Shown when Entra is configured but the visitor isn't signed in yet. A single
// full-page redirect to Microsoft; on return, MSAL has an account and the gate
// opens. Deliberately minimal — the journey shell renders only post-auth.
function SignInScreen({ onSignIn }) {
  return (
    <>
      <TopBar />
      <div className="wrap" style={{ maxWidth: 480, marginTop: "4rem", textAlign: "center" }}>
        <h2>Sign in to continue</h2>
        <p style={{ color: "var(--muted, #666)", margin: "0.75rem 0 1.5rem" }}>
          This tool is protected by your organisation's Microsoft account.
        </p>
        <button className="next" onClick={onSignIn}>
          Sign in with Microsoft
        </button>
      </div>
    </>
  );
}

// The signed-in user's name + a sign-out button, shown only when Entra is
// configured. Reads MSAL directly (hooks are provider-safe); renders nothing
// in local/unauthenticated dev.
function UserChip() {
  const isAuthenticated = useIsAuthenticated();
  const { instance } = useMsal();
  if (!isAadConfigured || !isAuthenticated) return null;
  const account = instance.getActiveAccount() ?? instance.getAllAccounts()[0];
  const name = account?.name || account?.username || "Signed in";
  return (
    <>
      <span className="user-chip" title={account?.username || ""}>{name}</span>
      <button
        className="ghost-btn"
        onClick={() => instance.logoutRedirect()}
        aria-label="Sign out"
      >
        Sign out
      </button>
    </>
  );
}

function TopBar({ isAdmin = false }) {
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
        {isAdmin && (
          <button
            className="ghost-btn"
            onClick={() => { window.location.hash = "settings"; }}
            aria-label="Settings"
          >
            ⚙ Settings
          </button>
        )}
        <button className="ghost-btn" onClick={toggleTheme} aria-label="Toggle colour theme">
          ◐ Theme
        </button>
        <UserChip />
      </div>
    </header>
  );
}
