// The six-stage bidding journey — single source of truth for the shell.
// Metadata + scope content ported from the approved mockup
// (docs/design/journey-mockups.html). The stepper nav and the stage
// placeholders both read from here, so the journey shape lives in one place.
//
// `state` reflects honest build status, not aspiration:
//   live   — works today (the discovery engine)
//   design — designed as a skill (B0x) but not yet wired to a real record
//   gap    — nothing exists yet
//
// `component` names which stage view to render. Only "search" is real; the
// rest render the scoped placeholder until their stage is built.

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
    scope: {
      does: "Search live government sources in one place and filter to what's genuinely relevant — by keyword, CPV code, buyer, region, value and how soon it closes.",
      ai: "Suggests which CPV codes and keywords match FWF's Microsoft Practice, and flags notices that look relevant even when the wording differs.",
      human: "Decides which opportunities are worth a closer look and sends them to Triage.",
      inn: [
        "Find a Tender + Contracts Finder",
        "Filter: CPV, region, value, deadline",
        "Keyword search + source badges",
        "Export / “Consider” handoff",
      ],
      out: [
        "Scotland / Wales / TED sources",
        "Saved searches & email alerts",
        "Auto bid/no-bid (that's Triage)",
      ],
    },
    asset: {
      state: "live",
      txt: "<b>Exists and works</b> — the discovery PoC (FastAPI + SQLite + React) already pulls, normalises and filters these two sources.",
    },
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
    scope: {
      does: "Runs a consistent bid/no-bid check on one opportunity: hard gates first (knockouts), then a weighted score and a plain effort-vs-value-vs-win view.",
      ai: "Pre-fills each gate from the notice + FWF's profile, and drafts the rationale — e.g. spotting the EFS gap and prompting for the Arobs PCG.",
      human: "Makes the actual call — <b>Bid</b>, <b>No-bid</b>, or <b>Needs review</b> — and assigns an owner. Any <b>Unknown</b> blocks a clean “bid”.",
      inn: [
        "Gate checklist w/ pass/fail/unknown",
        "EFS + PCG prompt baked in",
        "Effort vs value vs win-probability",
        "Decision + owner captured",
      ],
      out: [
        "Trained win-probability model",
        "Auto-pricing",
        "Full commercial sign-off flow",
      ],
    },
    asset: {
      state: "live",
      txt: "<b>Wired to real data + AI pre-fill</b> — pick a stored opportunity, let AI draft the FOR001 qualification from the notice (RAG gates, complexity, go/no-go rationale) for review, then a Go promotes it into a bid. Provider-agnostic (Anthropic now, Azure OpenAI later); needs an API key set in <code>discovery/.env</code>.",
    },
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
    scope: {
      does: "Shows every live bid on one board with its stage, owner, deadline and effort — plus whether the team actually has the days to deliver what's committed.",
      ai: "Estimates effort per bid, forecasts clashes, and surfaces the “this deadline will be missed” warning before it happens.",
      human: "Decides sequencing and trade-offs — which bids to commit to, which to drop, who owns each, when work starts.",
      inn: [
        "Pipeline board by stage",
        "Deadline + owner + effort per bid",
        "Capacity vs commitment view",
        "Deadline / clarification alerts",
      ],
      out: [
        "Automatic resource levelling",
        "Timesheet integration",
        "Revenue forecasting",
      ],
    },
    asset: {
      state: "live",
      txt: "<b>Wired to real data</b> — every bid promoted by a Triage “Go” lands on a live pipeline board reading <code>bids.db</code>: pipeline column, owner, both deadlines (days remaining) and the FOR001 “cost to chase”. The capacity bar sums committed effort against the team’s days, and the alerts fire on the real clarification/submission deadlines. Click a bid for its FOR002 phase timeline.",
    },
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
    scope: {
      does: "Turns the tender into a tracked question list, then drafts each answer with the evidence to back every claim — so the writer edits rather than starts from a blank page.",
      ai: "Retrieves the best past answers + evidence from the SharePoint library and drafts a first response mapped to what the evaluator scores; builds the evidence ledger.",
      human: "Rewrites, adds the win themes, and <b>approves</b> each answer. Nothing is submitted as-is; nothing auto-approves.",
      inn: [
        "Compliance matrix + per-answer status",
        "AI draft from past bids",
        "Evidence ledger (claim → proof → expiry)",
        "Stale-term & unsupported-claim checks",
      ],
      out: [
        "Live SharePoint (blocked on MS Graph)",
        "Full document assembly / export",
        "In-portal form filling",
      ],
    },
    asset: {
      state: "live",
      txt: "<b>Wired to real data</b> — every bid gets its FOR006 compliance matrix (one row per tender question) reading <code>bids.db</code>, seeded from FWF's real question master. AI drafts each answer from the actual bid library through the <code>LocalMirror</code> provider seam (the gitignored export), grounded in retrieved evidence and citing what it drew on; a live word-count check enforces the tender limit, and the evidence ledger surfaces any expired credential. Live SharePoint drops in behind the same seam later — no app changes. Needs an API key in <code>discovery/.env</code> for AI drafting.",
    },
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
    scope: {
      does: "Tracks every buyer clarification with an owner, a backup and a real deadline (date, time, timezone) — then runs a pre-flight gate before anyone submits.",
      ai: "Watches deadlines, drafts clarification responses from the library, and blocks submission when a mandatory item is missing or a document has expired.",
      human: "Owns each clarification, approves responses, and makes the final call to submit. The buyer's portal submission stays a human action.",
      inn: [
        "Clarification register w/ time + tz + escalation",
        "Backup owner on every item",
        "Pre-flight blocking checklist",
        "Expiry checks on documents",
      ],
      out: [
        "Live portal / mailbox integration",
        "Auto-submitting to the buyer",
        "Reminder scheduling off flight/award dates",
      ],
    },
    asset: {
      state: "live",
      txt: "<b>Wired to real data</b> — every live bid shows its FOR003 clarification register (owner, backup, buyer deadline captured <i>with time + timezone</i>) reading <code>bids.db</code>, and the alerts fire on the real clarification deadlines. A pre-flight gate blocks “submitted” until every mandatory item passes — auto-checking that clarifications are resolved and that no credential has expired. Nothing auto-submits.",
    },
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
    scope: {
      does: "Captures how the bid actually did — won/lost, evaluator score, feedback — and turns that into concrete improvements to the reusable library.",
      ai: "Reads the feedback and proposes what to promote, retire or refresh, so good content compounds and weak content is flagged before it's reused.",
      human: "Approves each library change. Nothing gets marked “reusable” without a person confirming it.",
      inn: [
        "Outcome + score + feedback capture",
        "Promote / retire / refresh suggestions",
        "Closes the loop into Stage 4",
        "Evidence expiry surfaced",
      ],
      out: [
        "Cross-bid analytics dashboards",
        "Automated win/loss reporting",
        "Pricing intelligence model",
      ],
    },
    asset: {
      state: "live",
      txt: "<b>Wired to real data</b> — every bid reads <code>bids.db</code> for its outcome (won / not won / withdrawn, evaluator score, feedback) and Lessons Learned. The win rate is tracked bid-by-bid, and each result derives promote / refresh / retire suggestions for the library that you approve. Applying approved updates to the real library needs the SharePoint connection Stage 4 is blocked on — the tool proposes and records sign-off; it never writes the library itself.",
    },
  },
];

// state slug → [stepper pill class, asset dot class]
export const STATE_MAP = {
  live: ["s-live", "dot-live"],
  design: ["s-design", "dot-design"],
  gap: ["s-gap", "dot-gap"],
};
