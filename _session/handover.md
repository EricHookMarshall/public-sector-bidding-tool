# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-09` (session 6) — **Manage (Stage 5) is built, wired to `bids.db`, and live-verified.**
The app now runs through **Stage 5**. Search (1), Triage (2, +AI +Settings), Plan (3) and now
**Manage (5)** are all real; only **Complete (4)** and **Learn (6)** are still preview screens.
Manage = the FOR003 clarification register + a pre-flight submission gate — the stage that directly
encodes the missed-clarification failure this tool exists to prevent. Built as a close parallel to
Plan: new domain module `src/clarification.py`, new `bid_manage` table, board + reference + detail
endpoints, a real board→detail UI (replacing the mock), and `src/seed_manage_demo.py`.

Verified over **real HTTP**: `bid_manage: 3` after seed (21 opps / 3 quals / 3 bids / 3 plans intact);
`/api/manage/board` 200 with alerts ordered most-urgent-first (a clarification "deadline PASSED 3d
ago" is the founding-failure signal); the pre-flight gate enforces server-side — an expired Cyber
Essentials cert and an unresolved-clarification auto-item both force fails, and `PUT …/manage
{submitted:"yes"}` on a blocked bid returns **409**. `npm run build` compiles clean.

## Active task

**Nothing blocking.** Two real options, same as before but now one stage further:

1. **User browser click-through — now 5 stages built, 0 human-reviewed (the standing thread).**
   Everything (Search, Triage, Settings, Plan, Manage) is verified server-side only. Strongly worth
   a first real browser walk before a 6th surface is built on five unreviewed ones. Spin up:
   `uvicorn api:app --app-dir src --port 8000` + `cd web && npm run dev` → localhost:5173, open
   `#manage`. Demo data is seeded (`python3 src/seed_manage_demo.py`; `--clear` resets).
2. **Build another stage.** Only **Complete (Stage 4, FOR006)** and **Learn (Stage 6, B07)** remain.
   Complete is blocked on live SharePoint/MS Graph (hard rule) so its AI pre-fill can't be
   live-verified the way the others were. **Learn (Stage 6)** has no external blocker and would
   complete the journey loop (outcome capture → library feedback) — the likely next build if not
   pausing for review.

## What shipped

**Manage (Stage 5) — session 6** (`src/clarification.py` new, `src/db.py`, `src/api.py`,
`web/src/api.js`, `web/src/stages/ManageStage.jsx`, `web/src/journey.js`, `web/src/styles.css`,
`src/seed_manage_demo.py` new) — FOR003 CQLOG + pre-flight domain rig (statuses, 9-item checklist
from data-model §5b, `resolve_preflight` enforcing auto + expiry items, `preflight_summary` gate,
`alerts` founding-failure signal), the `bid_manage` table (clarifications + preflight as JSON, like
`bid_plans.phases`), `/api/manage/{reference,board}` + `GET`/`PUT /api/bids/{id}/manage` (the PUT
gates `submitted` server-side → 409 if blocked), and a real board→detail UI. Register captures
owner + **backup** + buyer deadline **with time + timezone**. Full detail in
[progress.md](progress.md) session 6.

**Plan (Stage 3) — session 4** (`src/bidplan.py`, `src/db.py`, `src/api.py`, `web/src/api.js`,
`web/src/stages/PlanStage.jsx`, …, `src/seed_plan_demo.py`) — FOR002 pipeline board + team-capacity +
15-phase timeline + reactive alerts, `bid_plans` table, `/api/plan/*`. Live-verified. (The precedent
Manage was modelled on.)

**Restructure (session 5)** — flat repo: backend `src/`, frontend `web/`, `bids.db`/`.env` beside the
code, one `_session/` triad + one `CLAUDE.md`. App live-verified from the layout.

## Surfaced / parked threads

- **User review of the running shell — 5 sessions outstanding.** Search, Triage (+ Settings),
  Plan and now Manage all real and verified server-side; no browser click-through yet. Five stages
  built, none human-reviewed — worth doing before a 6th surface (Learn/Complete) is added.
- **HubSpot integration** — future feature (pipeline ↔ CRM). Noted in `architecture.md`, not scoped.
- **`web/src/StagePlaceholder.jsx`** — still dead code (superseded by per-stage screens); not deleted.
- **SharePoint data path for `LibraryItem`** — parked to the Complete stage. The concrete reason
  Complete is harder to build next than Manage.
- **Azure OpenAI provider** — skeleton in `src/llm.py`, not implemented. Client requirement;
  build when Azure access is provisioned.
- **Team capacity default (25 days, `src/bidplan.py`)** — a placeholder tuned to demo well, not
  a real FWF number, and not persisted. Should become a real input before it's more than illustrative.

## Open decisions

1. **What next** — pause for the user's browser review (5 stages built, 0 reviewed), or build
   **Learn (Stage 6)** to close the journey loop (no external blocker), or tackle **Complete (Stage 4)**
   despite its SharePoint block. Not decided.
2. **Pre-flight gate recompute cadence** — currently re-checks on *save* (server-authoritative), not
   live per-keystroke. Fine for the PoC; revisit if the UX wants instant gate feedback.
3. **Team capacity as a real input** — currently a hardcoded default overridable only per-request.
4. **Azure OpenAI timing** — build when Azure access is provisioned, not before.

Settled this session: **Manage (Stage 5) built** — FOR003 register + pre-flight gate, wired to
`bids.db`, gate enforced server-side. Modelled on the Plan (Stage 3) pattern.

Settled session 5: **flat repo structure** — backend `src/`, frontend `web/`, one `_session/`
triad + one `CLAUDE.md` at root, no nested sub-app (matches the user's other projects).

Settled earlier, unchanged: Plan (Stage 3) wired to real data; Triage (B01) + AI pre-fill +
Settings; storage extended into `bids.db` in place; mockups-first method; six-stage journey shape
+ visual style approved; local app now, Azure SPA later; library-provider seam for SharePoint; AI
drives task completion; stack = FastAPI + SQLite + React/Vite; shared bid record from
`docs/design/data-model.md`. Facts verified in `knowledge/VERIFIED_FACTS.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. Confirm DB state: `python3 src/db.py` → should show `opportunities: 21`,
   `qualifications: 3`, `bids: 3`, `bid_plans: 3`, `bid_manage: 3` (the demo seed) — unless a prior
   session's testing left different rows; check before assuming.
3. Spin up the stack: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev`
   → `http://localhost:5173`. Demo data is seeded by `python3 src/seed_plan_demo.py` (Plan bids) +
   `python3 src/seed_manage_demo.py` (Manage registers); each takes `--clear` to reset.
4. `src/.env` holds a real Anthropic key (gitignored) — AI drafting and Settings → Test connection
   should work live without setup.

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`).
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
