---
name: b06-clarification-management
description: >
  FWF Clarification Management. Use this skill during the evaluation period
  after a bid is submitted, to log, track, escalate and respond to buyer
  clarification requests so none is missed. Triggers include: "log a
  clarification", "we got a clarification request", "track clarifications",
  "what clarifications are open", "draft a clarification response", "when is
  the clarification due". It maintains a register with deadline date+time+
  timezone, portal link, owner and backup, internal due date and escalation
  date; flags due-soon, overdue and escalate; and drafts responses from the bid
  materials. This exists because a missed clarification — routed to a departed
  employee's inbox — is exactly what disregarded FWF from G-Cloud 15.
---

# B06 — Clarification Management

Manages buyer clarifications during evaluation so none is missed. Built directly
on the G-Cloud 15 post-mortem.

**Honest caveat:** the skill maintains the register and drafts responses. It
does not watch the inbox. The real fix is a **named owner + backup** and a
**monitored shared mailbox**. See `references/monitoring_discipline.md`.

---

## Register fields (per clarification)

| Field | Why |
|-------|-----|
| Deadline (date + time) | Date alone is not enough |
| Timezone | Portal deadlines are unforgiving |
| Portal link | Direct source |
| Received via | portal / email / buyer message |
| Owner | Main owner |
| Backup owner | Required — no single point of failure |
| Evidence required | Attachments needed |
| Internal due date | Earlier than the buyer deadline |
| Escalation date | When the MD is alerted |
| Status | open / drafting / with_reviewer / sent / closed |
| Sent by | Audit trail |
| Buyer confirmation | Proof the response was received |

---

## Monitoring cadence

- **Minimum:** daily portal **and** mailbox check throughout evaluation.
- **Twice daily:** during the final week, or whenever any clarification is open.
- Run `scripts/clarification_log.py list` at each check — it flags due-soon,
  overdue, and ESCALATE (past the escalation date and still open).

---

## Workflow

- **Set-up (pre-evaluation):** confirm owner + backup + monitored mailbox (B05
  hand-off). Create the register.
- **On each request:** log immediately (date+time+tz, portal, owner, backup,
  internal due, escalation). Draft the response from the matrix (B02) and
  submitted material (B03). Route for sign-off. Send before the internal due
  date. Close with sent-by + buyer confirmation.
- **On demand / daily:** `list` to see open items, time remaining, escalations.

---

## Bundled parts

- `scripts/clarification_log.py` — register with add/status/close/list,
  working-days-to-deadline, and escalation flagging (`--help`).
- `references/monitoring_discipline.md` — the process rules the skill supports
  but cannot enforce alone.

---

## Contract

**Inputs required:** owner, backup, monitored mailbox; each request's details.
**Output — human:** the open-items list with flags; drafted responses.
**Output — machine:** handoff envelope, `stage: clarifications`, `open_items`,
`escalations`, `overdue`, `next_skill: b07-outcome-learning` (at award/close).
**Blocking conditions:** an unowned clarification, or an unknown deadline, is a
red state — escalate, do not proceed silently.
**Human review points:** every clarification response before it is sent.
**Do-not-do:** never route clarifications to a personal/former-staff inbox;
never send a response without sign-off; never let an item pass its escalation
date unescalated.
**SharePoint locations:** register lives in the bid folder; drafts use B02/B03.
**Definition of done:** every clarification logged, owned, drafted, signed off,
sent before its internal due date, and closed with buyer confirmation.

---

## Relationship to other skills

Set up by B05. Uses B02/B03 to draft. Hands to B07 at award/close.
