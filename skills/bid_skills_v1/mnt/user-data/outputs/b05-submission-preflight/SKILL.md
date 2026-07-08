---
name: b05-submission-preflight
description: >
  FWF Submission Pre-flight & EFS/FVRA Gate. Use this skill in the final review
  before a bid is submitted, to confirm the submission is complete, compliant,
  and clears the financial-standing gate. Triggers include: "pre-flight check",
  "are we ready to submit", "submission checklist", "final review", "have we
  got everything", "check the EFS position", "is the bid complete". It runs a
  deterministic completeness-and-gate check across mandatory requirements,
  supporting documents, and — critically — the EFS/FVRA financial-standing
  position (the exact gate that disregarded FWF from G-Cloud 15). It produces a
  ready / not-ready report. It does not submit; a human submits.
---

# B05 — Submission Pre-flight & EFS/FVRA Gate

The last check before submission. Confirms nothing mandatory is missing and the
financial-standing gate is cleared. Built because the G-Cloud 15 disregard was
an avoidable completeness/gate failure — this skill exists to make that class of
failure structurally hard to repeat.

It reports **READY** or **NOT READY**. It never submits.

---

## What this skill does

1. **Checks mandatory completeness** — every Mandatory row in the B02 matrix is
   Green (complete, reviewed, evidenced).
2. **Checks answer compliance** — every drafted answer is within its
   word/character limit and has no unfilled `[EVIDENCE: ...]` placeholders.
3. **Checks supporting documents** — insurances, certifications, Carbon
   Reduction Plan, declarations, pricing — present and current.
4. **Checks the EFS/FVRA gate** — the financial-standing position for this
   route: standalone accounts sufficient, or Arobs PCG in place and acceptable
   at this stage. This is a first-class, blocking check.
5. **Checks the clarification channel** — confirms a named owner and a
   monitored mailbox are assigned for the evaluation period (hands to B06).
6. **Produces a report** — READY / NOT READY with an itemised list of anything
   outstanding.

---

## The EFS/FVRA gate — why it blocks

FWF UK's standalone accounts do not clear EFS on most GCA frameworks. The
remedy is an Arobs Group Parent Company Guarantee. The G-Cloud 15 submission
failed here: a clarification sought parent-company financial evidence and it
was never answered.

So this check is blocking. Pre-flight cannot return READY unless, for the
route in question, **one** of these is true and confirmed:

- The route imposes no separate financial-standing stage (e.g. below-threshold
  under PA23), **or**
- FWF's standalone position clears the stated threshold, **or**
- An Arobs Group PCG is in place, current, and confirmed acceptable at this
  stage of this procurement.

> **Verify per procurement:** PCG acceptability at framework-application stage
> is not universal — check the live instructions (e.g. RM1557.15 Attachment 5
> FVRA). Do not assume a PCG clears the gate without confirming it for this bid.

---

## Workflow

### Step 1 — Load the checklist
Read `references/preflight_checklist.md` and the bid's B02 matrix. Build the
check config (see `scripts/preflight.py` for format).

### Step 2 — Run the checks
Run `scripts/preflight.py --config bid.json`. It evaluates every item and the
EFS gate, and returns a structured report with a hard READY/NOT READY verdict.

### Step 3 — Report
Present the verdict and every outstanding item, grouped: mandatory-incomplete,
answers-non-compliant, documents-missing, EFS-gate, clarification-owner. Each
item names what is missing and (where known) who owns closing it.

### Step 4 — Do not submit
Hand the report to the MD. Submission is a human action. If NOT READY, the
report is the punch-list to clear first.

---

## Bundled parts

- `scripts/preflight.py` — the checklist/gate engine. Reads a bid config,
  returns READY/NOT READY + outstanding items. `python scripts/preflight.py --help`.
- `references/preflight_checklist.md` — the full standard checklist, including
  the EFS gate logic and the mandatory-document list.

---

## Error handling

| Condition | Action |
|-----------|--------|
| EFS position unconfirmed | Gate = NOT READY. Never assume PCG acceptability. |
| Matrix has Amber mandatory rows | NOT READY; list them. |
| Answer over limit / has placeholders | NOT READY; list them. |
| No clarification owner assigned | NOT READY; this is the G-Cloud 15 failure — do not waive it. |
| A document's currency is unknown | Flag as unconfirmed; treat as missing until confirmed. |

---

## Relationship to other skills

- **Consumes:** B02 (matrix status), B04 (answer compliance).
- **Hands to:** B06 (Clarification Management) — confirms the owner/mailbox are
  set before the evaluation period begins.
- **Precedes:** human submission.
