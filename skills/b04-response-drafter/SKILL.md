---
name: b04-response-drafter
description: >
  FWF Bid Response Drafter. Use this skill to draft answers to bid questions —
  the technical/quality/social-value narratives in a submission. Triggers
  include: "draft this answer", "write the response to question X", "draft the
  quality narrative", "respond to this requirement", "write our approach to Y".
  Before drafting it builds an evaluator map (criterion, weighting, buyer pain,
  win theme, evidence available/missing) and, after drafting, runs an upgraded
  checker (limit, stale terms, unsupported claims, evidence citations, unapproved
  commitments) and produces an evidence ledger per answer. THE DRAFT IS A DRAFT —
  a human red-teams (B04a) and the MD signs off. This is the last mile.
---

# B04 — Bid Response Drafter

Drafts evaluator-focused answers, then checks them and produces an evidence
ledger so no impressive-but-unsupported prose ships. An **assist** skill: it
does the lifting; B04a red-teams and the MD owns the final answer.

---

## Before drafting — the evaluator map (required)

Populate this for every answer before writing a word:

```
Question:
Evaluation criterion:
Score / weighting:
Buyer pain:
Win theme:
Evidence available:
Evidence missing:
Answer structure:
Word / character limit:
```

If **Evidence missing** is non-empty, the answer carries `[EVIDENCE: ...]`
placeholders — never invented facts.

---

## Drafting principles

- Answer the question asked, in its own terms; mirror the evaluation criterion.
- **Claim → evidence → benefit** on every point. No evidence-free assertions.
- Lead with the buyer's outcome, not FWF's history.
- Specific over generic; named methods, real metrics, concrete deliverables.
- Inside the Microsoft Practice envelope; delivery credibility via Arobs where
  relevant, framed honestly (small UK team, recharged delivery).
- Regime-correct: PA23/MAT, correct RM codes, GCA not CCS.
- Draft to ~90% of the limit. Never overrun.

See `references/answer_patterns.md`.

---

## After drafting — checker + evidence ledger

### Checker
Run `scripts/check_answer.py`. **Blocking:** over limit; unfilled placeholders.
**Flags (must be cleared by a human):** stale terms (CCS, MEAT, PCR 2015,
RM6263, G-Cloud 14…); unsupported superlatives (leading, expert, proven,
extensive, robust…); missing buyer-benefit signal; missing evidence-citation
signal; named people/clients (approval?); "we will" commitments (commercial
approval?); missing requirement keywords.

### Evidence ledger (per answer)
See `references/evidence_ledger.md`. One row per claim:

| Claim | Evidence | Source | Owner | Status |
|-------|----------|--------|-------|--------|
| We deliver Power Platform governance | prior project / method | SharePoint link | Practice lead | Approved |
| We hold Cyber Essentials | certificate | SharePoint link | Ops | Expires DD/MM/YYYY |

An answer is not ready until every claim has a ledger row with a real source.

---

## Bundled parts

- `scripts/check_answer.py` — blocking + flagging checks (`--help`).
- `references/answer_patterns.md` — structures, win-theme framing, guardrails.
- `references/evidence_ledger.md` — the ledger format and rules.

---

## Contract

**Inputs required:** matrix row; reuse components (B03); win themes; the limit.
**Output — human:** drafted answer (marked DRAFT) + checker report + evidence
ledger.
**Output — machine:** handoff envelope, `stage: drafting`, per-answer
`limit_ok`, `flags_open`, `ledger_unsupported`, `next_skill: b04a-human-review`.
**Blocking conditions:** over limit; unfilled placeholders; any ledger claim
with no source.
**Human review points:** all checker flags; the final answer (B04a + MD).
**Do-not-do:** never invent evidence/metrics/clients/certifications; never claim
outside the practice without a named partner basis; never attribute quotes to
real named people; never present a draft as final.
**SharePoint locations:** reads Answer Bank + Evidence Register (via B03).
**Definition of done:** answer within limit, no placeholders, no open blocking
flags, evidence ledger complete with real sources, marked DRAFT for B04a.

---

## Relationship to other skills

Uses B03 material. Feeds B04a (red-team) then B05 (pre-flight).
