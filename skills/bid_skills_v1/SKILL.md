---
name: b01-bid-qualification
description: >
  FWF Bid Qualification & No-Bid Assistant. Use this skill whenever an
  opportunity is presented for a go/no-go decision — a tender notice, framework
  call-off, PSL invitation, RFP, RFQ, ITT, or a warm buyer conversation that
  might convert. Triggers include: "should we bid", "bid or no-bid",
  "go/no-go", "qualify this opportunity", "is this worth pursuing", "score this
  tender", "run the qualification", "shall we go for this". The skill runs a
  two-layer assessment — hard eligibility gates first, then a weighted score —
  and produces a Bid/No-Bid Decision Record. It RECOMMENDS; the MD owns the
  final decision. Always use this skill before FWF commits effort to a
  response, so bandwidth is not spent on opportunities FWF cannot legally bid,
  cannot resource, or cannot win.
---

# B01 — Bid Qualification & No-Bid Assistant

Front gate of the bid lifecycle. Turns a raw opportunity into a defensible
go/no-go recommendation, protecting scarce MD and delivery bandwidth from
unwinnable or ineligible pursuits.

The output is a **recommendation and a record**, never a decision. Eric (MD)
signs the go/no-go.

---

## Why this skill exists

FWF is a small UK team (MD, sales director, Microsoft Practice) with Romanian
delivery recharged from Arobs. Every bid consumes bandwidth FWF cannot easily
replace. The two most expensive mistakes are:

1. **Bidding something FWF cannot legally submit** — no route to market, or a
   financial-standing gate FWF cannot clear (the structural issue behind the
   G-Cloud 15 disregard).
2. **Bidding something FWF cannot win or cannot deliver** — burning a scarce
   week of effort on a low-probability or unresourceable opportunity.

This skill catches both before effort is committed. The hard gates catch (1);
the weighted score catches (2).

---

## The two-layer model

Qualification is **not** a single score. A high score cannot rescue an
opportunity FWF is ineligible to bid. So the assessment runs in two layers,
in order:

```
Layer 1 — HARD GATES (knockout)
   Any FAIL → NO-BID or CONDITIONAL. Do not score. Stop.

Layer 2 — WEIGHTED SCORE (only if all gates pass or are conditional-cleared)
   Produces a 1–5 weighted score → BID / REVIEW / NO-BID recommendation.
```

This is the key difference from the S02 scoring model: S02 has no knockout
layer. Bid/no-bid does. A route-to-market failure is not a low weighting — it
is a stop.

---

## Layer 1 — Hard gates

Each gate is a yes/no. Any **FAIL** forces the recommendation regardless of how
attractive the opportunity looks. Some fails are **CONDITIONAL** — the
opportunity can proceed only if the condition is resolved before the deadline.

| # | Gate | Question | FAIL means |
|---|------|----------|------------|
| G1 | **Route to market** | Does FWF have a compliant route to bid this? (G-Cloud 14 place while live; RM6200 AI DPS membership; below-threshold under PA23; a valid open competitive procedure; or a prime willing to subcontract.) | No compliant route → **NO-BID**. |
| G2 | **Financial standing (EFS/FVRA)** | If the route imposes a financial-standing stage, can FWF clear it — standalone, or with an Arobs Group PCG *ready to issue*? | EFS stage applies and no PCG in place → **CONDITIONAL** (resolve PCG first) or **NO-BID** if PCG cannot be secured in time. This is the G-Cloud 15 failure mode — treat it as a first-class gate. |
| G3 | **Capability fit** | Is the scope inside the Microsoft Practice envelope (Power Platform, Copilot Studio, M365, Azure AI consultancy)? | Materially outside the envelope → **NO-BID** unless a credible partner covers the gap. |
| G4 | **Deliverability** | Can Arobs delivery resource the scope within the required timeframe and geography? | No resource path → **NO-BID** or **CONDITIONAL** (confirm Arobs availability). |
| G5 | **Deadline feasibility** | Is there enough working time to produce a compliant response given current MD/team load? | Insufficient time for a compliant submission → **NO-BID**. A rushed non-compliant bid is a wasted bid. |
| G6 | **Eligibility & mandatory requirements** | Any mandatory exclusion grounds, or mandatory certifications/insurances FWF lacks (e.g. Cyber Essentials, ISO 27001, PI/PL/EL cover, Carbon Reduction Plan where thresholds apply)? | A missing mandatory requirement that cannot be met by the deadline → **NO-BID** or **CONDITIONAL**. |

**Gate output:** state each gate PASS / FAIL / CONDITIONAL with a one-line
reason. If any gate is FAIL, stop and report — do not proceed to scoring. If
gates are only CONDITIONAL, note the conditions and proceed to scoring flagged
as conditional.

---

## Layer 2 — Weighted score

Runs only when all hard gates PASS (or are CONDITIONAL and worth pursuing).
Five dimensions, each scored 1–5, weighted to 100%. Weights are adjustable; if
revised weights are supplied, validate they sum to 100% before use.

| # | Dimension | Weight | Scores on |
|---|-----------|--------|-----------|
| 1 | **Strategic fit** | 20% | Alignment to FWF target frameworks/markets, reference value, foot-in-the-door with a target buyer |
| 2 | **Win probability** | 30% | Incumbency/relationship, competitive field, differentiation, evaluation fit, evidence strength |
| 3 | **Commercial value** | 20% | Contract value, margin, and call-off longevity (a G-Cloud 14 call-off can run up to 48 months) |
| 4 | **Deliverability & risk** | 20% | Delivery complexity, Arobs resource confidence, technical/commercial risk, contract terms |
| 5 | **Effort-to-win ratio** | 10% | Bid cost (person-days) against the prize, given a small team. High effort + low prize scores low. |

Weights sum to 100%. Win probability is weighted heaviest deliberately: for a
small team, a low-probability bid is the most expensive form of waste.

### Scoring scale (1–5)

| Score | Meaning |
|-------|---------|
| 1 | Poor — strong reason to walk away on this dimension |
| 2 | Weak |
| 3 | Neutral / acceptable |
| 4 | Strong |
| 5 | Compelling — a reason on its own to pursue |

### Calculation

```
For each dimension d:
  weighted(d) = score(d) × weight(d)

qualification_score = sum(weighted(d))   [range 1.0 – 5.0]
```

---

## Recommendation thresholds

| Weighted score | All gates PASS | Any gate CONDITIONAL |
|----------------|----------------|----------------------|
| ≥ 3.7 | **BID** | **CONDITIONAL BID** — resolve gate(s) then proceed |
| 3.0 – 3.69 | **REVIEW** — MD judgement call | **REVIEW** |
| < 3.0 | **NO-BID** | **NO-BID** |

Any hard-gate **FAIL** overrides the table → **NO-BID** (or CONDITIONAL if the
gate can be resolved before the deadline).

The threshold is a prompt for the MD, not a verdict. A 3.5 with a strategic
reference prize may be worth a yes; a 3.8 that eats three weeks of the only
bid-capable person may be worth a no.

---

## Workflow

### Step 1 — Ingest the opportunity

Accept the opportunity in any form: a tender notice / OCID, a Find a Tender or
Contracts Finder link, a pasted spec, a PSL invitation, or a described warm
lead. Extract and confirm the key facts:

- Buyer, title, reference/OCID
- Route (framework/DPS/below-threshold/open procedure/subcontract) and whether
  FWF can use it
- Value and duration (incl. call-off/extension potential)
- Deadline(s) — submission and any clarification window
- Mandatory requirements and evaluation basis (MEAT/MAT, weightings if stated)
- Scope, against the Microsoft Practice envelope

If a fact is missing, say so and flag it — do not infer a value that changes
the gate outcome.

### Step 2 — Run the hard gates

Assess G1–G6. Record PASS / FAIL / CONDITIONAL with a one-line reason each.
If any gate FAILs, **stop** — report the gate result and the NO-BID/CONDITIONAL
recommendation. Do not score a bid FWF cannot submit.

### Step 3 — Score (if gates clear)

Score dimensions 1–5, apply weights, compute the weighted score. Show the
working — per-dimension score, weighted contribution, total.

### Step 4 — Present

Produce:
1. **Gate summary** — G1–G6, each PASS/FAIL/CONDITIONAL + reason
2. **Score table** — dimension, score, weight, weighted contribution
3. **Weighted score** — with band label
4. **Recommendation** — BID / CONDITIONAL / REVIEW / NO-BID + the single most
   decisive factor in one sentence
5. **If CONDITIONAL** — the exact condition(s) and the deadline to resolve them

Then ask: *"Shall I record this as a Bid/No-Bid Decision Record?"*

### Step 5 — Record (if confirmed)

Write a dated Bid/No-Bid Decision Record capturing the opportunity facts, gate
results, scores, recommendation, and the MD's decision + rationale. Map to the
FWF FOR-series bid/no-bid form where one exists.

> **Confirm against Drive:** the exact FOR-series code for the bid/no-bid form
> is not yet verified in this skill. Check the Drive bid library (FOR001–FOR005
> series / Bid Library Tracker) and set the correct reference before this skill
> writes records to a shared template.

---

## Output artefact — Bid/No-Bid Decision Record

A single-page record per opportunity:

- **Header** — date, opportunity title, buyer, reference/OCID, route, value, deadline
- **Gate results** — G1–G6 with reasons
- **Score** — dimension table + weighted total + band
- **Recommendation** — BID / CONDITIONAL / REVIEW / NO-BID + decisive factor
- **Conditions** (if any) — what must be resolved, by when, owned by whom
- **Decision** — MD's go/no-go, date, signature/initials, rationale

This record is the audit trail. It is also the input to the pipeline tracker
and, if a BID, the trigger for B02 (compliance matrix) and B03 (answer reuse).

---

## Error handling

| Condition | Action |
|-----------|--------|
| Route to market unclear | Do not guess. Flag G1 as UNKNOWN and ask which route is intended before recommending. |
| EFS/FVRA applicability unclear | Flag G2 as CONDITIONAL, state the assumption, and note PCG dependency. Never assume a PCG is "in place" unless confirmed. |
| Value or deadline missing | Flag as missing; if it would change a gate or the band, do not produce a firm recommendation until supplied. |
| Weights don't sum to 100% | Recalculate proportionally or ask for confirmation. |
| Opportunity outside MS Practice but with partner | Score G3 CONDITIONAL, note the partner dependency explicitly. |
| Strong strategic case but low score | Present both; do not suppress the score. Let the MD weigh the strategic override. |

---

## Bundled parts

- `scripts/score.py` — deterministic engine. Takes gate results (PASS/FAIL/
  CONDITIONAL) and dimension scores, applies weights, enforces the gate-override
  rule, and returns the recommendation + band. Use this rather than computing by
  hand. Run `python scripts/score.py --help` for input format.
- `references/decision_record_template.md` — the Bid/No-Bid Decision Record
  layout to populate in Step 5.

---

## Relationship to other skills

- **Feeds:** B02 (Compliance Matrix) and B03 (Answer & Asset Reuse) — both
  trigger only on a BID decision.
- **Shares pattern with:** S02 (Scoring Assistant) — same weighted-dimension
  mechanics, plus a hard-gate layer S02 does not have.
- **Does not replace:** the MD's judgement, pricing strategy, or buyer
  relationship work. Those remain human.
