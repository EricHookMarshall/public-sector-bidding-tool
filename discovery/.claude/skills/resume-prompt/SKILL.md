---
name: resume-prompt
model: sonnet
description: Resume work on the Public Sector Bidding API Platform PoC from the previous session — read the canonical docs in order, restore context, and continue the Active task. Invoke as /resume-prompt at the start of a session, or when the user says "resume", "pick up where we left off", or "continue from last session".
---

# resume-prompt skill

Resumes work from the previous session. Instead of handing a human a prompt to paste, this skill
*executes* that onboarding itself: it reads the canonical docs in reading order, reconstructs the hot
state, and continues the Active task left in `_session/handover.md`.

The point is a single command that gets you fully oriented and moving — no copy-paste, no re-deriving
where things stand.

## Step 1 — Read the canonical docs, in order

Read these now (they are the project's source of truth, most-load-bearing first):

1. `CLAUDE.md` — project spine: what we're building, stack, conventions, hard rules.
2. `_session/handover.md` — hot state: current Status, **Active task**, surfaced threads, open decisions.
3. `_session/todo.md` — the active queue.

If any of these is missing, say so and stop — the session state is the thing being resumed; don't
guess it. Pull deeper context only as the task demands: `support/brief.md` (full PoC brief),
`cpv_codes.md` (relevance scope), `find_tender_filter.py` (reference connector),
`_session/progress.md` (cold dated history).

## Step 2 — Orient and report

Before doing any work, give the user a short orientation (a few lines, not a wall of text):

- **Where we are** — one line from the handover Status.
- **Active task** — what `_session/handover.md` says to do next, quoted/paraphrased.
- **Blockers / prerequisites** — call out anything the handover flags as needed before resuming (e.g.
  the start-of-session checklist: re-running the connector to confirm the API is reachable, or any
  open decision that gates the next step). Don't run those steps unless the Active task needs it —
  just surface them.

## Step 3 — Continue the work

Proceed with the Active task from `_session/handover.md`.

- If the next move is unambiguous, start on it.
- If it depends on a choice the handover lists as open (e.g. which second API source, or server/UI
  framework), ask the user how they want to proceed rather than assuming.

At session end, follow the working discipline: **replace** `_session/handover.md` hot state, **append**
a dated entry to `_session/progress.md`, and update `_session/todo.md`. Don't commit or push unless asked.
