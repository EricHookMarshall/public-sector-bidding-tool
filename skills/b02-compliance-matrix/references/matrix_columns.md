# Compliance Matrix — column definition (v2)

> Reconcile against the live G-Cloud 15 Compliance Matrix on first live use.

| Column | Purpose | Values |
|--------|---------|--------|
| Ref | Working requirement ID | 3.2.1, 3.2.1a |
| Source document | Which attachment/spec it came from | file name |
| Page/para/clause | Precise audit trail | e.g. Att.3, cl.4.2, p12 |
| Requirement | The requirement text | faithful, concise |
| Category | Type of requirement | eligibility \| technical \| commercial \| legal \| social_value \| pricing \| evidence |
| M/D | Mandatory or Desirable | M \| D |
| Pass/fail? | Compliance vs scored quality | pass_fail \| scored |
| Answer required? | Prose answer, or an action | Yes \| No (action in Notes) |
| Evaluation criterion | What the evaluator scores | text |
| Weight/score | Weighting or marks available | e.g. 10% / 5 marks |
| Limit | Response constraint | e.g. 500 words |
| Lot | Which lot | Lot 3 |
| Draft owner | Who writes it | name |
| Evidence owner | Who provides proof (may differ) | name |
| Dependency | External dependency | Arobs \| partner \| finance \| insurance \| legal |
| Draft link | Where the answer lives | link |
| Evidence link | Where the proof lives | link |
| Risk | Row risk | High \| Medium \| Low |
| Clarify? | Raise with buyer? | Yes \| No |
| Submission location | Where it goes at upload | portal field / attachment / pricing tab |
| RAG Compliance | Will comply | Red \| Amber \| Green |
| RAG Evidence | Evidence available | Red \| Amber \| Green |
| RAG Drafting | Drafted | Red \| Amber \| Green |
| RAG Review | Reviewed/approved | Red \| Amber \| Green |
| RAG Submission | In submission location | Red \| Amber \| Green |
| Notes | Anything else / the action | free text |

## RAG convention (per track)

- **Red** — not started
- **Amber** — in progress / identified but not complete
- **Green** — complete for that track

A row is done only when **all five RAGs are Green**. This is the check B05
enforces for every mandatory row.

## Rules

- Every row needs a **Ref**, **Requirement** and **Source locator**.
- Every **Mandatory** row must reach five-Green before submission.
- Split compound requirements into separate rows sharing the Ref stem.
