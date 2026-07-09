---
name: b00-library-ingestion
description: >
  FWF SharePoint Bid Library Ingestion & Indexing. Use this skill to turn old
  bids into reusable, structured bid knowledge — the foundation the whole
  system depends on. Triggers include: "ingest the old bids", "build the answer
  bank", "index the bid library", "structure our past bids", "migrate the bids
  to SharePoint", "populate the evidence register", "process this old bid into
  records". It reads previous bids (currently in the Google Drive Bids folder;
  target is SharePoint), splits each into reusable records — answers, evidence,
  metadata — and writes them into the three-library SharePoint architecture.
  Run this before B01/B03 rely on the library. Without it, retrieval is only as
  good as an unstructured folder dump.
---

# B00 — SharePoint Bid Library Ingestion & Indexing

Turns old bids into a controlled reuse system. This is the missing foundation:
B03 can only retrieve approved answer components if B00 has built them first.

**Transition role:** the historical bids currently live in Google Drive; the
target is the SharePoint architecture in `../SHAREPOINT.md`. B00's first run is
a migration — read Drive, structure, write SharePoint records.

---

## What this skill does

1. **Discovers bids** — walks the source (Drive Bids folder now; SharePoint
   Submissions Library thereafter) and lists every historical bid.
2. **Extracts per-bid metadata** — buyer, sector, framework, RM code, regime,
   lot, submission date, outcome, score/feedback, bid lead, confidentiality.
3. **Splits into reusable records** — one record per answer/component, not
   whole documents. Each record pairs the **buyer question** with the **answer**
   (retrieval searches the question, not just the answer).
4. **Captures evidence** — case studies, certificates, metrics, methods, CVs,
   policies → Evidence Register records with expiry dates.
5. **Sets reuse controls** — reuse status, confidentiality, content owner,
   expiry, do-not-reuse flags.
6. **Writes records** — `scripts/build_records.py` validates and emits the
   structured records for load into the three SharePoint libraries.
7. **Reports coverage** — how many bids, answers, and evidence items indexed;
   which are missing owners, outcomes, or approval — the gaps to close.

---

## Record fields (per answer record)

See `references/record_schema.md` for the full schema and defaults.

| Field | Why it matters |
|-------|----------------|
| Buyer | Matches public-sector context |
| Sector | NHS / local gov / central gov / education / blue light |
| Framework / route | G-Cloud / DPS / open tender / call-off |
| RM code / regime | Prevents stale CCS/GCA, PA23/PCR language |
| Outcome | won / lost / shortlisted / non-compliant / unknown |
| Score / feedback | Prioritises proven content |
| Question text | Retrieval searches the buyer question |
| Answer text | Reusable draft material |
| Evidence used | Case study / certificate / metric / CV / method / policy |
| Date submitted | Freshness control |
| Content owner | Who can approve reuse |
| Reuse status | approved / needs_update / do_not_reuse |
| Confidentiality | Prevents leakage of sensitive content |
| Expiry date | Insurance, accreditations, policies, figures |
| Source document link | Traceability back to source |

---

## Workflow

### Step 1 — Discover
List all historical bids from the source. Confirm the source (Drive during
migration; SharePoint thereafter).

### Step 2 — Extract & split
For each bid: pull bid-level metadata, then split the response into
question/answer records and pull evidence items. Preserve the source link for
every record.

### Step 3 — Set controls
Default reuse_status = `needs_update` (nothing is "approved" until a human
approves it). Set confidentiality conservatively. Record expiry for any
time-bound fact.

### Step 4 — Validate & write
Run `scripts/build_records.py` to validate required fields and emit records
per library (Submissions, Answer Bank, Evidence Register).

### Step 5 — Coverage report
Report counts and gaps: records missing owner, outcome, approval, expiry, or
confidentiality. These are the human tasks to close before the library is
trustworthy.

---

## Bundled parts

- `scripts/build_records.py` — validates and emits structured records for the
  three libraries. `python scripts/build_records.py --help`.
- `references/record_schema.md` — full field schema, enums, and defaults.
- `../SHAREPOINT.md` — the target library architecture.

---

## Contract

**Inputs required:** source location (Drive folder ID / SharePoint site);
access to read historical bids.
**Output — human:** coverage report (bids, answers, evidence indexed; gaps).
**Output — machine:** per-library record sets (JSON) + a handoff envelope with
`stage: library_ingestion`, counts, and `next_skill: b01-bid-qualification`.
**Blocking conditions:** source unreadable; a record missing buyer, question,
answer, or source link → that record is quarantined, not written.
**Human review points:** approving reuse_status (default `needs_update`);
setting confidentiality; confirming outcomes where unknown.
**Do-not-do:** never mark a record `approved` automatically; never ingest
client-confidential content as externally reusable; never drop the source link.
**SharePoint locations:** writes all three libraries (see `../SHAREPOINT.md`).
**Definition of done:** every historical bid has metadata; every answer is a
question-paired record with a source link, confidentiality, and reuse status;
coverage gaps are reported.
