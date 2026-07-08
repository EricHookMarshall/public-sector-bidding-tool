# FWF Bid Skills — writing standard

Every skill in the B-series carries the same eight-part contract so hand-offs
between skills are clean and every skill states its own guardrails.

## The eight sections (every SKILL.md ends with a `## Contract` block)

1. **Inputs required** — what must be supplied before the skill runs.
2. **Output — human** — the human-readable summary the skill produces.
3. **Output — machine** — a structured YAML/JSON handoff block for the next skill.
4. **Blocking conditions** — states that stop the skill returning a "ready/go".
5. **Human review points** — where a person must decide, not the skill.
6. **Do-not-do rules** — hard prohibitions.
7. **SharePoint locations** — which library/list the skill reads or writes.
8. **Definition of done** — the completion test.

## UNKNOWN is a first-class state

Across the series, facts are `PASS | FAIL | CONDITIONAL | UNKNOWN`.
- **FAIL** → blocks (knockout).
- **UNKNOWN on an eligibility-affecting fact** → blocks (cannot proceed on a
  guess). Eligibility facts: route to market, financial standing, mandatory
  eligibility, submission deadline, document expiry.
- **UNKNOWN on a non-eligibility fact** → REVIEW ("insufficient information to
  recommend"), never a silent PASS.

Nothing passes silently by omission.

## Machine handoff envelope

Every skill emits this envelope (stage-specific fields added):

```yaml
bid_id: FWF-2026-001
stage: <skill stage id, e.g. compliance_matrix>
buyer: Example Council
sector: local_gov
route: G-Cloud 15
rm_code: RM1557.15
regime: PA23
deadline: 2026-07-31T12:00:00+01:00
# --- stage-specific ---
mandatory_open_items: 4
evidence_gaps: 7
clarifications_to_raise: 2
blocking: []            # list of blocking conditions still open
next_skill: b03-answer-evidence-retrieval
```

The `blocking` list must be empty before a skill reports a green/ready state.

## Source-of-truth note

Historical bids currently live in the Google Drive "Bids" folder. The target
is the SharePoint architecture in `SHAREPOINT.md`. B00 owns the transition.
Until migration is complete, B00 reads Drive and writes SharePoint records;
B03 retrieves from SharePoint. Do not assume SharePoint is populated until B00
has run.
