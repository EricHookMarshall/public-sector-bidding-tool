# FWF Bid Skills — B-series (v2)

A controlled-reuse bid system, not just a workflow:

```
old bids → structured SharePoint answer bank → evidence-checked retrieval →
evaluator-focused drafts → human red-team → final compliance gate →
clarification control → feedback loop
```

Each skill is a folder: `SKILL.md` (triggers + orchestration + a `## Contract`
block) plus bundled `scripts/` and `references/`. Install by dropping each
folder into `/mnt/skills/user/`. Package references: `STANDARD.md` (skill
standard + handoff schema + UNKNOWN rule) and `SHAREPOINT.md` (three-library
architecture).

## The chain

```
B00 library intake/indexing
   → B01 qualify
   → B02 compliance matrix
   → B03 SharePoint answer/evidence retrieval
   → B04 response drafting
   → B04a human review / red-team
   → B05 pre-flight & submission gate
   → [HUMAN SUBMITS]
   → B06 clarification management
   → B07 outcome, debrief & library update  ──┐
                                               └──► feeds back into B00/library
```

## Skills

| Skill | Job | Deterministic engine |
|-------|-----|----------------------|
| **b00-library-ingestion** | Turn old bids into structured, reusable records across 3 SharePoint libraries | `build_records.py` (validate + quarantine + no auto-approve) |
| **b01-bid-qualification** | Gates (incl. UNKNOWN-blocks) + weighted score + bid economics | `score.py` |
| **b02-compliance-matrix** | Full-traceability matrix with 5 RAGs | `build_matrix.py` |
| **b03-answer-evidence-retrieval** | Hybrid retrieval + explicit reuse-score + do-not-reuse | `rank.py` |
| **b04-response-drafter** | Evaluator map + draft + upgraded checker + evidence ledger | `check_answer.py` |
| **b04a-human-review** | Structured red-team, GO/REWORK per answer | (human) |
| **b05-submission-preflight** | Two-stage gate; UNKNOWN blocks; conditional docs; EFS/FVRA | `preflight.py` |
| **b06-clarification-management** | Register w/ deadline+tz, backup owner, escalation | `clarification_log.py` |
| **b07-outcome-learning** | Debrief → promote/retire/refresh library actions | `debrief.py` |

## What changed from v1 (this review's upgrades)

- **B00 added** — the missing foundation; without it B03 is just folder search.
- **B03 rewritten for SharePoint** — Graph/Copilot/Azure AI Search, hybrid
  retrieval, explicit ranking formula, do-not-reuse controls, answer components.
- **B07 added** — the learning loop; library improves after every bid.
- **B02 expanded** — source traceability, evaluation mapping, split into 5 RAGs.
- **UNKNOWN is now blocking** in B01 and B05 — nothing passes by omission.
- **B04 evidence ledger + upgraded checker** — stale terms, unsupported claims,
  unapproved commitments, named people.
- **B06 upgraded** — deadline time+timezone, backup owner, escalation.
- **B04a added** — the human red-team as an explicit chain step.
- **Every skill** now carries the 8-part `## Contract` and a machine handoff.

## Flagged for grounding (refine step)

- Live bids are in **Google Drive**; target is **SharePoint** — B00 owns the
  migration. SharePoint isn't populated until B00 runs.
- **Semantic** retrieval needs Graph/Copilot/Azure AI Search stood up; keyword +
  metadata works day one.
- Reconcile B02 columns against the live G-Cloud 15 Compliance Matrix.
- B01 default weights and the >15% bid-cost flag are proposed baselines.
