# FWF Bid Skills — B-series

Six skills covering the bid lifecycle up to (and including) the point the
G-Cloud 15 failure actually occurred. Each is a proper skill folder:
`SKILL.md` (orchestration + triggers) plus bundled `scripts/` and `references/`.

Install by dropping each folder into `/mnt/skills/user/`.

| Skill | Job | Tier | Bundled parts |
|-------|-----|------|---------------|
| **b01-bid-qualification** | Go/no-go: hard gates then weighted score | Assist | `score.py`, decision-record template |
| **b02-compliance-matrix** | Shred a tender into a tracked requirements matrix | Full | `build_matrix.py`, column reference |
| **b03-answer-reuse** | Find & rank reusable prior answers from Drive | Full | reuse rubric (engine = Drive retrieval) |
| **b04-response-drafter** | Draft evaluator-focused answers to limit | Assist | `check_answer.py`, answer patterns |
| **b05-submission-preflight** | Ready/not-ready gate incl. EFS/FVRA | Full | `preflight.py`, checklist |
| **b06-clarification-management** | Log/track/draft clarifications | Full | `clarification_log.py`, monitoring discipline |

## The chain

```
B01 qualify ──(BID)──► B02 matrix ──► B03 reuse ──► B04 draft ──► B05 pre-flight ──► [HUMAN SUBMITS] ──► B06 clarifications
```

## Design decisions worth knowing

- **Separate skills, not one bundle.** Each stage triggers at a different moment
  on a different cue, so each is its own skill; the parts inside each skill are
  bundled.
- **B01 has a hard-gate layer** that S02-style scoring does not — a route or
  EFS failure is a knockout, not a low weighting.
- **B05 and B06 both treat EFS and clarification-ownership as blocking.** These
  are the two things that actually sank G-Cloud 15.
- **B06 is honest about its limits:** it maintains the register and drafts
  responses, but the real fix is a named owner + a monitored shared mailbox. A
  skill can't watch an inbox.

## Flagged for grounding against Drive (refine step)

- B01: correct FOR-series code for the bid/no-bid record.
- B02: reconcile matrix columns against the live G-Cloud 15 Compliance Matrix
  (`15TpOKNaR2bkJAyaTN3xc2hE7Kdq4EnyL`).
- B03: bid library structure, FOR-template codes, and won/lost outcome tagging.
- B01 weights (20/30/20/20/10) are a proposed baseline, not confirmed.
