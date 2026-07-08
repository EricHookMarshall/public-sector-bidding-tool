I am building skills for public sector bidding. The idea being that there is a lot of work needed, and definitely some human intervention required for rework and at final sign off, but having a library of previously submitted bids in SharePoint would massively help pre fill some of the content, which we have. Attached are the skills, can they be made better, can the steps be refined and made more effective, and how?

I’ll inspect the uploaded skill files, identify what each one is trying to do, then suggest concrete improvements to the workflow, retrieval logic, human review points, and SharePoint/bid-library use.

I’ve opened the package. It contains six lifecycle skills: qualification, compliance matrix, answer reuse, drafting, pre-flight, and clarification management, plus lightweight Python scripts and reference templates. The structure is already sensible; the biggest opportunity is to add a proper SharePoint knowledge layer and stronger evidence/approval controls.

Thought for 1m 41s

Yes. They are already a strong skeleton, but they can be made much more effective by changing them from a linear bid-writing workflow into a controlled bid knowledge system.

The biggest issue: B03 is written for Google Drive retrieval, but your target operating model is SharePoint as the bid library. That is the skill that needs the most redesign.

Also, your skills correctly recognise current UK public procurement language: the Procurement Act 2023 came into force on 24 February 2025, and award language has moved from MEAT to MAT. They are also right to use GCA, because Crown Commercial Service became Government Commercial Agency on 1 April 2026. G-Cloud 15 is also now a PA23 framework and its tender pack includes FVRA materials, so your focus on EFS/FVRA is directionally correct.

Overall verdict

The current six skills are good as process prompts, but not yet good enough as a reusable public-sector bidding system.

They need four upgrades:

A SharePoint bid-library ingestion skill before B01/B03.
A stronger evidence and source-control layer.
More deterministic gates: unknown should fail or block, not pass silently.
A post-award learning loop so the library improves after every bid.

At the moment the chain is:

B01 qualify → B02 matrix → B03 reuse → B04 draft → B05 pre-flight → submit → B06 clarifications

I would change it to:

B00 library intake/indexing
        ↓
B01 qualify
        ↓
B02 compliance matrix
        ↓
B03 SharePoint answer/evidence retrieval
        ↓
B04 response drafting
        ↓
B04a human review / red-team
        ↓
B05 pre-flight and submission gate
        ↓
Human submits
        ↓
B06 clarification management
        ↓
B07 outcome, debrief and library update
The most important new skill: B00 SharePoint Bid Library Ingestion

This is missing. Without it, B03 will only ever be as good as the messiness of the folder structure.

Create a new skill whose job is to turn old bids into reusable bid knowledge.

It should ingest every previous bid and split it into reusable records:

Field	Why it matters
Buyer	Helps match public sector context
Sector	NHS, local gov, central gov, education, blue light, etc.
Framework / route	G-Cloud, DPS, open tender, framework call-off
RM code / procurement regime	Prevents stale CCS/GCA, PA23/PCR language
Bid outcome	Won, lost, shortlisted, non-compliant, unknown
Evaluation score / feedback	Helps prioritise proven content
Question text	Retrieval should search the buyer question, not just the answer
Answer text	Reusable draft material
Evidence used	Case study, certificate, metric, CV, method, policy
Date submitted	Freshness control
Content owner	Who can approve reuse
Reuse status	Approved / needs update / do not reuse
Confidentiality	Prevents leakage of client-specific or commercially sensitive content
Expiry date	For insurance, accreditations, policies, figures
Source document link	Traceability back to SharePoint

This one addition would make the whole system much better. Otherwise B03 has to “search old documents”; with B00 it can retrieve approved answer components.

B01 Bid Qualification — good, but make unknowns blocking

B01 is strong. The hard-gate-plus-score model is right. Public sector bids need knockout checks before effort is spent.

I would refine it like this:

Improve the gates

Add these gates:

New / refined gate	Why
Buyer fit	Some buyers are poor-fit even if the scope looks right.
Incumbent / relationship position	Win probability is materially affected by incumbency.
Evidence availability	A bid may be technically deliverable but unwinnable if you cannot evidence it.
Pricing competitiveness	Commercial value alone is not enough; price-to-win matters.
Contract risk	Liability caps, TUPE, data processing, SLAs, cyber obligations.
Bid capacity	Who will actually write/review/approve it by the deadline?
Fix the script logic

Your score.py currently treats missing gates as neither fail nor conditional. That is risky. Missing/unknown gates should be explicit.

Use:

PASS / FAIL / CONDITIONAL / UNKNOWN

And make UNKNOWN produce:

REVIEW — insufficient information to recommend

unless the missing fact affects eligibility, in which case it should block.

Add bid-cost discipline

Add a person-day estimate:

Estimated bid effort:
- Qualification: x hours
- Matrix: x hours
- Drafting: x days
- Review: x days
- Pricing/commercial: x hours
- Submission/admin: x hours

Then calculate:

Bid effort vs contract value vs win probability

That will stop small teams over-bidding low-probability work.

B02 Compliance Matrix — add traceability and scoring intelligence

B02 is good, but the matrix is too thin for real bid control.

Add these columns:

Column	Purpose
Source document	Which attachment/specification the requirement came from
Page / paragraph / clause	Precise audit trail
Requirement category	Eligibility, technical, commercial, legal, social value, pricing, evidence
Evaluation criterion	What the evaluator will score
Weighting / score available	Prioritises effort
Pass/fail?	Separates compliance from scored quality
Answer required?	Some requirements need action, not prose
Evidence owner	Different from drafting owner
Draft answer link	Link to the answer file/location
Evidence link	Link to policy, case study, certificate, pricing doc
Risk level	High / medium / low
Clarification needed?	Marks questions to ask the buyer
Dependency	Arobs, partner, finance, insurance, legal
Review status	Drafted / reviewed / approved / final
Submission location	Portal field, attachment name, pricing workbook tab, etc.

The current RAG is useful but too broad. Split it into:

Compliance RAG
Evidence RAG
Drafting RAG
Review RAG
Submission RAG

A row can be drafted but not evidenced. That should not show as green.

B03 Answer Reuse — this needs the biggest rewrite

This skill should stop being “find old text” and become:

Find the best reusable answer, evidence, structure, and proof points from SharePoint.
Replace Drive-specific wording

Remove:

Google Drive MCP
Drive Bids folder
parentId
read_file_content

Replace with SharePoint/Microsoft 365 language:

SharePoint bid library
document library metadata
Microsoft Search / Graph search
SharePoint columns
file version history
approved answer bank
evidence register
Use hybrid retrieval

For every requirement, B03 should search in three ways:

Keyword search — exact terms like “incident response”, “Power Platform”, “Carbon Reduction Plan”.
Semantic search — similar meaning even where wording differs.
Metadata filters — won bids, same sector, same framework, recent date, approved content only.

The ranking formula should be explicit:

Reuse score =
  35% relevance to question
+ 20% same buyer/sector/framework
+ 15% outcome quality: won > shortlisted > unknown > lost
+ 15% freshness
+ 10% evidence availability
+ 5% approved reuse status
Add “do not reuse” controls

Some old content should never be reused. B03 should exclude:

- Lost-bid content where feedback criticised that answer
- Superseded framework language
- Named former employees
- Expired insurance/certification claims
- Client-specific confidential details
- Old CCS wording where GCA wording is now required
- PCR 2015 / MEAT wording where PA23 / MAT applies
Return answer components, not just passages

For each result, return:

Reusable answer text
Relevant evidence
Case study
Metrics
Required edits
Risks
Source link
Approval status
Freshness status

That makes B04 much stronger.

B04 Response Drafter — add evaluator mapping and evidence ledger

B04 is a good drafting skill, but it needs a more bid-professional structure.

For every answer, require this before drafting:

Question:
Evaluation criterion:
Score/weighting:
Buyer pain:
Win theme:
Evidence available:
Evidence missing:
Answer structure:
Word/character limit:

Then draft.

The answer checker should also be upgraded. The current check_answer.py checks word count, keyword coverage and evidence placeholders. Useful, but too basic.

Add checks for:

- Forbidden stale terms: CCS, MEAT, PCR 2015, RM6263, G-Cloud 14, unless contextually valid
- Unsupported claims: “leading”, “expert”, “proven”, “extensive”, “robust”
- Missing buyer benefit
- Missing evidence citation
- Overuse of generic bid language
- Named people / clients without approval
- “We will” commitments that need commercial approval

Also add an evidence ledger per answer:

Claim	Evidence	Source	Owner	Status
We deliver Power Platform governance	Prior project / method	SharePoint link	Practice lead	Approved
We hold Cyber Essentials	Certificate	SharePoint link	Ops	Expires DD/MM/YYYY

This prevents impressive but unsupported prose.

B05 Pre-flight — make it two-stage, not just final-stage

B05 is very important. The EFS/FVRA and clarification-owner gates are exactly the right lessons.

But pre-flight should not happen only at the end. Run it twice:

T-minus 5 working days: readiness review
T-minus 1 working day: final submission gate

Or for short deadlines:

Midpoint review
Final review no later than 4 working hours before deadline
Fix the script

The current preflight.py can return READY if mandatory_rows or answers are empty. That is dangerous.

Make these blocking:

- No matrix supplied
- No mandatory rows found
- No answer list supplied where answers are required
- Any document marked unknown
- Any expiry date missing
- Any submission deadline missing date, time, or timezone
Make documents conditional

The current required document list is hard-coded. Better:

document_required: true/false
document_present: true/false
expiry_date
acceptable_for_this_bid: true/false
source_link

A Carbon Reduction Plan or Modern Slavery Statement may not apply to every procurement in the same way, so the skill should check applicability rather than always assuming.

B06 Clarification Management — needs mailbox/portal discipline and escalation

B06 is conceptually strong. It captures the actual failure mode: missed clarifications.

But the script needs more fields:

Field	Why
Deadline time	Date alone is not enough
Timezone	Portal deadlines can be unforgiving
Portal link	Direct source
Received via	Portal / email / buyer message
Owner	Main owner
Backup owner	Required
Evidence required	Attachments needed
Internal due date	Earlier than buyer deadline
Escalation date	When MD gets alerted
Status	Open / drafting / with reviewer / sent / closed
Sent by	Audit trail
Buyer confirmation	Proof response was received

Also, “daily check” is good, but for live bids I would make it:

Daily portal + mailbox check as minimum.
Twice daily during the final week or where any clarification is open.
Add B07 Outcome & Learning Update

This is essential if you want the library to improve.

After award, standstill, loss notice, or feedback, B07 should:

- Record result: won/lost/non-compliant/withdrawn
- Capture evaluator scores
- Capture buyer feedback
- Identify answers to promote into approved library
- Identify answers to retire or mark “do not reuse”
- Update case studies and evidence
- Update qualification assumptions
- Update pricing intelligence
- Record lessons learned

This closes the loop. Without B07, the library will slowly become stale.

SharePoint structure I would use

Use three SharePoint libraries/lists rather than one folder dump.

1. Bid Submissions Library

For complete historical bids.

/Bids/Submitted/[Year]/[Buyer] - [Opportunity]/

Metadata:

Buyer
Sector
Framework
RM code
Lot
Submission date
Outcome
Score
Bid lead
Service line
Procurement regime
Reusable? yes/no
Confidentiality
2. Approved Answer Bank

For reusable answer chunks, not whole documents.

Each record should be one answer or answer component.

Metadata:

Theme
Question type
Service line
Framework
Sector
Outcome source
Approved by
Approval date
Review date
Do-not-use flag
Evidence links
3. Evidence Register

For reusable proof.

Metadata:

Evidence type
Document owner
Expiry date
Approved for external use
Related claims
Related services
Link to source document

This is what makes auto-prefill reliable.

Skill-writing improvements

Across all skills, add the same sections:

Inputs required
Output required
Blocking conditions
Human review points
Do-not-do rules
SharePoint locations
Machine-readable output schema
Definition of done

For example, every skill should output both:

1. Human-readable summary
2. Structured JSON/YAML block for the next skill

That makes handoff much cleaner.

Example:

bid_id: FWF-2026-001
stage: compliance_matrix
buyer: Example Council
route: G-Cloud 15
deadline: 2026-07-31T12:00:00+01:00
mandatory_open_items: 4
evidence_gaps: 7
clarifications_to_raise: 2
next_skill: b03-answer-reuse
Priority changes

Do these first:

Rewrite B03 for SharePoint, not Drive.
Add B00 library ingestion/indexing.
Add B07 outcome/debrief update.
Expand B02 matrix columns for source traceability, evidence, review and submission status.
Make UNKNOWN a blocking state in B01 and B05.
Add evidence ledger checks to B04.
Upgrade B06 with deadline time, timezone, backup owner and escalation.
Bottom line

The current skills are a good workflow. To make them genuinely powerful for public sector bidding, turn them into a controlled reuse system:

old bids → structured SharePoint answer bank → evidence-checked retrieval → evaluator-focused drafts → human review → final compliance gate → clarification control → feedback loop

That will materially reduce bid-writing effort while still keeping the right human intervention at rework and final sign-off.