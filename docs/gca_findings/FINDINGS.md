# GCA Supplier Registration — FWF Portal Review

**Prepared:** 13 July 2026
**Portal:** Government Commercial Agency (GCA) Supplier Registration Service — `supplierregistration.cabinetoffice.gov.uk`
(formerly Crown Commercial Service; renamed GCA on 1 April 2026). Shared login also covers Contracts Finder.
**Account:** Future Work Force Limited (SME) · DUNS 224987733 · Companies House 11934102 · VAT GB247160514
· Ibex House, 61 Baker Street, Weybridge KT13 8AH · joined 19/03/20 · signed in as Eric Hook-Marshall.

This folder is a point-in-time snapshot for review. Portal facts change — re-verify before relying on them.

---

## 1. Executive summary

FWF holds **three live DPS appointments** on the GCA portal — **AI DPS**, **RM6173 Automation Marketplace**
and **Spark DPS** — all in **APPOINTED** status. A fourth Automation Marketplace record (the original 2020
DPS) shows **REJECTED**, but that is the superseded legacy iteration, not a live rejection.

The material issues are **administrative, not commercial** — which mirrors the root cause this whole project
exists to fix (a missed clarification once killed a bid):

1. **Modern Slavery Assessment is unfinished** (status RESPONDING) and still names **Emma Selman** as the
   organisation's main contact. Emma's access is revoked.
2. **Legacy ownership throughout.** Emma Selman, Dan Johnson, Daniel Young and alastair roriston still appear
   as assigned users / contacts on numerous records. Notifications tied to departed staff are exactly how a
   clarification goes unanswered.
3. **A £100m turnover figure** is recorded on the MSA — almost certainly a group/consolidated number. Worth
   confirming it is intended and consistent with EFS declarations elsewhere.

The three live DPS records are, sensibly, on a shared **"DPS Email Notifications"** account rather than a
personal mailbox — keep and extend that pattern.

---

## 2. Live framework / DPS memberships (the "contracts")

| Agreement | Status | Dashboard ID | Reference | Notes |
|---|---|---|---|---|
| **AI DPS** (Artificial Intelligence) | ✅ APPOINTED | DPS154818 | SQ-A3P6TMM | Appointed via 2025 re-registration; assessor Lydia Hoy |
| **RM6173 Automation Marketplace** | ✅ APPOINTED | DPS234745 | SQ-GYHB4TU | Appointed 23/09/25; assessors Lydia Hoy / Emily Curtis. Covers RPA, IA, AI, ML consultancy |
| **Spark DPS** | ✅ APPOINTED | DPS269319 | SQ-3PG928A | Appointed 17/09/25; assessors Latisha Bagley / Julie Leeds |
| DPS_AUTOMATION_MARKETPLACE (2020) | ❌ REJECTED | DPS97416 | SQ-7VA7B4R | **Legacy** — original 2020 DPS, expiry 21/04/23, superseded by RM6173. No action |

Full per-agreement submission detail (self-certifications, insurance levels, cyber, workflow history) is in
[`captures/`](captures/). Highlights common to all three live appointments:

- **Insurances self-certified:** Employer's Liability £5m+, Public Liability £1m+, Professional Indemnity £1m+
  (evidence to be provided to GCA on request).
- **Cyber:** FWF holds **Cyber Essentials** (not Plus); agrees to provide the certificate on appointment.
- **Standard declarations:** Equality & Diversity policy ✔, no data-protection breaches, Supplier Code of
  Conduct ✔, no mandatory/discretionary exclusion issues, single economic operator (0 GEO members).
- **Companies House number 11934102** used consistently.

---

## 3. Compliance — Modern Slavery Assessment (MSA V.2)

Three MSA records exist on the account; the one that matters is **FWF's own**:

| Record | Status | Score | Owner | Note |
|---|---|---|---|---|
| **FUTURE WORK FORCE LIMITED** | ⚠️ RESPONDING (incomplete) | N/A | Ana Roxana Pana | Not submitted; contact = Emma Selman (stale) |
| 1584654809 | RESPONDING | N/A | Dan Johnson | Legacy duplicate |
| IBPA Consulting Ltd | COMPLETED | Amber / 25% | Dan Johnson | Different legal entity |

**What's outstanding on FWF's MSA** (see [`captures/Modern_Slavery_Assessment_FWF_capture.md`](captures/Modern_Slavery_Assessment_FWF_capture.md)):
- Assessment is **not submitted** — buyers see no completed MSA.
- **Main contact is Emma Selman, Bid Manager** — needs reassigning to a monitored owner.
- Q14 (purchasing-practice risk) answered **No**; Q17 highest-risk = "Have not identified"; Q18 = "have **not**
  investigated our suppliers' modern slavery risks." These weaken the profile — worth strengthening before submit.
- **Turnover recorded £100,000,000** (accounts end 04/02/2024) — confirm this is the intended (group) figure.
- Good side: modern-slavery policies exist and are publicly available, senior-approved, staff trained.

---

## 4. Full questionnaire register

The complete portal register (17 rows) is exported to
[`downloads/questionnaire_register_export.csv`](downloads/questionnaire_register_export.csv). It lists every
DPS, Selection Questionnaire (current + 2016 format) and MSA record with status, reference, last-edited date,
assigned owner and owner email — useful as the single source for the ownership clean-up below.

---

## 4b. Deep dive — full SQ2016 responses (all answers) + data-quality issues

The DPSQ "View" pages only show a read-only *index* of the underlying Selection Questionnaire. The actual
80-question SQ2016 answers live in the separate "Selection Questionnaire 2016" records — now captured in full
in [`captures/full/`](captures/full/) for all three live agreements. Highlights and issues:

**Clean compliance position (all three):** every mandatory (Q105–113) and discretionary (Q114–126) exclusion
ground answered **No**; SME **Yes**; no Person of Significant Control; tax/social-security clean.

**Reusable bid intelligence — three reference contracts** (identical across all three SQs; strong asset for the library):

| Customer | Referee | Value | Dates | Scope |
|---|---|---|---|---|
| NHS Barnsley NHS Trust | Tom Davidson, Direct ICT | £186,000 | 11/2022–11/2025 | Power Platform automation & low-code (Referral Mgmt, Finance & HR) |
| Sephora | Magdalena Ciudin, IT Finance Div Mgr | £505,000 | 06/2022–06/2026 | UiPath + Power Platform automation, 7+ EU countries |
| Close Brothers | Steve Durnin, Head of Op Ex & Automation | £2,000,000 | 03/2023–03/2026 | Automation/cloud/analytics across OutSystems, UiPath, Blue Prism, Alteryx, Power Platform, Azure AI |

**EFS / Parent Company Guarantee:** all three SQs answer **Yes** to "would the parent company be willing to
provide a guarantee if necessary?" and Yes to providing parent accounts — directly supporting the PCG remedy
that sits at the centre of this project.

**⚠️ Data-quality issues to fix before these are relied on in a live bid:**
1. **Turnover contradiction (material).** All three SQs state *"We do not turnover more [than] 36 million
   annually"* and answer **No** to Modern Slavery Act s.54 — while the **Modern Slavery Assessment records
   £100,000,000**. One is wrong. This is the exact EFS/turnover question the whole engagement turns on —
   reconcile it and be consistent everywhere (standalone FWF vs Arobs group).
2. **Cyber Essentials inconsistency.** FWF holds CE (dated **06/06/2025**, serial `7887de7c-3c00-4bea-e4495d9747a3`,
   captured on the RM6173 record). But the **AI DPS and Spark SQ2016 records still answer "No" to Q155** —
   update both to Yes so all three are current.
3. **Spark record has the wrong website** — `aispace.co.uk` (the legacy AiSpace domain) instead of
   `fwfcompany.com`.
4. **Three different company names in play:** legal *Future Work Force Limited*, trading *Future Work Force
   Company Limited*, and the supply-chain narrative says *FWF Solutions*. Pick one convention.
5. **Contact = Emma Selman** on the declaration of all three SQs — reassign.

## 4c. Deepest layer — DPS appointed scope + named role-holders (previously-collapsed sections)

Below the SQ2016 on each record sit further collapsed sections defining the **appointed scope** and the
**named role-holders**. Full detail in [`captures/full/DPS_profile_scope_and_roles.md`](captures/full/DPS_profile_scope_and_roles.md). Two findings here are as important as the turnover issue:

**A. Emma Selman is the named agreement contact across all three live DPS.** The DPS Agreement Manager /
Authorised Representative / Marketing Contact roles resolve to Emma (departed) on AI DPS, RM6173 and Spark;
RM6173 additionally has her as Compliance Officer. The DPS Agreement Manager is *the* contact GCA and buyers
use — this is the precise failure mode (contact = departed employee) that this project exists to prevent.

| Role | AI DPS | RM6173 | Spark |
|---|---|---|---|
| DPS Agreement Manager | Emma Selman | Emma Selman | Emma Selman (contact) |
| Authorised Representative | Emma Selman | Emma Selman | — |
| Compliance Officer | Daniel Young | Emma Selman | — |
| Data Protection Officer | Daniel Young | (verify) | — |
| Marketing Contact | Emma Selman | Emma Selman | — |

**B. AI DPS (RM6200) appointment form shows Expiry Date 11/04/2026 — already in the past.** The dashboard
still says APPOINTED and the record notes "2 optional extension periods of up to 12 months," so it may have
been extended — but this needs confirming urgently. (RM6173 expiry 15/11/2026 is fine.)

**Appointed scope (usable for bid-qualification / where FWF can compete):**
- **AI DPS:** Scope of Engagement = AI Discovery, Licencing, End-to-End Partnerships, Customisation & Support;
  Applications = RPA, ML, Deep Learning, Generative AI; **all sectors** (Blue Light, Central Gov, Devolved,
  Health, Local Gov, Not-for-profit, Defence & Security, Education, Culture/Media/Sport). Signed **Data Ethics
  Letter of Understanding** attached.
- **RM6173:** all four service categories (Design, Build, Live, Software Licences) — automation/RPA-led.
- **Spark:** broad sector ticks but **sub-services mostly blank** for Transport/Defence/Police/Fire/Education
  (a real scope gap); UK-wide (all 9 England regions); Security = Official only.

## 5. Recommended actions

**Administrative / hygiene (do first — cheap, high-value):**
1. **Complete and submit FWF's Modern Slavery Assessment**, and reassign its main contact away from Emma Selman.
2. **Reassign every named DPS role** (Agreement Manager, Authorised Representative, Compliance Officer, DPO,
   Marketing Contact) on AI DPS, RM6173 and Spark away from Emma Selman to a monitored owner — see §4c table.
   Confirm Emma's user access is fully revoked under **Manage your users**.
2a. **Urgently verify AI DPS (RM6200) is still live** — its appointment form shows an expiry of 11/04/2026,
   already passed; confirm it has been extended or re-appoint.
3. **Reconcile the turnover figure** (£100m on the MSA vs "<£36m" on all three SQs) and fix the SQ2016
   data-quality issues in §4b — Cyber Essentials answers (AI DPS, Spark), Spark's `aispace.co.uk` website,
   and the inconsistent company naming — before any of these records feed a live bid.

**Housekeeping:**
4. Note the 2020 REJECTED Automation Marketplace record is legacy — no action, but flag so it isn't misread.
5. Keep evidence current for the two agreements exposing **"Update Evidence"** (RM6173, AI DPS) — Cyber
   Essentials certificate and insurance evidence in particular.

**For the record:**
6. Download the Financial Report PDF and the per-agreement "Download questions" exports into `downloads/`
   (steps in [`downloads/README.md`](downloads/README.md)).

---

## 6. Evidence gaps / caveats

- **Financial Report PDF** and the portal-native **"Download questions"** exports are binary/authenticated
  downloads that could not be routed into this folder automatically — manual fetch steps are in
  `downloads/README.md`. All other content here was read directly from the live portal.
- This is a **13/07/2026 snapshot**. Statuses and assigned owners change — re-check on the portal before acting.
- Assessor names and workflow timestamps are transcribed from the portal's workflow history as-is.
