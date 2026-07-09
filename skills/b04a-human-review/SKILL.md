---
name: b04a-human-review
description: >
  FWF Human Review & Red-Team. Use this skill to structure a human review of a
  drafted bid response before it goes to the pre-flight/submission gate.
  Triggers include: "red-team this answer", "review the draft", "challenge this
  response", "would this score", "sanity-check the bid", "human review". It
  scaffolds a structured critique — score-the-answer-as-an-evaluator, evidence
  challenge, compliance re-check, risk and commitment review — and produces a
  review record with a GO / REWORK decision per answer. This is a HUMAN review
  point: the skill organises and prompts the critique; a person makes the call.
---

# B04a — Human Review & Red-Team

The deliberate human checkpoint between drafting (B04) and the submission gate
(B05). It does not auto-approve; it structures a person's critique and records
the GO/REWORK decision. Rework loops back to B04.

---

## Why it is its own step

Automated checks (B04's checker) catch mechanical problems. They do not catch a
technically-clean answer that would still score poorly, over-promises, or
leans on weak evidence. That judgement is human. B04a makes that judgement
structured and recorded rather than ad hoc.

---

## The four-lens review (per answer)

### 1. Score as the evaluator
Read the answer against the published evaluation criterion and score it as the
buyer would. Would it earn the marks available? What would cost marks?

### 2. Evidence challenge
For every claim in the evidence ledger: is the evidence real, current, and
strong enough? Challenge the weakest claim first. Cut or downgrade anything the
buyer could puncture.

### 3. Compliance re-check
Does the answer actually satisfy the requirement (not an adjacent, easier one)?
Within the word/character limit? Correct submission location noted?

### 4. Risk & commitment review
Any "we will" commitment that needs commercial/MD sign-off? Any named person or
client without approval? Any liability/SLA implied that should be qualified?
Any capability implied outside the Microsoft Practice envelope?

---

## Output — review record (per answer)

```
Answer ref:
Evaluator score (reviewer's estimate):
Strongest point:
Weakest point / biggest risk:
Evidence challenges:
Compliance: pass / fail (+reason)
Commitments needing approval:
Decision: GO | REWORK
Rework actions (if REWORK):
Reviewer / date:
```

See `references/redteam_checklist.md` for the full prompt list.

---

## Bundled parts

- `references/redteam_checklist.md` — the reviewer's structured question set.

---

## Contract

**Inputs required:** the drafted answer (B04), its evidence ledger, the matrix
row (criterion, weighting, limit).
**Output — human:** a review record per answer with GO/REWORK.
**Output — machine:** handoff envelope, `stage: human_review`, per-answer
`decision`, `rework_actions`, `next_skill: b05-submission-preflight`.
**Blocking conditions:** any answer marked REWORK is not cleared to B05.
**Human review points:** the whole skill — this *is* the human point.
**Do-not-do:** never let the skill mark GO on the human's behalf; never skip the
evidence challenge to save time.
**SharePoint locations:** none directly (reads B04 outputs).
**Definition of done:** every answer has a review record and a GO/REWORK
decision; REWORK items have named actions and loop back to B04.

---

## Relationship to other skills

Receives B04 drafts. Sends GO answers to B05; loops REWORK answers to B04.
