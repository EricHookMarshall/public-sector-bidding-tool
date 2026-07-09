---
name: b02-compliance-matrix
description: >
  FWF Compliance & Requirements Matrix Builder. Use this skill after a BID
  decision to break a tender, framework attachment, ITT, RFP or specification
  into a fully traceable, tracked requirements matrix. Triggers include: "build
  the compliance matrix", "extract the requirements", "shred the tender", "map
  the spec", "requirements tracker", "response matrix". It reads the source
  document(s), extracts every requirement with its exact source locator,
  classifies and categorises each, maps it to the evaluation criteria, and
  produces an Excel matrix with five separate RAG statuses (compliance,
  evidence, drafting, review, submission) so a row that is drafted but not
  evidenced never reads as green. Always run before B04 drafts.
---

# B02 — Compliance & Requirements Matrix Builder

The single source of truth for a response: every requirement, its exact source,
what the evaluator scores, who owns the answer and the evidence, and five
independent status tracks. This is the artefact that makes missed requirements
structurally hard.

---

## What this skill does

1. **Reads the source** — spec, attachments, evaluation criteria, question sets.
2. **Extracts requirements** — one row per discrete requirement, with the exact
   **source document** and **page/paragraph/clause** locator.
3. **Categorises** — eligibility / technical / commercial / legal / social
   value / pricing / evidence.
4. **Maps to evaluation** — the criterion scored, the weighting/score available,
   and whether it is pass/fail vs scored quality.
5. **Assigns ownership** — separate **draft owner** and **evidence owner**, plus
   any **dependency** (Arobs, partner, finance, insurance, legal).
6. **Tracks five RAGs** — compliance, evidence, drafting, review, submission.
7. **Flags clarifications** — marks questions to raise with the buyer.
8. **Records submission location** — portal field / attachment name / pricing
   tab, so nothing is lost at upload.

---

## The five RAG statuses

A single RAG hides real risk. These are independent:

| RAG | Green means |
|-----|-------------|
| **Compliance** | Requirement understood and the response will comply |
| **Evidence** | Evidence identified and available (not just claimed) |
| **Drafting** | Answer drafted |
| **Review** | Answer reviewed/approved |
| **Submission** | Placed in the correct submission location |

A row is only truly done when **all five** are Green. Drafted-but-not-evidenced
shows Drafting=Green, Evidence=Red — visibly not done.

---

## Full column set

See `references/matrix_columns.md`. Columns: Ref · Source document ·
Page/para/clause · Requirement · Category · M/D · Pass/fail? · Answer required? ·
Evaluation criterion · Weight/score · Limit · Lot · Draft owner · Evidence
owner · Dependency · Draft link · Evidence link · Risk · Clarify? · Submission
location · the five RAGs · Notes.

---

## Extraction rules

- One row per discrete requirement; split compound clauses (3.2.1a, 3.2.1b).
- Preserve the exact source locator — every answer traces to a clause.
- "shall/must/required" → M; "should/desirable/scored on" → D.
- Capture response constraints verbatim (word/page limit, format).
- Requirements needing an *action* (not prose) → Answer required? = No, with the
  action in Notes.
- Do not paraphrase so hard the meaning shifts.

---

## Bundled parts

- `scripts/build_matrix.py` — writes the structured requirement list to a
  formatted `.xlsx` with the five RAGs. `--help` for input format.
- `references/matrix_columns.md` — full column definitions and RAG conventions.

> **Confirm against library:** reconcile column names/order against the live
> G-Cloud 15 Compliance Matrix on first live use so output matches FWF's
> template.

---

## Contract

**Inputs required:** the governing source documents; the lot(s) being bid.
**Output — human:** the matrix workbook + a gap summary (mandatory rows not
fully Green, clarifications to raise, requirements with no evidence owner).
**Output — machine:** handoff envelope, `stage: compliance_matrix`,
`mandatory_open_items`, `evidence_gaps`, `clarifications_to_raise`,
`next_skill: b03-answer-evidence-retrieval`.
**Blocking conditions:** a requirement with no source locator is not a valid row.
**Human review points:** confirming M vs D where ambiguous; confirming the
evaluation criteria mapping.
**Do-not-do:** never collapse the five RAGs into one; never create an answer
with no matrix Ref.
**SharePoint locations:** none (reads the tender pack). Feeds B03.
**Definition of done:** every requirement is a row with a source locator,
category, evaluation mapping, owners, and five RAGs initialised.

---

## Relationship to other skills

Triggered by a BID from B01. Feeds B03 (retrieval per row) and B04 (one answer
per row). B05 checks every mandatory row is fully Green before submission.
