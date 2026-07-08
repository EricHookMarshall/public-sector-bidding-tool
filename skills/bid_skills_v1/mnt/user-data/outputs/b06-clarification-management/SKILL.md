---
name: b06-clarification-management
description: >
  FWF Clarification Management. Use this skill during the evaluation period
  after a bid is submitted, to log, track and respond to buyer clarification
  requests — and to make sure none is missed. Triggers include: "log a
  clarification", "we got a clarification request", "track clarifications",
  "what clarifications are open", "draft a clarification response", "when is the
  clarification due", "clarification deadline". It maintains a clarification
  register (owner, deadline, status), flags anything approaching or past its
  deadline, and drafts responses from the bid materials. This exists because a
  missed clarification — routed to a departed employee's inbox — is exactly what
  disregarded FWF from G-Cloud 15.
---

# B06 — Clarification Management

Manages buyer clarification requests during evaluation so none is missed. This
is the skill built directly on the G-Cloud 15 post-mortem: two clarification
messages routed to a former employee's inbox, went unread, and the bid was
disregarded. The fix was 60–90 minutes of work that no one saw was needed.

**Honest caveat:** a skill maintains the register and drafts the responses. It
does **not** watch the inbox. The real fix is a **named owner** and a
**monitored shared mailbox** for the evaluation period. The skill supports that
discipline; it does not replace it. See `references/monitoring_discipline.md`.

---

## What this skill does

1. **Registers clarifications** — logs each incoming request with its received
   date, deadline, owner and status.
2. **Tracks deadlines** — computes working days remaining, flags items due soon
   or overdue.
3. **Drafts responses** — from the compliance matrix (B02), reusable material
   (B03) and the submitted bid, produces a draft response for human sign-off.
4. **Surfaces the open list** — shows what is open, who owns it, and what is due
   when, at any point.
5. **Records closure** — logs the response sent and the date.

---

## Workflow

### On set-up (before the evaluation period)
Confirm the named owner and the monitored mailbox are in place (this is the B05
hand-off). Create the register with `scripts/clarification_log.py`.

### On each incoming clarification
1. **Log it immediately** — `clarification_log.py add` with received date,
   deadline (date **and** time), and owner.
2. **Draft the response** — pull the relevant matrix row(s) and submitted
   material; draft a precise, on-point answer. Flag any evidence to attach.
3. **Route for sign-off** — present the draft to the owner/MD. Do not send.
4. **On send, close it** — `clarification_log.py close` with the sent date.

### On demand
`clarification_log.py list` — show open items, days remaining, overdue flags.
Run this at least daily during the evaluation period.

---

## Bundled parts

- `scripts/clarification_log.py` — maintains the register (add / list / close),
  computes working-days-to-deadline, flags due-soon and overdue.
  `python scripts/clarification_log.py --help`.
- `references/monitoring_discipline.md` — the non-negotiable process rules
  (owner, mailbox, cadence) that the skill supports but cannot enforce alone.

---

## The rules that matter more than the skill

1. **One named owner** for clarifications for the entire evaluation period, with
   a named backup. Ownership never sits with someone who might leave mid-window.
2. **A monitored shared mailbox** as the portal/submission contact — never an
   individual's personal inbox. (The G-Cloud 14 listing still showing a former
   employee is the live version of this risk — fix it.)
3. **A daily check** of the portal and mailbox during evaluation.
4. **Short deadlines assumed** — clarification windows are typically 5–10
   working days. Treat every one as urgent.

---

## Error handling

| Condition | Action |
|-----------|--------|
| Deadline unknown | Log as URGENT-UNKNOWN; chase the buyer for the deadline immediately. |
| Owner not assigned | Do not proceed silently — escalate to MD; an unowned clarification is the failure mode. |
| Response needs evidence not to hand | Flag, and chase internally against the deadline, not after it. |
| Register file missing | Create a new one; never rely on memory for open items. |

---

## Relationship to other skills

- **Set up by:** B05 (Pre-flight) confirms owner + mailbox before evaluation.
- **Uses:** B02 (matrix) and B03 (reuse) to draft responses.
- **Guards:** the single most damaging failure mode in FWF's bid history.
