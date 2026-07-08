# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-09` — **App shell built.** User chose definition step (b) — start the local app shell — and
it's done: the discovery front end is now the shell of the full 6-stage journey (top bar + stepper nav
+ hash routing + light/dark theme), extending the discovery PoC per `docs/design/architecture.md`
(not a separate app). **Search** is the one live, wired stage; **Triage/Plan/Complete/Manage/Learn**
are labelled illustrative preview screens carrying the approved mockup's content, awaiting real data.
All new code lives under `discovery/web/` — see `discovery/_session/handover.md` for the file-level
detail. Builds clean (38 modules, no errors); backend+dev-server data plumbing curl-verified; **not
yet reviewed in a browser** (no browser tool this environment). Phase 1 (search → triage) now has a UI
skeleton. Foundational architecture direction unchanged: local app now, Azure SPA later, SharePoint via
the `LocalMirror → GraphSharePoint` seam; HubSpot a future feature.

## Active task

**User to review the running shell** (`cd discovery && uvicorn api:app --port 8000` + `cd web && npm
run dev` → <http://localhost:5173>) — click through all 6 stages + theme toggle, flag anything wrong.
Then the next real build step is **(a) the data model** — the shared bid record across the six stages
(Opportunity → Qualified Bid → Answers → Evidence → Clarifications → Outcome) — which is now the
concrete blocker for wiring Triage/Plan/etc. to real records instead of the illustrative mock data.

## Surfaced / parked threads

- **HubSpot integration** — future feature (pipeline ↔ CRM). Noted in `architecture.md`, not scoped.
- **How to get SharePoint data local** (Graph export vs manual vs sample set) — decide at Stage 4.
- **Product name** — "Bidpath" is a placeholder used in the mockup, not a real proposal.
- **FWF strategy docs** still carry `.docx` export artefacts (`knowledge/01–03`) — optional cleanup.

## Open decisions

1. **Data model** — the shared bid record across the six stages. Now the concrete next build step and
   the blocker for wiring the mock stages to real data. (Was "data model vs app shell"; the shell is
   built, so this is what's left.)
2. **SharePoint data path** — how `LocalMirror` gets seeded (parked to Stage 4).

Settled: mockups-first method; six-stage journey shape + visual style approved; **local app now, Azure
SPA later**; library-provider seam for SharePoint; AI drives task completion; stack = FastAPI + SQLite +
React/Vite (extend discovery). Facts verified in `knowledge/VERIFIED_FACTS.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. Skim the design so far: [`docs/design/journey-mockups.html`](../docs/design/journey-mockups.html) + [`docs/design/architecture.md`](../docs/design/architecture.md).
3. Confirm repo state: `git -C .. status` and `git -C .. log --oneline -3`.

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`).
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
