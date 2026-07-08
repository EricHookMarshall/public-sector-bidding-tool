---
name: b03-answer-reuse
description: >
  FWF Answer & Asset Reuse. Use this skill when drafting a bid response and FWF
  wants to reuse existing material rather than write from scratch. Triggers
  include: "have we answered this before", "find a similar response", "reuse
  our answer on X", "what have we said about Y", "pull the boilerplate", "is
  there a case study for Z", "check the bid library". Given a requirement or
  question, the skill searches the FWF Drive bid library, ranks candidate prior
  answers by fit and freshness, and returns the best reusable material with the
  parts that need updating flagged. Use it before B04 drafts anything net-new,
  so proven, evaluator-tested content is reused wherever it exists.
---

# B03 — Answer & Asset Reuse

Finds and surfaces the best existing FWF material for a given requirement, so
the response drafter (B04) starts from proven content, not a blank page.

The engine is **Drive retrieval**, not a bundled script — the value is in
querying the bid library well and judging reuse-readiness, not in local code.

---

## What this skill does

1. **Takes a requirement** — a single matrix row (from B02) or a described
   question.
2. **Searches the bid library** — Drive Bids folder: historical responses,
   templates (FOR-series), case studies, boilerplate, evidence documents.
3. **Ranks candidates** — by relevance, recency, and outcome (won bids rank
   above lost; recent above stale).
4. **Assesses reuse-readiness** — scores each candidate on the rubric in
   `references/reuse_rubric.md` (drop-in / light-edit / rework / not usable).
5. **Returns the best fit** — the candidate(s) with the specific edits needed
   flagged (dates, client names, figures, framework references).
6. **Flags true gaps** — if no usable prior answer exists, says so plainly so
   B04 drafts net-new rather than force-fitting stale content.

---

## Drive retrieval approach

Use the Google Drive MCP. Two complementary moves (per established FWF tooling
notes):

- **Folder-walk by `parentId`** for structural browsing of the Bids folder
  (top-level ID `16ne52kWeWVtl-zpGB7q99JlYJCaVrOzs`).
- **Keyword search** (`fullText contains` / `title contains`, combined with
  `or`) for scattered material — bid answers on a topic often live across
  several bid folders, not one place.

Drive search responses need a **two-layer JSON parse** (the outer array holds a
single object with a `text` field that is itself JSON containing `files` and
`nextPageToken`). Read individual files with `read_file_content` by `id`.

---

## Workflow

### Step 1 — Frame the query
From the requirement, pull the topic keywords (the content nouns — the
capability, framework, or subject), not meta-words. E.g. a requirement about
incident response → search "incident response", "security", "SLA", not
"requirement" or "question".

### Step 2 — Search
Run keyword search across the bid library. If thin, folder-walk relevant bid
packs (won bids first). Collect candidate passages with their source file + date
+ known outcome.

### Step 3 — Rank & assess
Order candidates by relevance × recency × outcome. Score each against the reuse
rubric. Discard anything below "rework".

### Step 4 — Return
Present the top 1–3 candidates. For each: the reusable text, its source and
date, its reuse band, and the exact edits required (what is out of date, what
must be re-evidenced, what references a superseded framework/RM code).

If nothing is usable, say so and hand to B04 for net-new drafting.

---

## Bundled parts

- `references/reuse_rubric.md` — the reuse-readiness bands and the mandatory
  freshness checks (dates, figures, personnel, framework/RM codes).

> **Confirm against Drive:** verify the bid library structure and the FOR-series
> template codes on first use. Won/lost outcome tagging may not be explicit in
> file metadata — check the Bid Library Tracker for outcome data.

---

## Freshness — non-negotiable checks before any reuse

Prior answers carry stale facts. Before returning any candidate, flag for update:

- **Framework / RM codes** — e.g. content citing RM6263 (superseded) or
  RM1557.14 where RM1557.15 now applies; PCR 2015 vs PA23 regime language.
- **Body names** — CCS references where GCA now applies (renamed 1 April 2026).
- **Personnel & contacts** — former staff named as contacts.
- **Figures** — turnover, headcount, dates, certifications, insurance values.
- **Evaluation basis** — MEAT (PCR) vs MAT (PA23).

Never return reused text as ready-to-submit. Return it as a draft with these
flagged.

---

## Relationship to other skills

- **Triggered by:** B02 matrix rows, or directly during drafting.
- **Feeds:** B04 (Response Drafter) — supplies the starting material.
- **Depends on:** Google Drive MCP access to the Bids folder.
