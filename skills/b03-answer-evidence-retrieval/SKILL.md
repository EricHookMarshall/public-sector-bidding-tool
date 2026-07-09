---
name: b03-answer-evidence-retrieval
description: >
  FWF SharePoint Answer & Evidence Retrieval. Use this skill when drafting a bid
  and FWF wants to reuse proven material rather than write from scratch.
  Triggers include: "have we answered this before", "find a similar response",
  "reuse our answer on X", "what have we said about Y", "pull the boilerplate",
  "is there a case study for Z", "check the answer bank". For a requirement, it
  runs hybrid retrieval (keyword + semantic + metadata filters) over the
  SharePoint Approved Answer Bank and Evidence Register, applies do-not-reuse
  exclusions, ranks by an explicit reuse-score formula, and returns answer
  COMPONENTS — text, evidence, case study, metrics, required edits, risks,
  source, approval and freshness status — ready for B04 to draft from.
---

# B03 — SharePoint Answer & Evidence Retrieval

Finds the best reusable **answer components** for a requirement — not just old
passages. This is a controlled-reuse retrieval skill over the SharePoint bid
library, not a Drive text search.

**Retrieval capability:** keyword search and metadata filters are native to
SharePoint/Microsoft Search and work day one. Semantic search needs Microsoft
Graph search, Copilot, or Azure AI Search indexed over the libraries — the
enrichment layer FWF builds. The skill works without it and improves with it.

---

## Hybrid retrieval — three ways, every requirement

1. **Keyword** — exact terms ("incident response", "Power Platform", "Carbon
   Reduction Plan").
2. **Semantic** — similar meaning where wording differs (Graph/Copilot/Azure AI
   Search). Falls back to keyword if the semantic layer is not stood up.
3. **Metadata filters** — SharePoint columns: won bids, same sector, same
   framework, recent date, **approved content only** by default.

Search the **buyer question**, not only the answer text (B00 stores both).

---

## Ranking — explicit formula

`scripts/rank.py` computes, per candidate (features 0–1):

```
Reuse score = 0.35 relevance to question
            + 0.20 same buyer/sector/framework
            + 0.15 outcome quality (won>shortlisted>unknown>lost)
            + 0.15 freshness
            + 0.10 evidence availability
            + 0.05 approved reuse status
```

---

## Do-not-reuse controls (applied before ranking)

Excluded, with a stated reason — never silently down-ranked:

- Lost-bid content where feedback criticised that answer
- Superseded framework language
- Named former employees
- Expired insurance / certification claims
- Client-specific confidential / commercially sensitive content not cleared
- Old CCS wording where GCA now applies
- PCR 2015 / MEAT wording where PA23 / MAT applies

---

## Return answer components (not just passages)

For each usable result, return:

- **Reusable answer text**
- **Relevant evidence** (from the Evidence Register)
- **Case study**
- **Metrics**
- **Required edits** (dates, names, figures, framework/RM codes)
- **Risks** (what could weaken this if reused as-is)
- **Source link**
- **Approval status** (approved / needs_update)
- **Freshness status** (in-date / expiring / expired)

If nothing clears the exclusions and reuse threshold, say so plainly and hand
to B04 for net-new drafting.

---

## Bundled parts

- `scripts/rank.py` — do-not-reuse exclusions + the explicit reuse-score formula.
- `references/reuse_rubric.md` — feature definitions and freshness checks.

---

## Contract

**Inputs required:** the requirement/matrix row; access to the SharePoint
Answer Bank + Evidence Register.
**Output — human:** ranked answer components per requirement, with edits/risks.
**Output — machine:** handoff envelope, `stage: retrieval`, per-row
`best_reuse_score`, `evidence_gaps`, `next_skill: b04-response-drafter`.
**Blocking conditions:** none (returns "no usable match" rather than blocking),
but never returns excluded content.
**Human review points:** none in retrieval; reuse approval lives in B00/B07.
**Do-not-do:** never return do-not-reuse content; never return client-
confidential material uncleared; never present reused text as submission-ready.
**SharePoint locations:** reads Approved Answer Bank + Evidence Register.
**Definition of done:** every requirement has ranked components or an explicit
"no usable match", with exclusions logged and reasons given.

---

## Relationship to other skills

Depends on B00 having populated the libraries. Feeds B04. Retrieval quality is
capped by library quality — which B00 builds and B07 improves.
