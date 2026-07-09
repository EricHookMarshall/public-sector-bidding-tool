# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-09` (session 3) — **Triage (B01) live, with AI pre-fill.** Stage 2 of the journey went
from mock screen to a real FOR001 qualification form wired to `bids.db`, and — the session's
bigger addition — an AI drafting layer that pre-fills the whole form from a notice, behind a
provider-agnostic seam (Anthropic today, Azure OpenAI later per the client's stated need) with a
novice-friendly Settings screen (`#settings`) to manage the model/key. This was **live-verified
with a real Anthropic key** the user added during the session: a real 8-token connection test and
a real AI draft on a stored opportunity both succeeded, with the draft correctly reasoning about
FWF's EFS/framework weaknesses. Detail lives in `discovery/_session/handover.md` (its own
sub-spine); this file tracks the cross-cutting picture.

## Active task

**Continue the journey build-out — Plan (Stage 3) recommended next.** `docs/design/data-model.md`
§3 (`BidPlan`: pipeline position from `Tender Pipeline.xlsx` + the FOR002 phase timeline) is fully
specified, and it's flagged in the app itself as "the highest-value missing piece" — it directly
answers the missed-deadline failure that killed the G-Cloud 15 bid. No hard blocker either way;
Complete (FOR006) is the alternative if the AI-drafting pattern built this session is worth
extending there first instead.

Still parked, unchanged: **user hasn't yet reviewed the running shell in a browser** — 3 sessions
now, and there are two new UI surfaces (the real Triage form, the Settings screen) worth a look
before more gets built on top of unreviewed UI.

## Surfaced / parked threads

- **HubSpot integration** — future feature (pipeline ↔ CRM). Noted in `architecture.md`, not scoped.
- **SharePoint data path for `LibraryItem`** — parked to the Complete stage build, per data-model.md.
- **Azure OpenAI provider** — the client will need the AI drafting layer on Azure OpenAI, not just
  Anthropic. The seam for this is built (`discovery/llm.py`) and the swap point is documented
  in-file as a ready-to-fill skeleton; implementation is deferred until Azure access is provisioned
  outside the session (mirrors the SharePoint/MS-Graph blocker pattern).
- **Product name** — "Bidpath" is a placeholder used in the mockup, not a real proposal.
- **FWF strategy docs** still carry `.docx` export artefacts (`knowledge/01–03`) — optional cleanup.

## Open decisions

1. **Which stage next** — Plan vs. extending Complete/AI further. Recommend Plan per the app's own
   "highest-value missing piece" flag; no hard blocker.
2. **Azure OpenAI timing** — build when Azure access is provisioned; not before.

Settled this session: **Triage (B01) wired to real data**, including FWF's real FOR001
go/no-go scoring rig; **AI pre-fill built** for Triage, provider-agnostic, defaulting to
`claude-haiku-4-5` for cost (a deliberate tradeoff — this is a review-before-save drafting task,
not deep reasoning); **storage for bid-lifecycle tables resolved** — extended `bids.db` in place,
not a separate store (the last open item from `data-model.md`).

Settled earlier, unchanged: mockups-first method; six-stage journey shape + visual style approved;
local app now, Azure SPA later; library-provider seam for SharePoint; AI drives task completion;
stack = FastAPI + SQLite + React/Vite; shared bid record shape derived from FWF's real bid store
(`docs/design/data-model.md`) — Opportunity → Qualification/Bid → BidPlan → ResponseItem/LibraryItem
→ Clarification/ComplianceCheck → Outcome. Facts verified in `knowledge/VERIFIED_FACTS.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. If picking up discovery-code work: also read `discovery/CLAUDE.md` and
   `discovery/_session/handover.md` — it has full file-level detail on Triage + AI pre-fill.
3. Confirm repo state: `git -C .. status` and `git -C .. log --oneline -3`.
4. `discovery/.env` already holds a real (gitignored) Anthropic key from this session — AI
   drafting and the Settings screen's Test connection should work live without setup.

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`).
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
