# Data model — derived from the FWF SharePoint bid store

> **Source of truth for the shared bid record.** This is not invented — it is
> *reverse-engineered* from FWF's real, working bid store
> (`knowledge/SharePoint Folder/Bids/`): the `FOR001–FOR006` bid forms, the
> `Tender Pipeline` / `Bid Library` trackers, the `Public Sector Bidding
> Framework.docx` process, and the folder taxonomy repeated across **26 real
> bids**. Each of the six journey stages already has a real artifact behind it;
> the data model just names the fields those artifacts already use.

## The key insight

FWF has already validated the data model by using it. We don't need to design a
record from first principles — we need to *encode what the forms already
capture*. Every stage maps to a concrete SharePoint artifact:

| Journey stage | Real FWF artifact | Becomes entity |
|---|---|---|
| 1. SEARCH   | discovery `bids.db` + `FOR004 Bid Opportunity Overview` | **Opportunity** |
| 2. TRIAGE   | `FOR001 Bid Qualification Questionnaire` + Bid/No-Bid governance form | **Qualification** (promotes Opportunity → **Bid**) |
| 3. PLAN     | `FOR002 BidPlan Timeline` + `Tender Pipeline.xlsx` + FOR001 effort model | **BidPlan** + pipeline status |
| 4. COMPLETE | `FOR006 Tender Response Master` (compliance matrix) + `02 Bid Library` | **ResponseItem** (per question) + **LibraryItem** |
| 5. MANAGE   | `FOR003 CQLOG` (clarification log) + preflight checklist | **Clarification** + **ComplianceCheck** |
| 6. LEARN    | Pipeline `Review` sheet (Won/Not Won) + Lessons Learned Log | **Outcome** |

The per-bid folder taxonomy is itself the lifecycle, identical across all 26 bids:
`00 Bid Admin → 01 Customer Documents → 02 Response Docs → 03 Internal Reviews →
04 Pricing & Financials → 05 Supporting Evidence → 06 Final Submission → 07 Post
Submission`.

---

## Entities

### 1. Opportunity  (SEARCH)  — *extends the existing `src/db.py` record*

Discovery already stores ~18 fields (`source`, `ocid`, `title`, `buyer_name`,
`cpv_codes`, `value_max`, `deadline_date`, `url`, …). `FOR004` shows the extra
human-facing fields FWF records when an opportunity is worth a second look — add
these to bridge SEARCH → TRIAGE:

- `sector` — e.g. "Housing / Registered Provider", "Central Gov"
- `procurement_portal` + `portal_ref` — e.g. "MyTenders – FTS Ref 2025/S 000-036416"
- `opportunity_type` — enum: `PPN` (early notice) · `PQQ`/`SQ` · `ITT` · `DPS` · `Framework` · `Further Competition` · `Direct Award`
- `scope_summary` — free text
- `client_objectives` — free text
- `evaluation_criteria` — free text (quality/price split, weightings)
- `known_competitors` — free text / list
- `clarification_deadline` — **distinct from submission deadline** (the missed-clarification failure this whole tool exists to prevent)

### 2. Qualification  (TRIAGE)  — promotes an Opportunity into a **Bid**

From `FOR001 Bid Qualification Questionnaire`. This is the bid/no-bid gate. A
`Qualification` record hangs off an `Opportunity`; a **Go** decision creates the
`Bid` that the remaining stages attach to.

Fields (from FOR001 `Qualification` sheet):
`client_name`, `sales_owner`, `framework`, `project_requirement_sentence`,
`scope_summary`, `platforms[]`, `estimated_value`, `estimated_start_date`,
`estimated_duration`, `pricing_model` (enum: `Fixed` · `T&M` · `Risk/Reward`),
`pricing_weighting`, `lots_breakdown`, `team_location`, `partner_required` (bool).

`delivery_team_required` — list of `{role, count, comments}` over roles:
Project Manager, Solution Architect, Business Analyst, Developer, Power BI
Developer, UX Designer (the FOR001 fixed role set).

Decision block (from FOR001 `Reference` sheet — this is FWF's actual scoring rig):
- `complexity` — enum: `Low` · `Low-Med` · `Medium` · `Med-High` · `High`
- `decision` — enum: `Go` · `No go`
- `estimated_bid_effort_days` + `estimated_bid_cost` — **computed** from complexity
  × a day-rate table (Bid Manager, Technical Author, Delivery Author, Presentation
  & Demo, Contract Negotiation @ £500/day; e.g. Medium ⇒ 16.5 days ⇒ £8,250). This
  is the "cost to chase" that Planning needs for capacity decisions.

Go/no-go criteria (from the framework doc, for a structured gate rather than a
free-text decision): framework place held? · buyer relationship? · realistic
timeline? · achievable margin? · certifications held? · written-for-incumbent?

### 3. BidPlan  (PLAN)

Two parts.

**(a) Pipeline position** — from `Tender Pipeline.xlsx`. One row per live bid on
the board:
- `pipeline_stage` — enum observed: `Pre-Tender` · `Open Tender` · (in-flight) · `Closed`
- `published_date`, `itt_due` (submission deadline), `buyer_contact`
- `estimated_amount` (may be "Unknown" — keep nullable/text-tolerant)

Also seen: a **Contracts Ending** sheet (incumbent contract, expiry, supplier,
value) — the *source* of future pipeline, and a natural feed from discovery.

**(b) Bid plan timeline** — from `FOR002`. A fixed, ordered phase list, each with
`{phase, owner, start_date, completion_date, dependencies[], comments}`:
`Opportunity Release → Opp/Doc Review → Bid/No-Bid Decision → Kick-Off →
Stakeholders → Win themes → Section ownership → Identify CQs → Solution Design →
Draft 1 → Red Review → Draft 2 → Gold Review → Submission → Post-submission`.
Owner roles: Bid Manager, Sales Lead, Solution Lead, Writers, Review Team, Senior
Stakeholders. These phases + `dependencies` give a real critical path / calendar.

### 4. ResponseItem  (COMPLETE)  — the answer/compliance matrix

From `FOR006 Tender Response Master` — **the richest schema in the store**. One
row per tender question; this *is* the compliance matrix and the AI-prefill
target. Fields:
`customer_document`, `section`, `sub_section`, `question_ref`, `question_text`,
`question_type` (e.g. `Text Response`), `weighting_pct`, `word_count_limit`,
`actual_words`, `images_permitted` (bool), `attachments_permitted` (bool),
`tags[]`, `supplier_response` (the answer text), `owner`, `supporting_person`,
`reviewer`, `target_date`, `status`.

`status` drives the completion board. `word_count_limit` vs `actual_words` is a
live compliance check. `tags` + `question_text` are the retrieval key against the
library (real answers already run 650–750 words — good few-shot material).

### 4b. LibraryItem  (COMPLETE, shared)  — reusable content + credentials

From `02 Bid Library` + `Bid Library Tracker.xlsx`. The reuse corpus AND the
compliance-asset register. Fields:
`category` (Company Credentials · Capabilities · Case Studies · Team & Resource ·
Social Value · Commercial · Delivery · Templates · Governance · Branding),
`item`, `description`, `status` (`Done`/`In Progress`/`Complete`/`TBC`),
`owner`, `assigned_to`, `review_frequency` (`Annually`/`As Required`),
`last_updated`, `notes`, and critically **`expiry_date`**.

> **Expiry is a first-class field.** The tracker already flags "ISO 27001 Expires
> 31 Oct 2025", "9001 Expires 09/01/2026", Cyber Essentials renewal, insurance
> certificates. An expired cert surfaced at bid time is exactly the admin failure
> this tool exists to catch — the model must carry expiry and the tool must alert
> on it (ties to `knowledge/VERIFIED_FACTS.md`'s "facts decay" principle).

### 5. Clarification  (MANAGE)

From `FOR003 CQLOG`. The register whose failure motivated the whole project:
`question_number`, `date_submitted`, `question`, `response_date`,
`buyer_response`, `notes`. Add a derived `status` (Open/Answered) and link to the
`clarification_deadline` on the Opportunity for alerting.

### 5b. ComplianceCheck  (MANAGE)  — preflight gate

Not a single file but implied by the Governance tracker ("Compliance Matrix",
"Bid Submission Checklist"). A pre-submission checklist: every `ResponseItem`
answered & within word count · required credentials present & **not expired** ·
mandatory content present (Social Value / PPN 06/20, Carbon Reduction Plan if
>£5m, Cyber Essentials, Modern Slavery, UK GDPR) · all clarifications resolved.

### 6. Outcome  (LEARN)

From the pipeline `Review` sheet + Lessons Learned Log:
`bid_name`, `submission_due`, `closed_date`, `start_date`,
`result` (enum: `Won` · `Not Won` · `Withdrawn`), plus `score_received`,
`winner`, `feedback`, `lessons[]`. Feeds win-rate tracking (the framework doc
explicitly wants "target win rate, tracked bid by bid") and library updates.

---

## The spine: one record, six stages

```
Opportunity ──(Qualification: Go)──▶ Bid
                                      ├─ BidPlan        (phases + pipeline slot)
                                      ├─ ResponseItem[] (the compliance matrix)   ⇄ LibraryItem[]
                                      ├─ Clarification[]
                                      ├─ ComplianceCheck (preflight gate)
                                      └─ Outcome         (Won/Not Won + lessons)  ──▶ updates LibraryItem[]
```

- **`Bid` is the spine.** It is born when a Qualification says Go, and every later
  stage attaches to it. Its `stage` field (Search/Triage/Plan/Complete/Manage/
  Learn) is what the app shell's stepper reads.
- **`LibraryItem` is shared, not per-bid** — the reuse corpus that COMPLETE draws
  from and LEARN writes back to. This is the `LocalMirror → GraphSharePoint` seam
  from `architecture.md`: today seed it from this folder; later read it live from
  SharePoint.
- **Two deadlines, always distinct**: `clarification_deadline` and
  `submission_deadline`. Losing track of the first is the founding failure.

## What this changes for the build

1. **Discovery's `Opportunity` needs ~7 new nullable fields** (§1) to carry a
   promoted opportunity into Triage without re-keying.
2. **Triage (B01 / Phase 1) is now fully specified** — FOR001 gives every field
   and FWF's real go/no-go scoring. This is the smallest, best-grounded next
   stage to wire to real data.
3. **`FOR006` is the COMPLETE schema** — when SharePoint/MS-Graph lands (Phase 3),
   AI-prefill targets exactly these rows, retrieving from `LibraryItem` by
   `tags` + `question_text`.
4. **Expiry/renewal tracking is core, not a nice-to-have** — bake `expiry_date`
   into `LibraryItem` from day one.

## Open questions

- **Storage**: extend `src/bids.db` (SQLite) with these tables, or a
  separate store? Recommend: same DB, new tables, `Opportunity` FK-linked — keeps
  one local file per the PoC boundary.
- **Enum vs free-text**: FWF's forms mix both (e.g. pipeline stages are ad-hoc
  strings). Start tolerant (text with a suggested enum), tighten later.
- **Seeding `LibraryItem`**: parse the trackers now (openpyxl, as done here) vs
  wait for live Graph. Recommend parse-now for a realistic COMPLETE demo.
</content>
