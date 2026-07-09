# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-09` (session 5) — **Repo restructured: one flat project, no nested sub-app.**
The `discovery/` folder is gone. Backend code now lives in `src/`, the frontend in `web/`,
the brief in `support/` — all at the repo root. The duplicated project-discipline files
(`discovery/_session/`, `discovery/.claude/`, `discovery/CLAUDE.md`) were consolidated into
the single top-level set. The app was **live-verified running from the new layout** (`db.py`
finds `src/bids.db` with all data intact — 21 opps / 3 bids / 3 plans; `uvicorn api:app
--app-dir src` serves `/api/meta` and `/api/plan/board` 200; `.env` loads from `src/`).

Before this, session 4 built **Plan (Stage 3)** — pipeline board + team-capacity + FOR002
timeline, reading `bids.db`, live-verified over real HTTP. That work is included here.

## Active task

**Nothing blocking — the structure is now clean and the app runs.** Pick the next stage,
or (still recommended, now 4 sessions outstanding) get the user's first browser click-through
of the running shell. Search, Triage (+ Settings), and Plan are all real and verified
server-side, but no human has looked at them in a browser yet.

If continuing the build: **Manage (Stage 5, FOR003 clarification log)** is the leaning choice —
no external blocker, and it directly encodes the missed-clarification failure this tool exists
to prevent. **Complete (Stage 4, FOR006)** is next in journey order but blocked on live
SharePoint/MS Graph (hard rule in `CLAUDE.md`), so its AI pre-fill can't be live-verified the
way Triage/Plan were.

## What shipped

**Restructure (session 5)** — `discovery/*.py` → `src/`, `discovery/web` → `web/`,
`discovery/support` → `support/`, `requirements.txt` → repo root; `bids.db` + `.env` +
`.env.example` moved into `src/` (both resolved relative to `__file__`, so they travel with
the code). Imports untouched (all bare) — the app runs via `uvicorn api:app --app-dir src`
and scripts via `python3 src/x.py`, which put `src/` on the path. Stale duplicate
`discovery/.claude` deleted (root `.claude` is the current set); `discovery/CLAUDE.md` merged
into root `CLAUDE.md`; `discovery/_session/` merged into this top-level triad. Root
`.gitignore` repointed `discovery/bids.db` → `src/bids.db`.

**Plan (Stage 3) — session 4** (`src/bidplan.py`, `src/db.py`, `src/api.py`, `web/src/api.js`,
`web/src/stages/PlanStage.jsx`, `web/src/journey.js`, `web/src/styles.css`,
`src/seed_plan_demo.py`) — FOR002 domain logic (15-phase timeline, 6 pipeline stages,
`capacity_summary()` + reactive `alerts()` incl. the clarification-deadline alert), the
`bid_plans` table, `/api/plan/board` + `/api/plan/reference` + `GET`/`PUT /api/bids/{id}/plan`,
and a real board UI replacing the mock. `seed_plan_demo.py` seeds 3 illustrative bids
(`--clear` resets). Live-verified: board grouping, capacity over-commit, reactive alerts,
timeline save.

## Surfaced / parked threads

- **User review of the running shell — 4 sessions outstanding.** Search, Triage (+ Settings),
  Plan all real and verified server-side; no browser click-through yet. Worth doing before a
  4th real stage is built on three unreviewed ones.
- **HubSpot integration** — future feature (pipeline ↔ CRM). Noted in `architecture.md`, not scoped.
- **`web/src/StagePlaceholder.jsx`** — still dead code (superseded by per-stage screens); not deleted.
- **SharePoint data path for `LibraryItem`** — parked to the Complete stage. The concrete reason
  Complete is harder to build next than Manage.
- **Azure OpenAI provider** — skeleton in `src/llm.py`, not implemented. Client requirement;
  build when Azure access is provisioned.
- **Team capacity default (25 days, `src/bidplan.py`)** — a placeholder tuned to demo well, not
  a real FWF number, and not persisted. Should become a real input before it's more than illustrative.

## Open decisions

1. **Which stage next** — Manage (Stage 5, no external blocker, directly on-thesis) vs. Complete
   (Stage 4, next in order but blocked on live SharePoint/MS Graph). Leaning Manage; not decided.
2. **Team capacity as a real input** — currently a hardcoded default overridable only per-request.
3. **Azure OpenAI timing** — build when Azure access is provisioned, not before.

Settled this session: **flat repo structure** — backend `src/`, frontend `web/`, one `_session/`
triad + one `CLAUDE.md` at root, no nested sub-app (matches the user's other projects).

Settled earlier, unchanged: Plan (Stage 3) wired to real data; Triage (B01) + AI pre-fill +
Settings; storage extended into `bids.db` in place; mockups-first method; six-stage journey shape
+ visual style approved; local app now, Azure SPA later; library-provider seam for SharePoint; AI
drives task completion; stack = FastAPI + SQLite + React/Vite; shared bid record from
`docs/design/data-model.md`. Facts verified in `knowledge/VERIFIED_FACTS.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. Confirm DB state: `python3 src/db.py` → should show `opportunities: 21`,
   `qualifications: 3`, `bids: 3`, `bid_plans: 3` (the demo seed) — unless a prior session's
   testing left different rows; check before assuming.
3. Spin up the stack: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev`
   → `http://localhost:5173`. Demo data is seeded; `python3 src/seed_plan_demo.py --clear` removes
   it, `python3 src/seed_plan_demo.py` reseeds.
4. `src/.env` holds a real Anthropic key (gitignored) — AI drafting and Settings → Test connection
   should work live without setup.

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`).
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
