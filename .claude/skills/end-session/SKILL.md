---
name: end-session
description: Close out a work session on the Public Sector Bidding Tool — stop running services, then update the three _session/ working-discipline docs (handover, progress, todo). Invoke as /end-session when wrapping up, or when the user says "end the session", "wrap up", or "update the docs".
model: Sonnet
effort: medium
---

# end-session skill

Closes a session cleanly so the next one resumes with zero re-discovery. Follow the steps in order.
This mirrors the **End-of-session checklist** in `_session/handover.md` and the ways of working in
`CLAUDE.md` — if those ever disagree with this skill, the docs win; update this skill to match.

## Step 1 — Stop running services

Harmless if nothing is running (the only long-running services are the app's API + UI):

```bash
pkill -f "uvicorn api:app"   # JSON API (run with --app-dir src)
pkill -f vite                # web UI
```

## Step 2 — Gather what actually happened this session

Before writing anything, reconstruct the session honestly:

- What changed on disk (files edited, added, deleted, moved)?
- Verification state: what did you actually run, and what was the real result? For app code:
  imports/`python3 src/db.py`, a live connector run, or the Vite build. For docs/skills: nothing to run —
  say so. **Quote real results. Never claim green you didn't observe**; if something failed or was
  skipped, say so.
- Decisions made, and any new open questions.
- **Check for false records:** if a prior `_session/` entry or a doc claims something exists, verify it
  before carrying it forward. (Precedent this project already caught: RM6263 was listed as a live
  framework in the recovery plan when it had already expired — see `knowledge/VERIFIED_FACTS.md`.)

## Step 3 — Replace `_session/handover.md` (hot state)

The handover is a **one-page snapshot of current state — replace, don't append.** Update at minimum:

- **Status** line: today's date + a one-line summary of where things now stand.
- **Active task**: the single next thing to pick up, concrete enough to start cold.
- Any **Surfaced / parked threads** and **Open decisions** that changed.

Keep it to a page. Cold history belongs in `progress.md`, not here.

## Step 4 — Prepend to `_session/progress.md` (cold history, append-only)

Add a new dated entry **at the top** (most-recent-first), using this shape:

```markdown
## YYYY-MM-DD — <short title>

**Context.** Why this session happened / what it resumed from.

**Work done.** Bulleted, specific. Files touched, commands run, real verification results.

**Decisions.** What was decided and why (or "None new").

**Open questions raised.** New unknowns (or "None new").

**Next.** The single next action — should match the handover Active task.
```

Get today's date from the environment's current-date context or `date +%Y-%m-%d`, don't guess.

## Step 5 — Update `_session/todo.md` (active queue)

- Tick completed items (`[x]`) with a one-line note + date; re-order so live work is near the top.
- Add anything surfaced this session.
- Completed items stay briefly for traceability; their full retrospective lives in `progress.md`.

## Step 6 — Commit (only if the user asks)

This **is** a git repo (remote: `github.com/EricHookMarshall/public-sector-bidding-tool`). Do **not**
commit or push unless the user asks. If they do: never stage `bids.db`, `node_modules/`, or secrets
(they're gitignored — keep it that way), and end commit messages with the project's Co-Authored-By line.

## Step 7 — Confirm

Give the user a short wrap-up: what was done, verification state (honest), which docs were updated, and
the single next action.
