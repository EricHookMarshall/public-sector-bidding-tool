# B03 — reuse feature definitions & freshness

## Feature inputs to the reuse score (each 0–1)

| Feature | 0 | 1 |
|---------|---|---|
| relevance | off-topic | directly answers this question at the right depth |
| context_match | different buyer/sector/framework | same buyer/sector/framework |
| freshness | old / stale facts | recent, reflects current offering & regime |
| evidence_availability | no supporting evidence | evidence in-date and available |
| approved_status | needs_update | approved |

`outcome_quality` is derived from the record outcome: won 1.0 · shortlisted 0.6
· unknown 0.3 · withdrawn 0.2 · lost 0.1 · non_compliant 0.0.

## Freshness status labels (returned per result)

- **in-date** — no time-bound facts, or all within expiry
- **expiring** — contains a fact within 60 days of expiry
- **expired** — contains an expired fact (must not be reused until refreshed)

## Mandatory edit checks before any reuse

- Framework / RM codes current (RM1557.15 vs .14; retire RM6263)
- Regime language current (PA23/MAT, not PCR2015/MEAT)
- Body name current (GCA, not CCS)
- No former staff named
- Figures, dates, certifications, insurance values current
- Word/character limit re-checked against *this* question

## Output shape per result

```
id / source_link
reuse_score + feature breakdown
answer_text
evidence[] | case_study | metrics
required_edits[]
risks[]
approval_status | freshness_status
```
