---
name: b01-bid-qualification
description: >
  FWF Bid Qualification & No-Bid Assistant. Use this skill whenever an
  opportunity is presented for a go/no-go decision — a tender notice, framework
  call-off, PSL invitation, RFP, RFQ, ITT, or a warm buyer conversation.
  Triggers include: "should we bid", "bid or no-bid", "go/no-go", "qualify this
  opportunity", "is this worth pursuing", "score this tender", "run the
  qualification". It runs a two-layer assessment — hard eligibility gates
  (PASS/FAIL/CONDITIONAL/UNKNOWN) then a weighted score — plus bid-cost
  discipline, and produces a Bid/No-Bid Decision Record. UNKNOWN never passes
  silently. It RECOMMENDS; the MD owns the decision.
---

# B01 — Bid Qualification & No-Bid Assistant

Front gate of the bid lifecycle. Turns a raw opportunity into a defensible
go/no-go recommendation, protecting scarce MD and delivery bandwidth from
ineligible, unwinnable, or uneconomic pursuits.

Recommendation and record — never the decision. The MD signs the go/no-go.

---

## The two-layer model + economics

```
Layer 1 — HARD GATES   PASS | FAIL | CONDITIONAL | UNKNOWN
   FAIL                        -> NO-BID (stop)
   UNKNOWN on eligibility gate -> BLOCK  (resolve before recommending)
   UNKNOWN on other gate       -> REVIEW (insufficient information)
   A gate left unset counts as UNKNOWN. Nothing passes by omission.

Layer 2 — WEIGHTED SCORE (only if no FAIL and no eligibility UNKNOWN)
   1-5 across seven dimensions -> BID / REVIEW / NO-BID

ECONOMICS — bid cost vs expected value, always shown.
```

---

## Layer 1 — Hard gates

Eligibility gates (marked ✱) block on UNKNOWN. All gates knock out on FAIL.

| # | Gate | Elig. | FAIL / UNKNOWN means |
|---|------|:---:|----------------------|
| G1 | **Route to market** | ✱ | No compliant route → NO-BID. Unknown route → BLOCK. |
| G2 | **Financial standing (EFS/FVRA)** | ✱ | EFS stage applies + no PCG ready → CONDITIONAL/NO-BID. Unknown → BLOCK. The G-Cloud 15 failure mode. |
| G3 | **Capability fit** | | Outside the Microsoft Practice envelope with no partner → NO-BID. |
| G4 | **Deliverability** | | No Arobs resource path → NO-BID/CONDITIONAL. |
| G5 | **Bid capacity & deadline** | | No one to write/review/approve by the deadline → NO-BID. Time *and* people. |
| G6 | **Eligibility & mandatory requirements** | ✱ | Missing mandatory cert/insurance/exclusion ground → NO-BID. Unknown → BLOCK. |
| G7 | **Evidence availability** | | Cannot evidence the mandatory claims → CONDITIONAL/NO-BID. Deliverable ≠ winnable. |
| G8 | **Contract risk** | | Unacceptable liability cap, TUPE, data processing, SLA, cyber terms → CONDITIONAL/NO-BID. |

State each gate PASS/FAIL/CONDITIONAL/UNKNOWN with a one-line reason. Any FAIL,
or any UNKNOWN on an eligibility gate, stops the assessment — report and stop.

---

## Layer 2 — Weighted score

Seven dimensions, 1-5, weighted to 100%. (Buyer fit, incumbency and pricing sit
here as scored factors, not gates — they lower a score, they don't make a bid
ineligible.)

| Dimension | Weight | Scores on |
|-----------|:---:|-----------|
| Win probability | 22% | Incumbency/relationship, competition, differentiation, evaluation fit |
| Strategic fit | 15% | Alignment to target frameworks/markets, reference value |
| Commercial value | 15% | Contract value, margin, call-off longevity |
| Pricing competitiveness | 14% | Price-to-win realism |
| Buyer fit | 12% | Is this a good-fit buyer, not just good-fit scope |
| Deliverability & risk | 12% | Complexity, resource confidence, delivery/contract risk |
| Effort-to-win ratio | 10% | Bid cost vs prize, given a small team |

**Scale:** 1 poor · 2 weak · 3 neutral · 4 strong · 5 compelling.
**Bands:** ≥3.7 BID · 3.0–3.69 REVIEW · <3.0 NO-BID (CONDITIONAL if any gate conditional).

---

## Bid-cost discipline

Estimate effort before recommending BID:

```
Qualification: x hours    Matrix: x hours       Drafting: x days
Review: x days            Pricing/commercial: x hours   Submission/admin: x hours
```

`score.py` computes: **bid cost** (effort_days × day_rate), **expected value**
(contract_value × win_probability), and the **cost-to-expected-value ratio**.
A high ratio (>15%) flags a likely over-bid — the check that stops a small team
chasing low-probability work.

---

## Workflow

1. **Ingest** the opportunity; extract buyer, sector, route, RM code, value,
   deadline, mandatory requirements, evaluation basis, scope. Missing facts →
   the relevant gate is UNKNOWN.
2. **Run gates** (G1–G8). FAIL or eligibility-UNKNOWN → stop and report.
3. **Estimate effort** and score the seven dimensions.
4. **Compute** via `scripts/score.py` — recommendation + economics.
5. **Present** gate summary, score table, economics, recommendation + the
   single decisive factor. Then offer to record.
6. **Record** (if confirmed) — Bid/No-Bid Decision Record.

---

## Bundled parts

- `scripts/score.py` — gate logic (incl. UNKNOWN), weighted score, economics.
- `references/decision_record_template.md` — the record layout.

---

## Contract

**Inputs required:** opportunity facts; effort estimate; day rate; contract value.
**Output — human:** gate summary + score table + economics + recommendation.
**Output — machine:** handoff envelope, `stage: qualification`, `recommendation`,
`blocking: [unknown eligibility gates]`, `next_skill: b02-compliance-matrix`.
**Blocking conditions:** any FAIL; any eligibility gate UNKNOWN.
**Human review points:** the go/no-go decision; strategic override of a low score.
**Do-not-do:** never treat a missing gate as PASS; never recommend BID with an
eligibility gate unresolved; never override an EFS FAIL with a high score.
**SharePoint locations:** reads Bid Submissions Library for buyer/sector history.
**Definition of done:** every gate stated; score computed or correctly blocked;
economics shown; recommendation + decisive factor given; record offered.

---

## Relationship to other skills

Feeds B02/B03 on a BID. Shares the weighted-dimension mechanics of S02, plus a
gate layer S02 lacks. Does not replace MD judgement, pricing strategy, or buyer
relationships.
