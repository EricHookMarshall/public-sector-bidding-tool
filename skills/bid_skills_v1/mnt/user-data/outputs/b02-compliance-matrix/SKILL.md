---
name: b02-compliance-matrix
description: >
  FWF Compliance & Requirements Matrix Builder. Use this skill whenever a
  BID decision has been taken and FWF needs to break a tender, framework
  attachment, ITT, RFP or specification down into a tracked list of
  requirements. Triggers include: "build the compliance matrix", "extract the
  requirements", "what do they actually ask for", "map the spec", "requirements
  tracker", "response matrix", "shred the tender", or when a tender document /
  attachment pack is provided after a go decision. The skill reads the source
  document(s), extracts every stated requirement, classifies each as
  mandatory/desirable, and produces a structured Excel matrix that drives the
  whole response. Always use this before drafting responses (B04) so no
  requirement is missed and every answer maps to a source clause.
---

# B02 — Compliance & Requirements Matrix Builder

Turns a tender or framework pack into the single source of truth for the
response: every requirement, where it came from, whether it is mandatory, who
owns the answer, and its status. This is the artefact that stops requirements
being missed — the discipline that was absent when G-Cloud 15 failed.

---

## What this skill does

1. **Reads the source** — tender notice, specification, framework attachments,
   evaluation criteria, question sets. Handles PDF and DOCX (see file-reading /
   pdf-reading skills for extraction).
2. **Extracts requirements** — pulls every discrete requirement, question, and
   evaluation criterion, preserving the source clause reference.
3. **Classifies** — mandatory (M) vs desirable (D); pass/fail vs scored;
   response type (narrative / evidence / declaration / pricing).
4. **Captures limits** — word/character limits and response format per question.
5. **Maps to lots** — tags each requirement to the relevant lot (e.g. G-Cloud
   Lot 3 Cloud Support).
6. **Assigns ownership & status** — owner, RAG status, evidence source, links.
7. **Writes the matrix** — calls `scripts/build_matrix.py` to produce a
   formatted Excel workbook (see `references/matrix_columns.md`).
8. **Flags gaps** — requirements with no FWF evidence or an unclear owner are
   surfaced explicitly for the MD.

---

## Requirement extraction rules

- One row per discrete requirement. Split compound clauses ("the supplier
  shall X and Y") into separate rows.
- Preserve the exact source reference (section/clause/question number). This is
  non-negotiable — every answer must trace to a source clause.
- Capture mandatory language ("shall", "must", "is required to") as **M**;
  preference language ("should", "desirable", "will be scored on") as **D**.
- Record the evaluation weighting where stated.
- Record any response constraint verbatim (word limit, page limit, format).
- Do not paraphrase the requirement text so heavily that its meaning shifts —
  keep it faithful but concise.

---

## Workflow

### Step 1 — Ingest source documents
Identify the governing documents (spec, evaluation criteria, question set,
framework attachments). If several, note precedence. Confirm the lot(s) FWF is
bidding.

### Step 2 — Extract
Walk each document and extract requirements per the rules above into a
structured list (dicts). Do not build the workbook yet.

### Step 3 — Classify & map
For each requirement set: type (M/D), response type, weighting, word/char
limit, lot, proposed owner, initial RAG (default Red until evidenced).

### Step 4 — Build the workbook
Run `scripts/build_matrix.py` with the structured list to produce the formatted
matrix. Columns and formatting are defined in `references/matrix_columns.md`.

### Step 5 — Gap review
Present a short summary: total requirements, count mandatory, count with no
identified FWF evidence, count with no owner. Surface the gaps for the MD.

---

## Bundled parts

- `scripts/build_matrix.py` — writes the structured requirement list to a
  formatted `.xlsx` matrix (openpyxl). `python scripts/build_matrix.py --help`.
- `references/matrix_columns.md` — the FWF matrix column definition and RAG
  convention.

> **Confirm against Drive:** the live G-Cloud 15 Compliance Matrix
> (`15TpOKNaR2bkJAyaTN3xc2hE7Kdq4EnyL`) is the reference format. Read it and
> reconcile column names/order in `references/matrix_columns.md` before this
> skill is used on a live bid, so the output matches FWF's existing template.

---

## Error handling

| Condition | Action |
|-----------|--------|
| Source is a scanned PDF | Route through pdf-reading skill (OCR) before extraction. |
| Compound requirement | Split into separate rows; note the shared source clause. |
| Ambiguous M vs D | Default to M (safer), flag for MD confirmation. |
| No word limit stated | Leave blank; do not invent a limit. |
| openpyxl not installed | `pip install openpyxl --break-system-packages`, or route workbook build through the xlsx skill. |

---

## Relationship to other skills

- **Triggered by:** a BID decision from B01.
- **Feeds:** B04 (Response Drafter) — one drafted answer per matrix row —
  and B05 (Pre-flight), which checks every mandatory row is complete.
- **Can call:** file-reading / pdf-reading (extraction), xlsx (richer
  formatting).
