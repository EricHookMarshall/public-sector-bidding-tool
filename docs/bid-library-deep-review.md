# Bid library — deep review (13/07/2026)

A full pass over the SharePoint export: **504 files, 812 MB**, read in four batches
(spine / `02 Bid Library` / `03 FWF Bids` / `04 Portal Registrations`). This is a
point-in-time snapshot — **re-verify before relying on it**.

It pairs with [`gca_findings/FINDINGS.md`](gca_findings/FINDINGS.md) (the portal side)
and [`standard-answers.md`](standard-answers.md) (the store built from it). Several
findings below **correct** earlier conclusions, including two of my own.

---

## 1. Critical — act on these

### 1a. The ISO certificates belong to a different legal entity

The ISO 9001 and ISO 27001 certificates in `02 Bid Library/Company Credentials/ISO Certs/`
are issued to **FUTURE WORK FORCE SRL / S.R.L.** — the **Romanian** company in
Cluj-Napoca (the 9001 certificate even annotates the head-office address *"no activity"*).
They are **not** issued to Future Work Force Limited, company 11934102, which is the
entity that bids in the UK.

| Certificate | Entity | Expiry | Note |
|---|---|---|---|
| ISO 9001:2015 (BV `RO23.4749175Q`) | Future Work Force **SRL** (RO) | **08/01/2026** | expired |
| ISO 27001:**2013** (BV `IND.23.2004/IS/U`) | Future Work Force **S.R.L.** (RO) | **31/10/2025** | expired; superseded standard |

This is the most dangerous thing in the library and the least visible: the files are
named `FUTURE WORK FORCE - ISO 9001.pdf`, they sit in FWF's own credential folder, and
they read as "ours" to every automated check and every hurried human. **Answering a UK
selection question with another legal person's expired certificate is a
misrepresentation** — the kind that gets a bid disregarded rather than merely marked down.

**The real position, stated accurately:** FWF Ltd (UK) holds **no ISO certification in
its own right**. For 27001 there is a genuine group-level mitigation — Bureau Veritas
letter `L/BUH/06.11.2025/423/BCT` (Nov 2025) confirms **AROBS GROUP, explicitly naming
"Future Work Force"**, passed the **ISO 27001:2022** transition audit (audited 09–17 Oct
2025). But that is *group certification evidenced by a letter*, not an FWF Ltd
certificate, and the group certificate itself is not in the library. Say precisely that;
do not attach the lapsed SRL certificate.

### 1b. Live portal passwords in cleartext

`04 Portal Registrations/Portal Registration Tracker.xlsx` holds portal passwords in
plain text across its *Supplier Portals* and *Supplier Networks* sheets. The handover
already flagged this. Two things make it worse than a filing problem:

- Several passwords are **reused across portals**.
- They belong to a **departed employee's** accounts (`Emma.Selman@fwfcompany.com`).

These need **rotating**, not just moving. The folder is gitignored, so nothing has leaked
to git.

### 1c. CCS Management Information returns may be in breach

The tracker states plainly: *"Crown Commercial MI — **Must submit MI monthly**, AI DPS
RM6200, SPARK DPS RM6094"* (portal `reportmi.crowncommercial.gov.uk`). But
`07 CCS MI Reports/` contains **only the blank RM6200 template** — no submitted returns
for any month, for any agreement.

CCS DPS appointments carry a **monthly MI obligation including nil returns**;
non-submission attracts charges and can suspend an appointment. **Verify whether returns
have been filed** — if they're being submitted somewhere outside this folder, fine; if
not, this is a live contract-compliance breach on all three appointments.

### 1d. Cyber Essentials has lapsed

Certificate `7887de7c-3c00-4bea-abb2-e4495d9747a3`, issued to **Future Work Force
Limited** (correct entity, whole-organisation scope), certified **06/06/2025**.
Cyber Essentials runs 12 months → **recertification was due 06/06/2026**, so it lapsed
~5 weeks ago. The copy on file is also an **"INSPECTION COPY"** watermarked image, not a
clean certificate.

---

## 2. Corrections to earlier conclusions

### 2a. The insurance has NOT lapsed — the tracker is stale

Both the GCA review and my first version of the answer bank concluded FWF's insurance
expired on 27/05/2026. **It did not.** Reading the certificates themselves:

| Cover | Level | Policy | Period |
|---|---|---|---|
| Employers' Liability | £5,000,000 | `PL-PSC10002770678/11` | 28/05/2026 → **27/05/2027** |
| Public **and Products** Liability | £10,000,000 | `PL-PSC10002770678/11` | 28/05/2026 → **27/05/2027** |
| Professional Indemnity | £2,000,000 | `PL-PSC10002770678/11` | 28/05/2026 → **27/05/2027** |
| Cyber & Data | £1,000,000 | `PL-PSC10002770678/11` | 28/05/2026 → **27/05/2027** |

Cover is **current**, confirmed by the Hiscox policy schedule (`DC546`, effective
28/05/2026, annual premium £7,561.05). `Insurance Tracker.xlsx` was simply never updated
at renewal — it still lists the superseded `/08` policy.

Two consequences, both now fixed in [`src/answers.py`](../src/answers.py):

- **The bank reads the certificates, not the tracker.** A document issued by the insurer
  beats a spreadsheet row typed by someone who has since left. Trusting the tracker made
  the bank raise a *false alarm* that cover had lapsed — which is its own kind of wrong,
  and would have sent someone scrambling to re-buy insurance they already have.
- **Product Liability is not a gap.** The Hiscox certificate is a single *"public **and
  products** liability"* policy at £10m. The tracker has no products row at all, which is
  the only reason it looked missing. The past PSQ claim of £10m product cover was right.

### 2b. G-Cloud 15 was submitted, not skipped

`04 Portal Registrations/Frameworks/G Cloud 15/` holds **108 files** — a full Submission
Master with final PDFs for **Lot 2b (SaaS) and Lot 3 (Cloud Support)**, service
definitions, pricing, a compliance matrix and a clarification log.

This corroborates [`knowledge/01-current-position.md`](../knowledge/01-current-position.md):
the submission was **disregarded on 17 March 2026** at Stage 3 (Conditions of
Participation) on the **Financial Viability Risk Assessment** — *"failed to provide
financial statements; failed to clarify information."*

The folder makes the failure concrete and considerably more painful:
`03 Pricing/FVRA/AROBS/` contains **the Arobs 2023 and 2024 annual reports and the
completed FVRA Gold workbook**. **The parent-company financials that would have answered
the FVRA were prepared and were sitting in the folder — they just never got submitted,
and the clarification was never answered.** The whole project exists because of this.

---

## 3. More inconsistencies (the answer bank's core problem)

Beyond the four already in `KNOWN_CONFLICTS`, the deep read found the reference contracts
disagree between the library and the portal:

| | `Contract Examples.xlsx` (library) | Portal SQ2016 |
|---|---|---|
| Close Brothers — value | **£1,000,000** | **£2,000,000** |
| Close Brothers — referee | **Jag Bassi**, Head of Technology Product | **Steve Durnin**, Head of Op Ex & Automation |
| NHS Barnsley | £186,000 · 11/2022–11/2025 | same ✓ |
| Sephora | £505,000 | same ✓ |

The library also holds **five+** contract examples (adding Planet Payments £36k and LSEG),
not the three on the portal. A referee who doesn't expect the call, or a value that
contradicts what the buyer can see on another record, is a scored-question own goal.

---

## 4. Structural rot in `03 FWF Bids` (231 files, 27 bids)

- **Outcomes are not being captured.** Only **2 of 27** bid folders have anything in
  `07 Post Submission`. The two that do are both **loss letters with full scoresheets** —
  exactly the Learn-stage (Stage 6) data the tool wants, sitting unexploited:
  - **Northumberland CC** (NCC1547 Revenues & Benefits Automation, 4 Aug 2025) — lost to
    **Roboyo (UK Trading) Ltd**. Quality 49/65. Price **28.23/35 vs Roboyo's 33.13**.
    Lost on price, with **Social Value scoring 6/10**.
  - **Cardiff University** (CU.1982.TH Invoice Automation, 24 Jul 2025) — not in the top five.
  - `Tender Pipeline.xlsx` names two further losses (**WM5G AI**, **Commission Futures**).
- **Three names for one folder:** `02 Response Docs` (13) / `02 Response Drafts` (7) /
  `02 Response Documents` (6). Same for `04 Pricing & Financials` vs `...and Financials`.
  Any automation that walks this structure will silently miss a third of it.
- **Index collision:** `05 GCloud14` and `05 Scottish Water` both take index 05.
- **Botched duplicate tree** in `11 Efficiency East Midlands` (`00 Bid Admin1`,
  `01 Customer Documents1`, `07 Post Submission1`).
- **Two empty bid folders:** `03 The Insolvency Agency`, `08 Student Loan`.
- A stray **`.claude/settings.local.json`** committed inside `26 Office for Students`.
- `AI DPS RM62000` is a typo for **RM6200**.
- Two framework folders are **empty shells**: `MOD AI & Edge Framework DDAD`,
  `Public Sector Software Framework RM6396`.

---

## 5. Assets worth knowing about

- **`Tender Pipeline.xlsx`** is a three-part radar and is better than it looks:
  *Contracts Ending* (17 rows of competitor incumbency with expiry dates and values —
  DWP/UiPath £9.99m ending 10/2026, DVLA £4m, Lancashire £2.97m), *Upcoming Tenders*
  (pre-tender radar with named buyer contacts), and *Review* (bid outcomes).
- **`06 PS Contacts/Public Sector Orgs 2025.xlsx`** — a full UK public-sector org list
  (sector, industry, LinkedIn, employee range) for targeting.
- **`Defence Positioning.docx`** — a costed MOD pipeline (£500k–£40m programmes across
  Defence Digital, DE&S, DMS, DIO) and a named prime-partner strategy.
- **`00 Bid Management Framework/`** — an 11-theme capability framework + scored discovery
  assessment for the Romanian team.
- The **handover** names the CRM as **Pipedrive** and the discovery source as **BidStats**.
  Note `CLAUDE.md`'s deferred roadmap says *HubSpot* — one of the two is wrong.
- The handover's outstanding actions on Emma include *"upload question library and case
  studies to shared drive"*. **That question library was never delivered** — the Bid
  Library Tracker's `Templates → Standard Answer Bank` row is empty. It is precisely the
  gap the [standard-answer bank](standard-answers.md) now fills.

## 6. Caveats

- The ISO certificates and the Cyber Essentials certificate are **image scans with no text
  layer** — the entity and date findings above come from reading the rendered pages, not
  from a parser. They are recorded declaratively in `answers.py`
  (`WRONG_ENTITY_EVIDENCE`) with a verified date, and **must be re-checked** if the certs
  are reissued.
- `futureworkforcelimited-2025-06-11-12-04-39.pdf` looks like a Companies House export
  from its filename. It is not — it is the **Cyber Essentials assessment report**.
- Financial statements, turnover and the EFS position are **not** resolved here; the
  £100m-vs-<£36m contradiction from the GCA review still stands and still blocks the
  `annual_turnover` answer.
