---
name: b05-submission-preflight
description: >
  FWF Submission Pre-flight & EFS/FVRA Gate. Use this skill to confirm a bid is
  complete, compliant and clears the financial-standing gate — run TWICE, not
  just at the end. Triggers include: "pre-flight check", "are we ready to
  submit", "readiness review", "submission checklist", "final review", "check
  the EFS position". It runs a deterministic completeness-and-gate check across
  mandatory matrix rows (all five RAGs Green), answer compliance, conditional
  supporting documents, the EFS/FVRA gate (the G-Cloud 15 failure), the
  deadline (date+time+timezone) and clarification ownership. UNKNOWN blocks.
  It produces READY / NOT READY. It never submits.
---

# B05 — Submission Pre-flight & EFS/FVRA Gate

The completeness-and-gate check that makes the G-Cloud 15 class of failure
structurally hard. Reports **READY / NOT READY** with a punch-list. Never
submits — a human does.

---

## Run it twice

| Stage | When | Purpose |
|-------|------|---------|
| **Readiness** | T-5 working days (or midpoint on short deadlines) | Catch gaps while there is still time to fix them |
| **Final** | T-1 working day (never later than 4 working hours before deadline) | Confirm ready to submit |

A single final-stage check leaves no time to fix what it finds. The readiness
pass is where problems get solved.

---

## What blocks (UNKNOWN blocks — nothing passes silently)

1. **Matrix** — no matrix / no mandatory rows supplied → block. Any mandatory
   row not Green on **all five** RAGs → block.
2. **Answers** — answers required but none supplied → block. Any answer over
   limit, with unfilled placeholders, or with unresolved checker flags → block.
3. **Documents (conditional)** — each required doc checked for present, expiry,
   and acceptability *for this bid*. Any doc marked **UNKNOWN** → block. Missing
   expiry where expected → block.
4. **EFS/FVRA gate** — clears only if: no financial-standing stage on this
   route, OR standalone clears, OR Arobs PCG in place and acceptable at this
   stage. Not supplied / unconfirmed → block.
5. **Deadline** — must have date **and** time **and** timezone → else block.
6. **Clarification handling** — named owner + confirmed monitored mailbox → else
   block (the G-Cloud 15 lesson; not waivable).

---

## Conditional documents

Not a hard-coded list — applicability varies by procurement. Each document:

```
required: true/false
present: true/false        # null = UNKNOWN = block
expiry_date: <date>        # blocks if expected and missing
acceptable_for_this_bid: true/false
source_link: <link>
```

A Carbon Reduction Plan or Modern Slavery Statement may apply differently per
procurement — check applicability, do not always assume required.

---

## Bundled parts

- `scripts/preflight.py` — the two-stage gate engine (`--stage readiness|final`).
- `references/preflight_checklist.md` — the full checklist incl. EFS logic.

> **Verify per procurement:** PCG acceptability at framework-application stage is
> not universal — check the live FVRA instructions (e.g. RM1557.15 Attachment 5).

---

## Contract

**Inputs required:** the B02 matrix status; B04 answer compliance flags; the
document set with statuses; EFS position; deadline (ISO + tz); clarification
owner/mailbox status.
**Output — human:** READY / NOT READY + itemised punch-list by category.
**Output — machine:** handoff envelope, `stage: preflight`, `preflight_stage`,
`verdict`, `blocking: [...]`, `next_skill: human_submit` (then
`b06-clarification-management`).
**Blocking conditions:** see "What blocks" — all are hard.
**Human review points:** submission itself.
**Do-not-do:** never return READY with any UNKNOWN; never assume PCG
acceptability; never waive the clarification-owner check.
**SharePoint locations:** none directly (consumes B02/B04 outputs + doc register).
**Definition of done:** a verdict with an empty blocking list at the final stage,
or a punch-list of exactly what remains.

---

## Relationship to other skills

Consumes B02 (matrix) and B04/B04a (answers). Hands to human submission, then
sets up B06 (owner + mailbox confirmed before evaluation).
