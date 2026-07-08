# FWF Bid Library — SharePoint architecture

Three libraries/lists, not one folder dump. This structure is what makes
reliable retrieval (B03) and auto-prefill possible.

---

## 1. Bid Submissions Library

Complete historical bids, as submitted.

Path convention: `/Bids/Submitted/[Year]/[Buyer] - [Opportunity]/`

Metadata columns:
- Buyer
- Sector (NHS | local_gov | central_gov | education | blue_light | other)
- Framework
- RM code
- Lot
- Submission date
- Outcome (won | lost | shortlisted | non_compliant | withdrawn | unknown)
- Score / feedback
- Bid lead
- Service line
- Procurement regime (PA23 | PCR2015)
- Reusable? (yes | no)
- Confidentiality (public | internal | client_confidential | commercially_sensitive)

## 2. Approved Answer Bank

Reusable answer chunks — **one record per answer or answer component**, not
whole documents.

Metadata columns:
- Theme
- Question type
- Service line
- Framework
- Sector
- Outcome source (which bid it came from + that bid's outcome)
- Approved by
- Approval date
- Review date
- Do-not-use flag
- Evidence links
- Confidentiality
- Expiry date (where the content contains time-bound facts)

## 3. Evidence Register

Reusable proof — certificates, case studies, metrics, methods, CVs, policies.

Metadata columns:
- Evidence type (case_study | certificate | metric | CV | method | policy)
- Document owner
- Expiry date
- Approved for external use (yes | no)
- Related claims
- Related services
- Link to source document

---

## How the skills use these

| Skill | Reads | Writes |
|-------|-------|--------|
| B00 ingestion | Google Drive (migration) | all three libraries |
| B03 retrieval | Approved Answer Bank + Evidence Register | — |
| B04 drafter | Approved Answer Bank + Evidence Register (via B03) | — |
| B07 learning | Bid Submissions Library | Approved Answer Bank + Evidence Register (promote/retire/expire) |

## Retrieval capability note

- **Keyword search + metadata filters** — native to SharePoint / Microsoft
  Search. Works day one.
- **Semantic search** — requires Microsoft Graph search, Copilot, or Azure AI
  Search indexed over the libraries. This is the enrichment layer FWF builds;
  B03 works without it (keyword + metadata) and improves with it.
