# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-08` — **In the definition phase (mockups-first). Journey style approved; architecture
direction set.** Built an interactive 6-stage journey mockup (`docs/design/journey-mockups.html`,
published artifact) — user approved the style and shape. Architecture decided at direction level
(`docs/design/architecture.md`): **local app now** (extend the discovery PoC), **Azure SPA is a
budget-dependent longer-term goal**, SharePoint via a **library-provider seam** (`LocalMirror` now →
`GraphSharePoint` later). HubSpot integration noted as a future feature. Repo: Phase 0 still stands.

## Active task

**Confirm the next definition step.** Candidates: (a) **Data model** — define the shared bid record
that flows across the six stages (Opportunity → Qualified Bid → Answers → Evidence → Clarifications →
Outcome); or (b) **start the local app shell** from the approved mockup (journey nav + stage routing,
extending the discovery front end). Not started — pick with the user first. Working method: mockups-first,
strawman → react.

## Surfaced / parked threads

- **HubSpot integration** — future feature (pipeline ↔ CRM). Noted in `architecture.md`, not scoped.
- **How to get SharePoint data local** (Graph export vs manual vs sample set) — decide at Stage 4.
- **Product name** — "Bidpath" is a placeholder used in the mockup, not a real proposal.
- **FWF strategy docs** still carry `.docx` export artefacts (`knowledge/01–03`) — optional cleanup.

## Open decisions

1. **Next definition step** — data model vs start building the app shell (see Active task).
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
