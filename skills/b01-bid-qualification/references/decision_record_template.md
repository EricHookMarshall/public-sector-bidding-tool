# Bid/No-Bid Decision Record

> Confirm the correct FWF FOR-series code for this form against the bid library.

**Date:** {date}  **Opportunity:** {title}  **Buyer:** {buyer}  **Sector:** {sector}
**Reference / OCID:** {reference}  **Route:** {route}  **RM code / regime:** {rm} / {regime}
**Value / duration:** {value} / {duration}  **Deadline:** {deadline}

## Hard gates

| Gate | State | Reason |
|------|-------|--------|
| G1 Route to market ✱ | {G1} | {G1_reason} |
| G2 Financial standing (EFS/FVRA) ✱ | {G2} | {G2_reason} |
| G3 Capability fit | {G3} | {G3_reason} |
| G4 Deliverability | {G4} | {G4_reason} |
| G5 Bid capacity & deadline | {G5} | {G5_reason} |
| G6 Eligibility & mandatory reqs ✱ | {G6} | {G6_reason} |
| G7 Evidence availability | {G7} | {G7_reason} |
| G8 Contract risk | {G8} | {G8_reason} |

State: PASS / FAIL / CONDITIONAL / UNKNOWN. ✱ = eligibility (UNKNOWN blocks).

## Weighted score

| Dimension | Score | Weight | Contribution |
|-----------|:---:|:---:|:---:|
| Win probability | {s1} | 22% | {c1} |
| Strategic fit | {s2} | 15% | {c2} |
| Commercial value | {s3} | 15% | {c3} |
| Pricing competitiveness | {s4} | 14% | {c4} |
| Buyer fit | {s5} | 12% | {c5} |
| Deliverability & risk | {s6} | 12% | {c6} |
| Effort-to-win ratio | {s7} | 10% | {c7} |
| **Total** | | | **{total}** |

## Bid economics

- Estimated effort: {effort_days} days · day rate {day_rate}
- Bid cost: {bid_cost}
- Expected value (value × win%): {expected_value}
- Cost-to-expected-value: {ratio}% — {econ_flag}

## Recommendation

**{recommendation}** — {decisive_factor}
Conditions to resolve (if any): {condition} — by {condition_deadline} — owner {condition_owner}

## MD decision

**Decision:** GO / NO-GO  **Date:** {decision_date}  **By:** {md}
**Rationale:** {rationale}
