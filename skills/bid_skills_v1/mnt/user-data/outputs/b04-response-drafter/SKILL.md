---
name: b04-response-drafter
description: >
  FWF Bid Response Drafter. Use this skill to draft answers to bid questions —
  the technical/quality responses in a tender or framework submission. Triggers
  include: "draft this answer", "write the response to question X", "draft the
  quality narrative", "respond to this requirement", "write our approach to Y",
  "turn this into a bid answer". Working from a compliance-matrix row (B02) and
  any reusable material (B03), it drafts a structured, evaluator-focused answer
  within the stated word/character limit, then checks the draft against the
  limit and the requirement's keywords. THE DRAFT IS A DRAFT — a human edits and
  owns the final answer. This is the human-in-the-loop last mile.
---

# B04 — Bid Response Drafter

Drafts evaluator-focused answers to bid questions. It does the heavy lifting;
the final edit and sign-off are human. This is deliberately an **assist** skill,
not an autonomous one — bid answers carry commercial and evidential
commitments the MD must own.

---

## What this skill does

1. **Takes a question** — a matrix row (B02) with its text, type, weighting,
   response type and word/character limit.
2. **Pulls reusable material** — via B03 where prior content exists.
3. **Drafts to structure** — using the patterns in
   `references/answer_patterns.md` (claim → evidence → benefit; method →
   deliverable → assurance), led by the win themes for the bid.
4. **Writes to the limit** — respects the stated word/character limit; never
   overruns.
5. **Answers the actual question** — mirrors the evaluation criteria and the
   requirement's language so the evaluator can score it easily.
6. **Checks the draft** — runs `scripts/check_answer.py` for limit compliance
   and requirement-keyword coverage.
7. **Flags evidence needs** — marks every claim that needs a real evidence
   reference (metric, case study, certification) with `[EVIDENCE: ...]` so
   nothing ships as an unsupported assertion.

---

## Drafting principles

- **Answer the question asked**, in its own terms. Evaluators score against
  published criteria — make it trivial to award marks.
- **Claim → evidence → benefit.** Every claim carries evidence and a benefit to
  the buyer. No evidence-free assertions.
- **Lead with the win theme**, not with FWF's history. What the buyer gets, not
  what FWF is.
- **Specific over generic.** Named methods, real metrics, concrete deliverables.
  Replace "robust processes" with the actual process.
- **Within the Microsoft Practice envelope** — Power Platform, Copilot Studio,
  M365, Azure AI. Draw delivery credibility from the Arobs team where relevant.
- **Regime-correct language** — PA23/MAT for new procurements; framework-correct
  RM codes; GCA not CCS.
- **Never overrun the limit.** An over-limit answer can be truncated or
  disqualified. Draft to ~90% of the limit to leave editing room.

---

## Workflow

### Step 1 — Understand the question
Read the requirement, its weighting, response type and limit. Identify what the
evaluator is actually scoring.

### Step 2 — Gather material
Pull reusable content (B03). Identify what is genuinely new. Identify the win
theme(s) this answer should carry.

### Step 3 — Draft
Draft to structure and to limit. Mark evidence needs with `[EVIDENCE: ...]`.
Keep FWF's real shape honest — do not overstate scale or claim capabilities
outside the practice.

### Step 4 — Check
Run `scripts/check_answer.py --limit "<limit>" --keywords "<k1,k2>" --file draft.txt`.
Report word/char count vs limit and keyword coverage. Fix any overrun.

### Step 5 — Hand over for sign-off
Present the draft clearly marked as a draft, with the evidence placeholders and
any judgement calls flagged for the MD. **Do not present it as final.**

---

## Bundled parts

- `scripts/check_answer.py` — word/character count vs limit, and
  requirement-keyword coverage check. `python scripts/check_answer.py --help`.
- `references/answer_patterns.md` — answer structures, win-theme framing, and
  the FWF honesty guardrails.

---

## Guardrails

- Never invent evidence, metrics, client names, or certifications. Use
  `[EVIDENCE: ...]` placeholders for the human to fill with real facts.
- Never claim capability outside the Microsoft Practice without a named
  partner/Arobs basis.
- Never attribute quotes to real named people.
- The output is always a draft for human sign-off — state this every time.

---

## Relationship to other skills

- **Triggered by:** matrix rows from B02.
- **Uses:** B03 for reusable material.
- **Feeds:** B05 (Pre-flight), which confirms every mandatory answer is present,
  within limit, and evidence-complete before submission.
