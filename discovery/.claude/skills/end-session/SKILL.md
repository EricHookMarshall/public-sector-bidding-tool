---
name: end-session
description: Close out a work session on the Public Sector Bidding API Platform PoC — stop any running services, then update the three _session/ working-discipline docs (handover, progress, todo). Invoke as /end-session when wrapping up, or when the user says "end the session", "wrap up", or "update the docs".
model: Sonnet
effort: medium
---

# end-session skill

Closes a session cleanly so the next one resumes with zero re-discovery. Follow the steps in order.
This mirrors the **End-of-session checklist** in `CLAUDE.md` and `_session/handover.md` — if those ever
disagree with this skill, the docs win; update this skill to match.

## Step 1 — Stop running services

Kill anything left running for the PoC (harmless if nothing is up). There is no long-running dev
server or tunnel yet — only the connector script, which is run on demand and exits on its own. If a
local web server has since been added, stop it here, e.g.:

```bash
pkill -f "find_tender_filter.py"   # connector (only if left looping)
# add the UI/server stop command here once a server exists
```

## Step 2 — Gather what actually happened this session

Before writing anything, reconstruct the session honestly:

- What changed on disk (files edited, added, deleted)?
- Verification state: was the connector run (`python3 find_tender_filter.py`), and what did it return
  (counts, errors)? Once a DB/UI exists, quote real results from whatever check applies. If something
  failed or was skipped, say so. Never claim green you didn't observe.
- Decisions made, and any new open questions.
- **Check for false records:** if a prior `_session/` entry claims something exists (a table, a second
  connector, a UI), verify it on disk before carrying it forward.

## Step 3 — Replace `_session/handover.md` (hot state)

The handover is a **one-page snapshot of current state — replace, don't append.** Update at minimum:

- **Status** line: today's date + a one-line summary of where things now stand.
- **Active task**: the single next thing to pick up, concrete enough to start cold.
- Any **Surfaced / parked threads** and **Open decisions** that changed.

Keep it to a page. Cold history belongs in `progress.md`, not here.

## Step 4 — Append to `_session/progress.md` (cold history, append-only)

Prepend a new dated entry **at the top** (most-recent-first), using this shape:

```markdown
## YYYY-MM-DD — <short title>

**Context.** Why this session happened / what it resumed from.

**Work done.** Bulleted, specific. Files touched, commands run, real verification results.

**Decisions.** What was decided and why (or "None new").

**Open questions raised.** New unknowns (or "None new").

**Next.** The single next action — should match the handover Active task.
```

Use today's date from the session context. (`Date` is unavailable in some tooling — get the date from
`date +%Y-%m-%d` or the environment's current-date context, don't guess.)

## Step 5 — Update `_session/todo.md` (active queue)

- Tick completed items (`[x]`) with a one-line note + date; re-order so live work is near the top.
- Add anything surfaced this session.
- Completed items stay briefly for traceability but their full retrospective lives in `progress.md`.

## Step 6 — Confirm

Give the user a short wrap-up: what was done, verification state (honest), which docs were updated, and
the single next action. Note that this is **not** a git repo in the current environment, so there is
nothing to commit — only mention git if that changes.
