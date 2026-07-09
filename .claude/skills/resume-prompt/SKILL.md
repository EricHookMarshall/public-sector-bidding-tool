---
name: resume-prompt
description: Resume work on the Public Sector Bidding Tool from the previous session — read the canonical docs in order, restore context, and continue the Active task. Invoke as /resume-prompt at the start of a session, or when the user says "resume", "pick up where we left off", or "continue from last session".
---

# resume-prompt skill

Resumes work from the previous session. Instead of handing a human a prompt to paste, this skill
*executes* that onboarding itself: it reads the canonical docs in reading order, reconstructs the hot
state, and continues the Active task left in `_session/handover.md`.

The point is a single command that gets you fully oriented and moving — no copy-paste, no re-deriving
where things stand.

## Step 1 — Read the canonical docs, in order

Read these now (project source of truth, most-load-bearing first):

1. `CLAUDE.md` — project spine: what we're building, the journey, repo map, ways of working, hard rules.
2. `_session/handover.md` — hot state: current Status, **Active task**, surfaced threads, open decisions.
3. `_session/todo.md` — the active queue.

If any of these is missing, say so and stop — the session state is the thing being resumed; don't
guess it. Pull deeper context only as the task demands: `README.md` (the journey overview),
`knowledge/` (FWF context + `VERIFIED_FACTS.md`), the app code under `src/` (backend) and `web/`
(frontend), `skills/` (the B00–B07 bid chain), `_session/progress.md` (cold dated history).

The app runs from the repo root: `uvicorn api:app --app-dir src --port 8000` for the API and
`cd web && npm run dev` for the UI. `src/bids.db` and `src/.env` live beside the code (gitignored).

## Step 2 — Orient and report

Before doing any work, give the user a short orientation (a few lines, not a wall of text):

- **Where we are** — one line from the handover Status.
- **Active task** — what `_session/handover.md` says to do next, quoted/paraphrased.
- **Blockers / prerequisites** — anything the handover flags as needed before resuming (e.g. the
  SharePoint/MS-Graph dependency for Phase 3, or spinning up the discovery stack for live checks).
  Surface them; don't run them unless the Active task needs it.

## Step 3 — Continue the work

Proceed with the Active task from `_session/handover.md`.

- If the next move is unambiguous, start on it.
- If it depends on a choice the handover lists as an open decision, or needs infrastructure that isn't
  available (e.g. live SharePoint), ask the user how they want to proceed rather than assuming.

At session end, follow the working discipline (or run `/end-session`): **replace**
`_session/handover.md` hot state, **prepend** a dated entry to `_session/progress.md`, and update
`_session/todo.md`. Don't commit or push unless asked.
