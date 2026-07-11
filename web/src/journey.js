// The six-stage bidding journey — single source of truth for the shell.
// Metadata ported from the approved mockup (docs/design/journey-mockups.html).
// The stepper nav reads from here, so the journey shape lives in one place.
//
// `state` reflects honest build status. All six stages are `live` today (wired
// to bids.db); `design`/`gap` remain in STATE_MAP for any future stage that is
// scoped but not yet built.
//
// `component` names which stage view App.jsx renders for each stage.

export const STAGES = [
  {
    id: "search",
    n: "01",
    t: "Search",
    d: "Find opportunities",
    state: "live",
    stateLabel: "Works today",
    maps: "Discovery engine · Find a Tender + Contracts Finder",
    component: "search",
  },
  {
    id: "triage",
    n: "02",
    t: "Triage",
    d: "Bid or no-bid",
    state: "live",
    stateLabel: "Works today (B01)",
    maps: "Skill B01 — FWF's FOR001 qualification + bid economics",
    component: "triage",
  },
  {
    id: "plan",
    n: "03",
    t: "Plan",
    d: "Which bids, when",
    state: "live",
    stateLabel: "Works today (FOR002)",
    maps: "FOR002 BidPlan + Tender Pipeline — pipeline board + capacity",
    component: "plan",
  },
  {
    id: "complete",
    n: "04",
    t: "Complete",
    d: "Draft the bid",
    state: "live",
    stateLabel: "Works today (FOR006)",
    maps: "FOR006 response matrix + LocalMirror bid library · AI pre-fill",
    component: "complete",
  },
  {
    id: "manage",
    n: "05",
    t: "Manage",
    d: "Clarify & submit",
    state: "live",
    stateLabel: "Works today (FOR003)",
    maps: "FOR003 CQLOG + pre-flight gate · the exact failure that lost G-Cloud 15",
    component: "manage",
  },
  {
    id: "learn",
    n: "06",
    t: "Learn",
    d: "Outcome & library",
    state: "live",
    stateLabel: "Works today (B07)",
    maps: "Skill B07 — outcome + win-rate + library feedback into Stage 4",
    component: "learn",
  },
];

// state slug → stepper pill class
export const STATE_MAP = {
  live: "s-live",
  design: "s-design",
  gap: "s-gap",
};
