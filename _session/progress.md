# Progress — cold history

> **Immutable, newest-first** — prepend a new dated entry per session; never edit or delete old ones.
> The current hot state lives in [handover.md](handover.md); this is the retrospective trail behind it.

## 2026-07-13 (session 25) — A-series answer bank + a full deep read of the bid library (504 files)

**Context.** Resumed from session 24 (`4cbd18d`). The user's ask was not on the backlog: *"analyse the data in
the findings and build data stores for consistent responses to questions that do not require reasoning — e.g.
do you have a modern day slavery policy, yes, location of file to upload."* They then asked for a deep,
batched read of the whole SharePoint export.

### What shipped — the standard-answer bank (A-series)

`src/answers.py` + `standard_answers` table (`db.py`) + 4 endpoints (`api.py`) + `tests/test_answers.py` (24).
Docs: [`docs/standard-answers.md`](../docs/standard-answers.md).

The design decision that matters: **it is a lookup, not a generator.** Each of these questions has exactly one
correct answer, it is a matter of record, and a model can only add the chance of getting it wrong. So the bank
answers **from record, with provenance — or it refuses.** Anything needing judgement (the H&S narrative, GDPR
technical measures) stays with Complete/AI pre-fill and is deliberately *not* in the bank.

**Question definitions are committed; values are not** — values are company data, seeded into the gitignored
`bids.db` from the gitignored library export at startup, through the existing `LocalMirror` seam. Re-seeds on
**every** start (the library moves: a policy gets filed, a cert renewed), keyed on `answer_key`, and **never
overwrites a human-verified value**.

**The readiness gate** is what makes it safe to auto-fill from. Status is derived live against today, never
stored. Only `ready` may be auto-filled. Ordered so nothing can route around a problem to reach it:
`wrong_entity` → `conflict` → `confirm_per_bid` → `gap` → `evidence_missing` → `evidence_expired` →
`unverified` → `ready`.

**Seeding against the REAL library (not a fixture) exposed six ways a "simple lookup" produces a confident
wrong answer.** Each now has a regression test. Every one of them failed *toward* a confident yes:

1. **The buyer's own form answered as ours.** Evidence search reached into `03 FWF Bids/`, found Scottish
   Water's blank `Supplier Modern Slavery Declaration.docx` — *a form the BUYER sent us to fill in* — and
   answered "Do you have a Modern Slavery policy?" with **Yes, here's the file.** Evidence is now confined to
   `02 Bid Library/`. A correctness boundary, not tidiness.
2. A greedy `\S+` ate the separator between two expiry dates in one tracker note (`09/01/2026 2700`),
   swallowing the `27001` marker — so a **lapsed ISO 27001 came back with no expiry, and read as fine**.
3. A certificate the library itself named `..._Expired.pdf` resolved to `ready`.
4. "Most recent audited accounts" picked **2022** over 2024.
5. A cert with **no expiry on record** read as `ready` — silence is not evidence of validity (`unverified`).
6. **The stale tracker (a FALSE alarm)** — see the correction below.

**The answer to the user's literal question: FWF does NOT have a Modern Slavery policy.** No such document
exists in the library. The Bid Library Tracker lists *"Anti-Bribery & Modern Slavery Policies — aligned to
Public Contracts Regulations"* with no owner, no date, no file. **A tracker row is an intention, not a
policy** — which is exactly why the bank checks the filesystem rather than trusting the tracker.

**Then `docs/gca_findings/` reframed the task.** The GCA review proves FWF has answered *the same
no-reasoning questions three different ways across three live portals* (Cyber Essentials Yes on RM6173 / No on
AI DPS + Spark; PI declared £10m against a £2m policy; turnover £100m on the MSA vs "<£36m" on all three SQs;
three variants of the legal name). **That is the disease the bank exists to cure** — and a bank that silently
picked a side would *industrialise* the inconsistency. Hence `conflict`: never auto-fillable, cites the
finding, stays flagged until a human reconciles it.

### The deep read — all 504 files / 812 MB, in 4 batches

Full write-up: [`docs/bid-library-deep-review.md`](../docs/bid-library-deep-review.md). It **corrects two
earlier conclusions** (one of them mine) and surfaces **three business-urgent items**.

**🔴 The ISO certificates belong to a different legal person.** ISO 9001 (BV `RO23.4749175Q`, exp 08/01/2026)
and ISO 27001**:2013** (BV `IND.23.2004/IS/U`, exp 31/10/2025) are both issued to **FUTURE WORK FORCE SRL** —
the **Romanian** sister company in Cluj-Napoca; the 9001 even annotates its head-office address *"no
activity"*. **Not** Future Work Force **Limited** (UK, CH 11934102), the entity that bids. Both are also
expired. This is the most dangerous thing in the library and the least visible: the files are named
`FUTURE WORK FORCE - ISO 9001.pdf` and sit in FWF's own credentials folder, so they read as *ours* to every
automated check and every hurried human. **Answering a UK selection question with another legal person's
expired certificate is a misrepresentation** — the kind that gets a bid *disregarded*, not merely marked down.
Truth: **FWF Ltd holds no ISO certification of its own.** For 27001 there is a genuine group mitigation — BV
letter `L/BUH/06.11.2025/423/BCT` confirms **Arobs Group, explicitly naming "Future Work Force"**, passed the
**ISO 27001:2022** transition audit (09–17 Oct 2025) — but that is **group** certification evidenced by a
**letter**, not an FWF Ltd certificate, and the group certificate is not in the library. New `wrong_entity`
status: outranks everything, because it is not a data-quality problem, it is a misrepresentation. The certs
are **image scans with no text layer**, so no parser can see this — recorded declaratively in
`WRONG_ENTITY_EVIDENCE` with a verified date. **Re-check if reissued.**

**🔴 CCS MI returns look unfiled.** The portal tracker states plainly: *"Crown Commercial MI — **must submit MI
monthly**, AI DPS RM6200, SPARK DPS RM6094"*. But `07 CCS MI Reports/` contains **only the blank RM6200
template** — no submitted returns, any month, any agreement. CCS DPS appointments carry a monthly MI
obligation **including nil returns**; non-submission attracts charges and can **suspend an appointment**.
Verify whether they are filed elsewhere; if not, this is a live breach on all three appointments.

**🟠 Portal passwords.** Known since session 24, but worse than filed: **reused across portals**, on a
**departed employee's** accounts. They need **rotating**. (My own redaction filter caught the `Password`
column but missed the `PW` columns on two other sheets, so some printed into the session transcript — another
reason to rotate.)

**CORRECTION — the insurance has NOT lapsed; the tracker is stale.** Both the GCA review *and* the first cut
of the answer bank concluded cover expired 27/05/2026. It did not. The Hiscox **certificates** show policy
`PL-PSC10002770678/11` running **28/05/2026 → 27/05/2027**: EL £5m, Public **and Products** Liability £10m,
PI £2m, Cyber £1m — confirmed by policy schedule `DC546` (annual premium £7,561.05). `Insurance
Tracker.xlsx` was simply never updated at renewal. **Reading it made the bank raise a false alarm that cover
had lapsed — every bit as damaging as a missed expiry**, and it would have sent someone scrambling to re-buy
insurance they already hold. **Fix: `answers.py` now reads the certificates (`insurance_from_certificates`,
pypdf); the tracker is only a fallback.** *A document issued by the insurer beats a spreadsheet row typed by
someone who has since left.* Knock-on: **Product Liability is not a gap** — it is the same "public **and
products** liability" certificate at £10m, and the tracker simply has no products row.

**Cyber Essentials HAS lapsed.** Cert `7887de7c-…`, issued to Future Work Force **Limited** (correct entity),
whole-org scope, certified 06/06/2025. CE runs 12 months → **due 06/06/2026**, so ~5 weeks past. Expiry is
**derived** (cert date + 12 months) because nothing in the library ever writes it down.

**The founding failure, in files.** `04 Portal Registrations/Frameworks/G Cloud 15/` holds **108 files** — a
full Submission Master for Lots 2b and 3 — corroborating `knowledge/01-current-position.md` (disregarded
17/03/2026 at Stage 3 on the FVRA: *"failed to provide financial statements; failed to clarify"*). And
`03 Pricing/FVRA/AROBS/` contains **the Arobs 2023 + 2024 annual reports and the completed FVRA Gold
workbook**. **The parent-company financials that would have answered the FVRA were prepared and sitting in the
folder — they just never got submitted, and the clarification went unanswered.**

**Other findings.** Only **2 of 27** bid folders have anything in `07 Post Submission` — and both are **loss
letters with full scoresheets** (Northumberland CC lost to **Roboyo** on *price*: 28.23/35 vs 33.13, with
Social Value 6/10; Cardiff Uni missed the top five). That is Stage-6 data sitting unused. Structural rot:
three names for one folder (`02 Response Docs`/`Drafts`/`Documents`), an index collision (`05` used twice), a
botched duplicate tree in `11 Efficiency East Midlands`, a stray `.claude/` inside `26 Office for Students`,
two empty bid folders, `AI DPS RM62000` (typo for RM6200). The reference contracts **disagree** between the
library and the portal (Close Brothers: £1m/Jag Bassi vs £2m/Steve Durnin). The handover names the CRM as
**Pipedrive** (CLAUDE.md's roadmap says HubSpot — one is wrong) and lists an outstanding action on Emma to
*"upload question library and case studies"* — **that question library was never delivered.** It is precisely
the gap this session's bank fills.

### Verification

`make check` **green: 142 backend tests** (118 + 24 answers) + doc-consistency + vite build. `ruff` clean on
all new/touched files (`api.py`'s E402s are pre-existing and deliberate — it calls `_load_dotenv()` before
imports). Live end-to-end via uvicorn on a **fresh DB**: the bank auto-seeded 33 answers from the real library,
and `GET /api/answers/lookup?q="do you have a modern day slavery policy"` returned **`status=gap`, match 1.0**,
*"the honest answer is No"* — while Health & Safety returned `ready` with the file path to attach.

### Carried forward

Escalate the three findings (they outrank any code task). Then build the **Answers UI** — the bank is
API-only. Session-24 items (GCA overlay into `framework_positions`; mine tender refs from inside bid docs)
remain open and cheap.

## 2026-07-12 (session 24) — G1 "bids we lost": bulk-feed unlock + lost-bid resolver (2 real losses)

**Context.** Resumed from session 23 (`83c91f8`). The queued next action was "keep API-searching for the NHS
Barnsley award" — the user **explicitly dropped that thread** ("ok ignore nhs but lets look into the others")
and redirected to the 27 real bid folders in the SharePoint export. Session 23's verdict (Barnsley is not in
public OCDS) stands and was not reopened.

**Finding 1 — the bid library does not hold our win/loss history, and one file actively misleads.**
Surveyed the gitignored export (`knowledge/SharePoint Folder/Bids/`, 512 files, 27 bid folders).

- **`D365 Awards.xlsx` is NOT our awards.** Despite the name, every row is an award to a *different* company —
  Hitachi Solutions, Ceox, EY, Softcat, AvePoint, HSO. It is **market intelligence**. Same for
  `Tender Pipeline.xlsx` → *Contracts Ending* (incumbents' contracts expiring — a re-compete prospect list).
  An importer pointed at either would have written **10 false FWF records** into the `awards` table. The user
  flagged the risk in advance ("be careful, there is a mix of details") and was right.
- **The only real FWF outcome data in the entire export is 2 malformed rows** in Tender Pipeline → *Review*:
  "WM5G AI Proposition" = Not Won, and "Commision Futures Programme" = `Not Won]` (stray bracket, typo'd
  buyer). Dates in that sheet contradict each other (submission due *after* the closed date).
- **Folder evidence is a prior, not truth.** `06 Final Submission` populated → submitted (6 bids); drafts only
  (9); empty (12). But **WM5G shows "drafted-only" while the Review sheet records it as Not Won** — you cannot
  lose a bid you didn't submit, so it *was* submitted via a portal with no copy saved back. Confirmed false
  negative; the folder tree cannot be trusted as the record. **FWF has bid ~27 times and recorded the outcome
  twice.** That is the same admin gap that killed the bid this project exists to prevent.

**Finding 2 — the OCDS APIs structurally cannot answer "who won?".** (Probed, not assumed.)

- **Find a Tender** enumerates its allowed params in its own 400: `stages, limit, cursor, updatedFrom,
  updatedTo`. No buyer, no supplier, no keyword.
- **Contracts Finder SILENTLY IGNORES unknown params.** A `keyword=zzzznonsense` control returned *the same
  rows* as a real keyword. That is worse than a 400 — a keyword search there looks filtered and is not.
- Therefore the window must be read **whole** and matched client-side. Cost: pages are 20–55s → **~10 hours
  serially** for 14 months. **Parallelising the API failed completely: 126 of 126 shards, 124 × HTTP 429.**
  (So session 23's "the 429s were the VPN" was only half the story — *concurrency* triggers them too. The
  crawler exited 0 while achieving nothing; only its honest error-recording revealed the 100% failure.)

**Finding 3 — the unlock is bulk data (user's steer: "wasn't there something with archive data?").**
data.gov.uk publishes the same notices as **one CSV per day on S3** — bucket `cdp-sirsi-production-cfs-*`,
i.e. the **Central Digital Platform**, so under the Procurement Act 2023 it carries central-government notices
too (empirically: Home Office, UK SBS, Office for Students all present). S3 is not the throttled API, so it
parallelises safely.

- **`src/cf_bulk.py`** (new) — daily bulk OCDS extracts, 10 workers, cached per-day + resumable, atomic writes,
  missing days reported (never silently a zero). **2025-05-01 → 2026-07-12 = 47,797 unique notices in 12.3
  minutes, 0 failed days.** Window derived from the folders' own mtimes (bid activity May 2025 → Jan 2026).
  Caveat handled in code: the CSV's **column set varies by day** (1372 cols one day, 574 the next), so the
  parser walks award/supplier/party indices rather than assuming columns exist.
- **Coverage gap, on the record:** the feed is CF/CDP only. **PCS (Scotland) and Sell2Wales (Wales) are
  absent** → a `NO MATCH` for Forestry and Land Scotland / Scottish Water / Cardiff Uni is a coverage gap,
  **never** a loss.

**Finding 4 — `src/bid_outcomes.py` (new) resolves folders → notices → outcome. It PROPOSES, never asserts.**
Ranked evidence tiers: `ref` (buyer's own tender reference in the notice — near-proof) > `title` (buyer +
a *distinctive* title word) > `buyer` (a lead, not a match). Nothing is written to `bids.db`.

- **CONFIRMED LOSS — `22 UK BS (ACAS)`:** ref `PS25317` matched exactly → *"Ai Discovery for Early Conciliation
  & Helpline"*, buyer UK SBS → won by **Informed Solutions Ltd, £100,000, awarded 2026-02-13**.
- **PROBABLE LOSS — `25 Home Office PPPT`:** → *"PPPT Protective Monitoring"* → **Police Digital Services,
  £426,873**. Needs human confirm — PPPT is a programme, so this may be a sibling procurement.
- Remainder: **20 buyer-leads, 5 no-match, 1 excluded** (G-Cloud 14 = a *framework application*, not a tender —
  it has no award notice naming FWF, so scoring it would only manufacture noise).

**Two false positives — both confident, both wrong, both now pinned in tests.**

- **Buyer-name leak:** folder `25 Home Office PPPT` shares {home, office} with *"Home Office - Strategic Cost
  Review"* → reported **LOST to PwC**. A buyer-name collision was being laundered into the stronger `title` tier.
- **Geography leak:** folder `20 West Midlands WM5G` shares {west, midlands} with WMCA's *rail-fares* and *Ring
  & Ride* awards → reported **LOST to WSP**, a transport consultancy. **The bid library's own "Not Won" row for
  WM5G is what caught it** — the one piece of ground truth we had, earning its place.
- Fix: subtract the buyer's name **and every alias's tokens** before scoring a title match; if nothing
  distinctive survives (WM5G reduces to the empty set) the bid has *no* title signal and degrades to a buyer
  lead. **`LOST` fell 9 → 2.** `tests/test_bid_outcomes.py` (7 tests) pins both leaks, the ref tier, the
  CH-number win path, and "unmatched ≠ lost".

**Finding 5 — the framework folders were the other half of the value (`src/framework_positions.py`, new).**
G-Cloud 14 was excluded from win/loss as "a framework application, not a tender" — correct, but the user
pushed back that the framework *detail* is useful regardless. It is: G2's radar carried a hand-written
`fwf_status` caveated "internal fact — confirm on the Digital Marketplace", while FWF's own framework folders
hold the evidence. Reading them (LocalMirror seam, same as `library.py`; `available: false` when the export
is absent) shows:

- **The radar and reality disagree.** Radar: G-Cloud 15 = `not_member`, recommendation **"prepare"**. Library:
  **108 files and a drafted response**, last touched 2026-01-30. Surfaced as `contradicts_radar` / *"⚠ Already
  in flight"* — a prioritiser that tells you to start what you've half-finished is worse than useless.
- **Six agreements FWF is actively working on were invisible to the radar:** Bluelight Commercial, DDaT-NSW,
  KCC Digital Transformation, Spark DPS (RM6094), AI DPS (RM6200), Automation Marketplace DPS (RM6173). Now
  listed as *"Also in flight — not on the radar"*.
- **Two are empty scaffolds** — MOD AI & Edge (DDAD) and Public Sector Software (RM6396): 0 files. Intent, not
  work, and now labelled as such rather than counting as pipeline.
- **Honesty ceiling, pinned in tests:** a folder proves WORK, never MEMBERSHIP. The ladder is
  `planned` → `preparing` → `response_drafted` and stops there — the export cannot tell us a response was
  *submitted*, let alone accepted. No "member" label exists in the UI for that reason.
- Wired: `GET /api/frameworks/positions`, radar annotated at `GET /api/frameworks/radar`, `FrameworksView`
  section + badges. `tests/test_framework_positions.py` (8, offline against a fake export tree).
- Source typo handled on read, not rewritten: the real folder is `AI DPS RM62000` (a typo for RM6200).

**Verification.** `make check` green — **118 backend tests** (103 + 7 bid-outcomes + 8 framework-positions),
doc-consistency, vite build. `bid_outcomes.py` re-run from the repo reproduces the same 2/20/5/1 split; radar
annotation live-verified via TestClient. **`bids.db` untouched** (awards still 1 manual NHS Barnsley record).

**Also surfaced (not code).** `04 Portal Registrations/Portal Registration Tracker.xlsx` stores **plaintext
portal passwords**. Gitignored, so nothing leaked to git — but it needs raising with Emma.

**Next.** 20 of 27 bids stall at "buyer seen, bid not identifiable" because folder names carry no subject
words, and only 6 folders yield a tender ref from *filenames*. The refs and real titles are **inside** the docs
(`00 Bid Admin/FOR001 …xlsx`, `01 Customer Documents/` ITT files). Mine those → ref-grade matches for most of
the 20. **The feed is already cached; this needs no further crawling.** Then design the human confirm step that
writes an accepted verdict through Stage 6 (Learn) to feed the win-rate loop — never auto-import.

---

## 2026-07-12 (session 23) — Award-refresh diagnosis (VPN) + G1 manual award capture (NHS Barnsley)

**Context.** Resumed from session 22 (G-series, `699bbd4`). User asked "what's next?" → chased the open
session-22 thread: get a clean award refresh so FWF's own awards populate. The specific target emerged in
conversation: FWF has won exactly **one** public-sector contract — with **NHS Barnsley, ~3–4 years ago**.

**Diagnosis (the refresh 429s).**

- **It was the VPN.** The session-22 RATE_LIMITED verdict blamed our own smoke-test hammering; wrong. The user
  had a VPN running whose **shared exit IP** was the throttled one. With it off (a normal residential IP),
  a 7-day `--no-db` probe walked **930 award notices with zero 429s**. A subsequent full 4-yr run still took
  42 min (killed) — the full-feed walk is impractical AND `_fetch_source` caps at `max_pages=200` (~5 months of
  feed volume), so "4-yr window" ≠ "4 yrs scanned". A durable timestamped attempt log now lives at
  `_session/award_refresh_log.md` (start/end BST, window, exit code, output) so retries have a real clock.
- **The NHS Barnsley award is NOT in public OCDS under FWF.** Verified CH `11934102` = "FUTURE WORK FORCE
  LIMITED" (active, SIC 62020) — the matcher key is correct. But Contracts Finder supplier search + web search
  under both spellings ("Future Workforce" / "Future Work Force") surface **no** NHS Barnsley award to FWF (only
  the unrelated national NHSBSA/Infosys ESR deal). Website search and the OCDS feed read the same data, so more
  scanning won't change it. Likely the notice named FWF **without a CH identifier** (the GB-COH matcher then
  correctly won't record it — no false record), was **sub-threshold**, or FWF was a **subcontractor**.

**Work done — G1 manual award capture** (public OCDS can't surface a real win → let an Admin record it by hand).

- **Backend.** `POST /api/awards/manual` + `DELETE /api/awards/{id}` (Admin), new `db.delete_award`. Stored
  under a DISTINCT source `Internal record (manual)`, `supplier_scheme = "MANUAL"` (never GB-COH), `status =
  "unverified"` — honest provenance, never dressed up as a public match, and **untouched by the OCDS refresh**
  (different source key). At-least-one-of title/buyer/supplier required (422 otherwise). Bug caught + fixed:
  `upsert_award` doesn't self-commit (callers do), so the endpoint commits explicitly like `own_awards.run`.
- **Frontend.** `AwardsView` "Record a known award" collapsible form (title/buyer/supplier/date/value/term/note),
  `unverified` badge on manual cards, Remove control; KPIs now show when any award exists (not only when CH-set).
- **Data.** Seeded the NHS Barnsley record into `bids.db` (buyer + supplier + provenance note; blanks elsewhere).
- **Tests.** `tests/test_manual_awards.py` (5) incl. a "manual record survives an OCDS refresh" guard. Full
  `make check` green: **103 backend tests** (was 98), doc-consistency, vite build. Live-verified via uvicorn:
  POST → board total 1, empty → 422, DELETE-missing → 404, persisted to disk.

**Next task.** Continue searching the APIs for the NHS Barnsley award's details (date-boxed 3–4yr OCDS walk with
date-chunking to beat the 200-page cap; buyer/keyword angles) to enrich the manual stub — or confirm definitively
it isn't published. Also: click G1/G2/G3 in a live browser (still API+build-verified only).

## 2026-07-12 (session 22) — G-series: how-to-supply reference (G3) + own-awards (G1) + framework radar (G2)

**Context.** Resumed from session 21 (F-series polish, `1a8f7ae`). User asked "what's next?"; agreed to work
the recommended order of the deferred G-series (GCA/frameworks intelligence): G3 → G1 → G2.

**Work done.**

- **G3 — How to supply** (`src/supply_reference.py`, `GET /api/supply/reference`, `web/src/SupplyGuideView.jsx`
  at `#supply`, TopBar 📘). Curated, read-only reference: 5 routes to market (Frameworks, Dynamic Markets, DPS,
  Catalogues, finding notices) + a novice getting-started path + help/registration links. Honest-provenance
  pattern: a `source` link per route + a doc-level `verified` date (2026-07-08, mirrors VERIFIED_FACTS) + a
  re-verify disclaimer. No DB, no live fetch. `tests/test_supply_reference.py` (4).
- **G1 — Our contracts** (`src/own_awards.py`, `awards` sibling table in `db.py`, `web/src/AwardsView.jsx` at
  `#awards`, TopBar 🏆). Pulls FWF's OWN awards from the OCDS **award** packages (Find a Tender + Contracts
  Finder) and matches FWF by **Companies House number** (scheme GB-COH) — the one unambiguous identifier, so no
  false records (a buyer sharing the number is excluded; leading-zero tolerance; inline-supplier fallback). The
  number is app config (`own_org` in app_settings, `11934102` set in bids.db), never hardcoded — empty = inert.
  New DB helpers `upsert_award`/`list_awards` (dedupe on `(source, award_id)`). API: `GET/PUT
  /api/settings/own-org`, `GET /api/awards/board`, `POST /api/awards/refresh` (Admin; surfaces
  `incomplete`+failed-source count, raw errors server-side only). `tests/test_own_awards.py` (8).
- **G2 — Framework radar** (`src/frameworks_radar.py`, `GET /api/frameworks/radar`, `web/src/FrameworksView.jsx`
  at `#frameworks`, TopBar 📡). Curated candidate GCA agreements (G-Cloud 14/15, RM6190 TS4, DOS7, RM6263) but
  **lifecycle + recommendation computed LIVE against today** (act/pursue/prepare/maintain/watch/skip) — the
  antidote to the RM6263 "still listed after it expired" failure. Projected dates flagged; source per agreement.
  `tests/test_frameworks_radar.py` (6).

**Verification.** `make check` green — **98 backend tests** (was 80; +18), doc-consistency, vite build clean
(135.92 kB). Live via uvicorn: all new endpoints respond correctly; **G1's matcher fired on real live FTS award
data** (Softcat Plc, CH 02174990, correctly matched + normalised); G2 radar scores correctly at today's date.

**Honest gaps.**

- **Award table is empty — rate-limiting, not "no awards".** The first 365-day refresh 429'd on both sources
  (I'd just hammered FTS in the live smokes). The connector degraded correctly (2 source_errors, kept 0, no
  crash). Added 429-backoff to BOTH sources + inter-page pacing; a 4-year retry is running. Needs a clean run.
- **"Bids we lost" is not in public OCDS** — award notices name only the winner. That history lives in the
  app's internal Learn/outcome capture (Stage 6) + bid library, not the connector (user req 2026-07-12; deferred).
- The 3 new views are API + build verified only — **not yet clicked in a live browser.**

## 2026-07-12 (session 21) — F-series polish: search partition-error surfacing + F6 hide-closed default

**Context.** Resumed from session 20 (F1: PCS + Sell2Wales connectors, committed/pushed at `7c954e2`). User
asked "what's next?"; agreed to work through session 20's punch list — item 1 (surface partition errors),
then F6 (hide closed opps by default).

**Work done.**
- **Search partition-error surfacing** (`src/api.py` `/api/search`): a source run that returns
  `incomplete: true` (e.g. Sell2Wales's per-partition degrade) now surfaces `incomplete` + a
  `failed_partitions` count on that run's summary, with a server-side warning log. Raw `partition_errors`
  (upstream SQL/HTTP detail) are deliberately NOT passed to the client — matches the endpoint's existing
  generic-error policy. UI (`web/src/stages/SearchStage.jsx`): an amber "⚠ partial — N partition(s)
  unavailable upstream" note in the run-summary; new `.run-summary .warn` style (`web/src/styles.css`) using
  the existing `--warn` token.
- **F6 — Search default-hides closed opps unless in the pipeline** (`src/api.py`): new
  `_inflight_opportunity_ids()` helper (selected into Triage, has a qualification, or has a bid) mirrors the
  Triage pull-gate carve-out. `_query_opportunities` gained a `hide_closed` param (default `True` via
  `_list_params`) that drops `bid_status == "closed"` rows unless in-flight; an explicit `bid_status` filter
  always overrides. Applies to both `/api/opportunities` and `/api/export` (shared query). UI: a "Hide closed
  (unless in pipeline)" checkbox in the Filters panel, checked by default, disabled when Bid-status is
  explicitly set (with a tooltip explaining why); new `.filters .check-row` style.
- Two new test files: `tests/test_search_surfacing.py` (2 tests — incomplete flag/count surfaced, raw errors
  not leaked, healthy runs stay quiet) and `tests/test_search_hide_closed.py` (4 tests — default hides
  closed, in-flight closed stays visible, toggle-off shows all, explicit filter overrides), both exercising
  the real code paths (`TestClient` route / `api._query_opportunities` against a temp DB).

**Decisions.** None new — both items were already scoped in session 20's punch list and todo.md's F6 entry;
implemented as specified.

**Verification (honest).** `make check`: **80 backend tests** passed (74 baseline + 2 + 4 new), doc-state
consistency ok, Vite build clean (133.49 kB). Live-verified `hide_closed` against the real `bids.db` (24
opps, GET-only, no mutation): `hide_closed=false` → 24 (14 open/6 unknown/4 closed); default → 20 (4 closed
dropped, unknown kept); `bid_status=closed` explicit → 4 (override confirmed). Did not run a live search this
session, so partition-error surfacing was verified via the unit test's fake source, not a real Sell2Wales
call — reasonable given Sell2Wales's outage is already confirmed upstream, not connector-side.

**Open questions raised.** None new.

**Next.** User's call: commit this session's work, or continue the backlog (Sell2Wales bulk-download
fallback, F1 remainder — eTendersNI/G-Cloud — or G1–G3 GCA/frameworks intelligence).

## 2026-07-12 (session 20) — F1 more search sources: PCS + Sell2Wales; 4 new user reqs recorded

**Context.** Resumed from session 19 (C-series Compliance shipped, committed). User asked "what's next?",
then raised four requirement ideas to check/record (public framework-data APIs, hide-closed-by-default in
Search, a GCA agreements-to-pursue radar, an in-app how-to-supply reference) — all checked against the
codebase (none existed), recorded as scoped backlog items (F6, G1–G3), nothing built yet. User then asked to
work on **F1** (more search-source connectors).

**Work done.**
- Researched the UK devolved-nation procurement API landscape (Find a Tender/Contracts Finder OCDS award
  packages for G1; Public Contracts Scotland + Sell2Wales both on the Proactis/"klickstream" platform;
  eTendersNI on a different platform — Jaggaer).
- **Built `src/public_contracts_scotland.py`** (3rd search connector): month-granular OCDS paging,
  OJEU+sub-threshold notice-type split per stage, bespoke buyer/region/URL mapping (`ft.cpvs_in` reused
  verbatim for CPV extraction). Registered in `src/sources.py`. `tests/test_pcs.py` (6 tests, offline).
  **Live-verified**: a 45-day `--no-db` run returned real Scottish IT opportunities (ICT Managed Services,
  HR/Payroll, a decarbonisation framework, a DPS) with correct fields.
- **TLS finding + fix:** PCS's server omits its intermediate cert; no trust store (incl. certifi) can verify
  it. Rather than disable verification, **pinned the public Sectigo intermediate**
  (`src/certs/sectigo_dv_r36_intermediate.pem`, fetched from the leaf cert's AIA URL, valid to 2036 — not a
  secret) and kept full verification (`verify_mode=CERT_REQUIRED`). Proved: a default context rejects the
  connection, the pinned context accepts it.
- **Built `src/sell2wales.py`** (4th connector). Probing the documented query (incl. the exact params the
  user supplied mid-session: `dateFrom`, `noticeType`, `outputType`, `locale=2057/1106`) consistently returned
  **HTTP 500 "Error converting data type nvarchar to float"** — reproduced on every month/notice-type/output
  combination, including Sell2Wales's own documented 2019 example. Cross-tested PCS (same platform) to
  confirm it's Sell2Wales's bug, not ours. User supplied a resilient-ingestion design (partition by
  month×noticeType, bounded retry, structured error record, fall back to bulk download, don't silently drop
  the source) — implemented the connector-side portion: per-partition retry+backoff, a structured error
  record (`{source, partition, httpStatus, error, retryable, fallback}`), and graceful degradation (0 kept +
  recorded errors, never raises). Reuses PCS's shared helpers + the same pinned cert (same CA).
  `tests/test_sell2wales.py` (5 tests: mapping, poisoned-partition, healthy-ingest, partial-outage). **Live
  check against the real broken API**: 4 partition errors recorded, 0 kept, no crash — will resume ingesting
  automatically once Sell2Wales fixes their endpoint.
- `make check`: **74 backend tests** (63 + 6 PCS + 5 Sell2Wales) green, doc-consistency green, vite build
  clean. `bids.db` left untouched (24 opps, tracked baseline) — both connectors proved via `--no-db`.
- Docs updated: `CLAUDE.md`, `README.md` (connector list), `state.yaml`, `todo.md` (F-series expanded, new
  deferred items for the bulk-download fallback, FTS cross-publish recovery, and surfacing partition errors
  in the UI).

**Decisions.**
- First F1 deliverable is **Public Contracts Scotland + Sell2Wales together** (not just one source) since
  both came from the same platform-probing work.
- TLS: **pin the public intermediate cert, keep full verification** — rejected both "disable verification"
  and "fail until they fix it" as the default posture. User confirmed this recommendation explicitly.
- Sell2Wales: built as a **resilient per-partition adapter** rather than skipping it or hard-failing — the
  connector is correct and ready; only the upstream is broken.
- Did not build the bulk-download fallback this session — it's an aspx-postback form, not a clean GET, and
  is a materially bigger effort than the API-adapter work; scoped as a follow-on instead of rushed.

**Open questions raised.**
- Should `api.py`'s `/api/search` surface `partition_errors`/`incomplete` to the UI? Today Sell2Wales's
  degraded state is invisible to the user — the connector reports it, the API drops it.
- When (if) Sell2Wales's list API is fixed, worth a quick live re-check before assuming it's still down.
- G1–G3 and F6 (recorded this session, not built) — no decision yet on which to pick up next.

**Next.** User's choice: commit this session's work, surface `partition_errors` in the search UI (small),
chase the Sell2Wales bulk-download fallback (bigger), or start F6/G1–G3 instead.

## 2026-07-12 (session 19) — C-series "Compliance & Renewals" view shipped

**Context.** Opened on a terse status line ("still no rg in az") that I first mis-read as a task — the user
corrected sharply: it was a statement (no Resource Group in Azure), the question was "what's next?". Saved
that as a working-style memory. Chose **C-series** (highest founding-purpose payoff). While scoping, the user
**reframed C3**: the app should be the **system of record** for compliance assets (upload to a store, log
file locations, updatable, expiry extracted) — *not* a read of the bid library. Locked: **real file upload
now** (gitignored store + SharePoint seam later), **seed from the current library** on day one, **new
top-level view**.

**Work done (all verified before it was called done).**
- **`src/db.py`** — new `compliance_assets` table (+ `asset_uid` for cross-dialect id read-back) and CRUD
  helpers: `insert/get/list/update/delete_compliance_asset` + idempotent `seed_compliance_assets`
  (inserts only when the register is empty). Field allow-list guards against column smuggling.
- **`src/compliance_store.py`** (new) — the file-store seam, mirroring `library.py`'s provider pattern:
  `LocalFileStore` (gitignored `src/compliance_store/`) now, `SharePointStore` later behind the same
  interface (`COMPLIANCE_STORE` env). Stored paths are `uuid+ext`, never the client filename; every
  read/delete re-confines to the root → **path traversal blocked**. 25 MB cap + allowed-extension filter.
- **`src/compliance.py`** (new) — expiry derivation **live against today** (reuses `library.py` date maths,
  so Complete's ledger and this view agree), with a fallback that **mines a date from name/notes** when no
  `expiry_date` is set; board sort (expired→soonest→ok→undated); status summary; seed-from-library
  (evidence categories only, carries extracted expiry).
- **`src/api.py`** — full CRUD: `GET /api/compliance/board|reference`, `POST /assets` (multipart, optional
  file), `PUT /assets/{id}`, `DELETE /assets/{id}`, `GET /assets/{id}/file` (**attachment-only**, generic
  content-type so a stored HTML/SVG can't execute), `POST /import-from-library`. One-time startup seed in
  lifespan (no-op once populated / when library absent — never fakes). **CORS gained `DELETE`.** ISO-date
  and file-type/size validation → `422`/`413`.
- **Frontend** — new top-level **`ComplianceView.jsx`** (`#compliance` route via a generalised
  `routeFromHash`; a **"🛡 Compliance"** TopBar button open to all, not just Admin), `api.js` helpers
  (incl. a `sendForm` multipart helper + blob download), KPI banner (expired/expiring/no-date), an
  urgency-sorted register with per-row edit/delete/download, and an "Import from bid library" empty state.
  Small CSS block reusing the app's `.pd-facts`/`.ledger` idioms.
- **Deps/hygiene** — `python-multipart` added to `requirements.txt`; `src/compliance_store/` gitignored.

**Verification (honest, live).** `make check` green — **63 backend tests (+10 new: expiry derivation,
store round-trip + traversal, DB CRUD + idempotent seed) + doc-consistency + vite build clean**. Against the
real running server + `bids.db`: startup **seeded 19 assets from the real bid library, incl. the EXPIRED ISO
27001 (2025-10-31)** surfaced org-wide — the founding failure now visible in one place. Full cycle: upload a
cert with expiry only in the notes → **auto-mined to 2026-09-30 / expiring_soon**; attachment download (28
bytes, `Content-Disposition: attachment`); `PUT` expiry → recomputed; `.exe` upload and bad date → `422`;
delete → file removed + `404` after. `git check-ignore` confirms the store is **IGNORED** — no confidential
bytes tracked.

**Decisions.** (1) App-owned table + file-store seam over reading the library — the user's reframe; the
store mirrors `LocalMirror→GraphSharePoint` exactly. (2) Expiry status derived, never stored (facts decay).
(3) Writes open to any authenticated user (like bid saves), not Admin-only — flagged to revisit. (4) File
upload real; **file-content parsing (PDF/docx) deferred** — today expiry is mined from the text fields.

**Azure aside (source-of-truth fix).** Verified `az account list`: the **FWF Intern subscription is live**
(`0965…1ef1`), and the TalentGrow blueprint RGs exist. So `state.yaml`'s old
`azure_phase_d_hosting: needs_subscription` was stale → corrected to `iac_not_built` (the real gap is A1
Bicep, not access). Did **not** touch Azure — the user was explicit about not drifting there.

**Not committed.** All on disk (7 modified + 4 new). Left for the user to commit. UI is build- and
API-verified but **not clicked in a live browser** this session.

**Next.** Commit (user's call); then C4 frameworks / phase-2 file-content extraction, or R1 router split
(compliance is a clean first carve of the now-~1.9k-line api.py).

## 2026-07-12 (session 18) — Triage becomes an explicit "pull" gate

**Context.** User observed that the Triage board (Stage 2) showed *every* stored opportunity by default —
all 24, as "Untriaged" — and flagged it as unintended: only opps explicitly selected for triage should appear.
Investigation confirmed the board endpoint ran the *same unfiltered query as Search*, and there was no
"selected for triage" concept in the schema at all (state was computed from qualifications/bids; the only
opt-out was a reversible dismissal). User chose the **explicit-pull** model (over "keep funnel, hide
untriaged" or "keep as-is").

**Work done.**

- **`src/db.py`** — new `triage_selections` side-table (mirrors `triage_dismissals`, kept OUT of the
  `opportunities` table so Search stays untouched; auto-creates via startup `create_all(checkfirst=True)`),
  plus `selected_opportunity_ids()` / `set_triage_selected()` helpers.
- **`src/api.py`** — `triage_board` now skips any opp that isn't selected **and** isn't already worked
  (the OR-worked clause = `triaged or has_bid`, so existing Go/No-go decisions never vanish); new
  `PUT /api/opportunities/{id}/triage-select` + `TriageSelectUpdate` model.
- **`web/src/api.js`** — `setTriageSelected()`.
- **`web/src/stages/SearchStage.jsx`** — the "Triage this →" button now calls `setTriageSelected(id, true)`
  (the pull action) before the hash-navigation handoff; navigates even if the select call fails
  (board membership self-heals on load).
- **`web/src/stages/TriageStage.jsx`** — empty-state copy now points the user to Search's "Triage this →".
- **Verification (honest):** `make check` green — **53 backend tests + doc-consistency + vite build clean**.
  TestClient round-trip on a temp DB: board `0` before selection → select opp → board shows exactly that one
  as `untriaged` → deselect → `0`; missing opp → `404`; and a *worked-but-unselected* opp (qualification
  saved via `PUT …/qualification`) **still** appears (`no_go`) — backward-compat confirmed. **Live**
  `GET /api/triage/board` against the real `bids.db` now returns **0 items (was 24)**.

**Decisions.** (1) Side-table over a column on `opportunities` — matches the codebase's own dismissals
precedent and keeps the shared record shape / Search untouched. (2) Admit already-worked opps (qual or bid)
so the gate never hides an existing decision. (3) Left the board's ✕ as `dismiss` (reversible hide) rather
than merging it with de-select — non-breaking, and only the pull gate was asked for.

**Open questions raised.** Should the board ✕ de-select (remove from Triage) instead of / in addition to
dismiss? They overlap in a pull model. Deferred — flagged in handover.

**Gotcha.** The first attempt *looked* like it hadn't worked: the user's browser still showed 24. Root cause
was a stale server — the running `uvicorn` had been started **without `--reload`**, so it served pre-change
code. Restarted with `--reload`; the live endpoint then returned 0. (The code was correct all along.)

**Next.** No task in flight. Deferred queue unchanged (S5 key rotation = user action; R1/R3/C3 refactors;
Azure A1–A9; C-series compliance view — scope with user).

## 2026-07-11 (session 17) — Local/Azure hybrid review: security gate + tests + hygiene cleared

**Context.** A new merged code review landed (`docs/code_reviews/2026-07-11-local-azure-hybrid-review-
merged.md`, 58 findings from a GPT-5 + Opus 4.8 pass). Verified against HEAD that all spot-checked findings
were still live. User chose scope: **security gate + tests + hygiene**; defer the structural refactors
(R1/R3/C3) and the Azure-readiness block (A1–A9). Net **−461 lines** across 32 files, 4 commits on `main`.

**Work done (all verified before commit).**
- **Security gate (S1–S10, minus S5).** S1 `_csv_safe()` neutralises `= + - @ \t \r` export cells;
  S2 `SearchRequest` validators bound `days`/cpv-list/stage/ISO-dates → 422; S3 connector failures log
  server-side + return generic `"source fetch failed"`; S4 raw MSAL errors gated behind `import.meta.env.DEV`;
  S6 connectors validate `stage` + `urllib.parse.urlencode` the query; S7 untrusted notice/question text fenced
  in `<<<NOTICE_DATA>>>` markers + system-prompt data-boundary note (triage + complete); S8 AI-read dates →
  `meta.provisional_dates`, surfaced in Triage UI; S9 `evidence_used` ∩ `matches_offered`, unsupported split
  out + shown in Complete UI; S10 non-JSON 200 body → clean source-scoped error.
- **Tests (T1, T2).** `tests/test_outcome.py` (win-rate denominators, rounding, CL3 unknown-result guard) +
  `tests/test_response.py` (word-count/over-limit boundaries). Suite **29 → 53**.
- **Hygiene (~35 findings).** Backend: U1/U4 dead code, N1 removed commented AzureOpenAIProvider (+ fixed two
  stale doc pointers), N2/N3 orphaned alias/function, CL3 guard, CL4 redundant SELECT, C4 `_row_dict`, C5
  keyword `HTTPException` (18 sites), **C6 `_require_bid`/`_require_opp` helpers** (replaced ~10 duplicated 404
  guards; 404 paths re-verified), C7 end-date normalisation, C8 shared `IMMINENT_DAYS`, R4 `dict(row)`, CL2
  connector logger, N4/N5/N7 documented invariants. Frontend: C10 `fmtDate`→`format.js`, N6 dead journey
  states, O3 dead CSS. Skills: CL1 atomic writes, C1/U3 build_matrix, **U2 preflight `--stage` now genuinely
  differs** (readiness advisory / final blocking — was a no-op), O1 documented standalone vocabulary, R2
  whole-word stale matching. Config: O2 Azurite behind opt-in `storage` profile, O4 `make seed-demo`.
- **Honesty note.** U1's dead `datetime` import was removed, but `datetime` is now legitimately used by the
  S2 date validator, so the import stays — used, not dead.

**Verified.** `make check` green (53 tests + doc-consistency + vite build); a `TestClient` security smoke
confirmed S1 neutralise, S2 → 422, S3 generic, S6 urlencode, S10 clean decode, and the `_require_*` 404 paths;
preflight `--stage readiness` vs `final` exit 0/1 confirmed; check_answer whole-word (no false hit on
"success/access", real "CCS" still flagged); `make seed-demo` runs in dependency order. Ruff on touched files:
remaining warnings are pre-existing (intentional post-`_load_dotenv` E402 in api.py; skills-script lint I
didn't author).

**Deferred (with the user's agreement).** S5 (rotate the real Anthropic key in `src/.env` — **user action**);
R1 (split `api.py` routers); R3 (dedupe connector `to_record`/`run`); C3 (shared fetch/backoff); A1–A9 Azure
readiness. R5/R6 are "no action" by design. The review file carries a remediation-status header and stays
active (not archived) until the deferred items are addressed.

## 2026-07-11 (session 16) — Cleared Wave 5 (right-sizing refactors) + Wave 6 (auth hardening) — queue empty

**Context.** Resumed with no task in flight; user chose to "finish the low hanging fruit before we make more
debt" — i.e. the remaining code-review remediation (Waves 5 + 6) before scoping the C-series feature. Reality-
checked every todo item against the actual code first; four turned out to be false records (already done). Net
**−163 code lines** + new `web/src/format.js`. Committed + pushed on `main`.

**Work done (all verified before commit).**
- **db.py — 5 upserts → one `_upsert_one`.** `upsert_qualification`/`_bid_plan`/`_bid_manage`/`_bid_responses`/
  `_bid_outcome` were structurally identical (differing only in table, key column, field allow-lists) → now
  2-line wrappers over a shared `_upsert_one(conn, table, key_col, key_val, fields, allowed, json_fields)`.
  Table/key-col are internal constants (safe to interpolate). Roundtrip-verified on a temp DB: insert; update
  (id stable, `created_at` preserved, `updated_at` bumped); blank-update (bumps timestamp, no field smuggle);
  JSON encode/decode. This is the single home for a unique-violation retry if ever needed.
- **web/src/format.js (new) — shared formatters.** `fmtMoney` (was ×3, slightly drifted), `deadlineBadge`
  (×3), `daysUntil` (×2) de-duped out of Plan/Manage/Complete/Triage/Search. **Fixed a real latent bug:**
  Complete hard-coded 7/14-day urgency thresholds while Plan/Manage read `imminent_days` from the server —
  a silent disagreement on "urgent". Complete now reads `imminent_days` too; added it to
  `/api/complete/reference` (from `P.IMMINENT_DAYS`) so all stages share one source.
- **db.derive_lifecycle — backend twin dedup.** `api._derive_open` and `refresh_clean._open_closed` (open/
  closed/unknown from a deadline) were near-verbatim → both now thin aliases over `db.derive_lifecycle(deadline,
  now=None)`, so the live API and the persisted lifecycle flag can't drift.
- **Wave 6 hardening.** `authConfig.js` MSAL cache → `sessionStorage` (tab-scoped, cleared on close);
  `web/.gitignore` now ignores `.env`/`.env.*` (keeps `.env.example`).

**False records found (already implemented — cleared from todo, not re-done).**
- api.js error-handling consolidation — every helper already routes through `getJSON`/`sendJSON` → `errorFrom`,
  which already surfaces server `detail`. The todo's line refs didn't exist in the file.
- `LocalMirror.items()` caching — already memoized per-instance; `get_provider()` returns one instance per
  request, so status()+items() parse the workbook once (docstring already said so).
- auth.py 401 hardening — already logs the real reason server-side, already catches `jwt.PyJWTError` (not bare
  `Exception`), already maps a JWKS outage to 503 (`auth.py:267-278`).

**Verification.** `make check` green — 29 backend tests, doc-state consistency, vite build clean (131.12 kB,
unchanged). `db`/`api`/`refresh_clean` import clean. `_upsert_one` roundtrip test (above) passed. The formatter
refactor was not re-driven in a live browser (vite build is the guard); last live-browser confirm remains
2026-07-10.

**Decisions.** Kept the connector `to_record`/`run`/`main` dedup deferred — the todo's own guidance is to
extract when a 3rd source lands; doing it against 2 sources would be speculative abstraction.

**Open questions raised.** None new.

**Next.** Scope the **C-series "Compliance & Renewals" view** with the user (highest founding-purpose payoff),
or pick up **Azure Phase D** (hosting scaffold; needs a subscription).

## 2026-07-11 (session 15) — Cleared Wave 3 (doc/comment truth sweep) + Wave 4 (dead code)

**Context.** Resumed with no task in flight; handover named the code-review remediation queue as the natural
continuation. Picked the cheap, no-scoping-needed waves (3 + 4) plus the Wave 6 `library.py` win. Net **−369
lines**. `make check` green (29 backend tests + doc-consistency + vite build 131 kB). Committed + pushed.

**Work done (all verified before commit).**
- **Wave 4 — dead code.** Deleted `MockStage.jsx`, `ScopeCard.jsx`, `StagePlaceholder.jsx` (preview-era
  orphans). `StagePlaceholder` was still imported in `App.jsx` as a fallback but never rendered (all 6 stages
  resolve to live views) → replaced with a minimal inline guard against a mistyped `component` slug. Stripped
  the orphaned `scope`/`asset` data from all 6 stages in `journey.js`, simplified `STATE_MAP` to just the pill
  class (its 2nd element only fed the deleted dot renderer) + updated the one `App.jsx` consumer. Removed the
  matching dead CSS (`.split`, placeholder, scope-card, mock-screen, `.asset`, `.dot-*`). Unused imports:
  `datetime` (`clarification.py`), `useMemo` (`PlanStage.jsx`); renamed a local `bids` shadowing the module
  Table (`db.py:1024`); collapsed a no-op spread (`SearchStage.jsx`).
- **Wave 3 — doc/comment truth sweep.** Fixed "only Search is live" comments (App.jsx, journey.js header,
  SearchStage.jsx); corrected `llm.py` docstring (default is `claude-haiku-4-5`, not opus), db.py "12-field
  sketch"/`sqlite3.Row` staleness, api.py SQLite-only/3-endpoint docstring (now dual-mode + noted
  representative); `discovery/.env` → `src/.env` (.env.example, api.py). Hoisted `import response as R` to
  module top in `complete_ai.py` — **verified empirically there is no import cycle** (response imports only
  `re`; both import orders work), so the "local import avoids a cycle" comment was wrong.

**Two todo claims that were false records (verified, left alone).**
- **Wave 6 `library.py` "raise on unknown provider"** is **already implemented** (`library.py:422-438` already
  fails loudly) — nothing to do; corrected the todo.
- **SearchStage:268 eslint-disable** is *not* inert (deliberately suppresses a `seeded`-dep warning), and the
  claimed **TriageStage "dead branch"** couldn't be located with confidence — left both rather than risk live
  code.

**Next.** Wave 5 (right-sizing refactors — api.js error handling, db.py upsert consolidation, shared web
formatters) or the user-scoped C-series "Compliance & Renewals" view. Wave 6 auth hardening also open.

## 2026-07-11 (session 14) — Cleared Wave 2 correctness bugs (deadline compare, 3.12 f-string, seeder portability)

**Context.** Resumed from session 13 (Active task = scope C-series, with Wave 2 bugs as a listed
alternative). User chose the **Wave 2 correctness bugs** — real defects, well-specified, no scoping needed.
Worked all four items in one pass; committed + pushed at `33980dd`.

**Work done (all verified; committed + pushed at session end).**
- **FTS lexicographic deadline compare** (`find_tender_filter.py:155`). Moved the offset-aware `is_open`
  (parses the ISO string via `datetime.fromisoformat`, string-compare fallback) out of
  `contracts_finder_filter.py` into `find_tender_filter.py` as the shared home; CF re-exports it
  (`is_open = ft.is_open`); FTS's `run()` now calls it instead of `end >= now.isoformat()`. Removes the
  CF/FTS duplication (Wave 5 `↳`) at the same time. Updated `tests/test_deadline.py` docstring to the new
  home. Verified: the `13:00+05:00` (= 08:00 UTC, past noon UTC) case the old string compare called "open"
  (`True`) now correctly reads closed (`False`).
- **`seed_learn_demo.py` 3.12-only f-string.** Extracted the `score`/`winner` conditional fragments to
  `score_part`/`winner_part` locals so no f-string nests same-type quotes (PEP 701 is 3.12-only). `ast.parse`
  clean → importable on ≤3.11.
- **Seeder `LIMIT 1`** (all four `seed_*_demo.py` `_find` helpers). Dropped `LIMIT 1`; `ORDER BY` +
  `.fetchone()` already returns the first row, so the query is identical on sqlite and SQL Server. (The
  todo's suggested `FETCH NEXT` would have broken sqlite — this is a dual-mode DB, so removal is the
  portable fix.)
- **Seeder hard-coded ~July-2026 dates.** Added a `_day(offset)` helper (`date.today()` + `timedelta`) to
  the plan/manage/learn seeders; every literal converted to an offset preserving intent
  (passed/imminent/expired/in-date) and per-record chronological order.

**Verification.** `make check-fast` green (29 backend tests + doc-consistency; web build skipped). Ran all
four seeders against `bids.db` end-to-end (every `_find_bid` matched, dates inserted with the right spread,
the fixed learn f-string rendered "lost to Incumbent Digital Ltd" at runtime), then `--clear`'d all four →
empty pipeline restored (24 opps, 0 bids/plans/quals). `git push` → `51e3315..33980dd main`.

**Decisions.** Fixed the `LIMIT 1` item by *removing* `LIMIT` rather than the todo's suggested
`OFFSET…FETCH NEXT` — the latter is not valid sqlite, and this DB is dual-mode. Left the pre-existing
untracked `docs/harness_design/` out of the commit (not this session's work).

**Open questions raised.** None new.

**Next.** No task in flight — pick the next code-review remediation wave (Wave 3 doc sweep or Wave 4
dead-code, both cheap/batchable), or scope the C-series compliance view with the user. See handover.

## 2026-07-10 (session 13) — Cleared the walkthrough quick-wins queue + a user-requested Triage "dismiss" & demo cleanse

**Context.** Resumed from session 12's handover (Active task = quick-wins-first). Worked the Session-12
walkthrough queue in priority order, then the user asked for a way to remove items from Triage, which
surfaced that the 24 opportunities are all real (genuine FTS/CF OCIDs) — only 4 had seeded demo bids.

**Work done (all live-verified; committed at session end).**
- **S5 — team roster.** `team_roster` in `app_settings`; `_team_roster` resolver (trim/case-insensitive
  dedupe/cap 100×80) + `GET`/`PUT /api/settings/team-roster` (Admin PUT); roster injected into the Plan +
  Manage reference payloads; Settings "Team roster" card; owner `<datalist>`s on Plan (people + FOR002
  roles) and Manage (Owner/Backup). Verified: clean/dedupe, 400 on over-long, roster in both refs.
- **S3 — search defaults.** `search_defaults` in `app_settings`; read-time `_search_defaults` resolver
  re-validates every field vs the live source/stage registry (silent fallback), `_search_defaults_code`
  baseline; `GET`/`PUT /api/settings/search-defaults` (Admin PUT, strict 400s); folded into `/api/meta`
  `search_options.defaults`; Settings "Search defaults" card (source toggles, CPV chip editor, stage,
  window, open-only, reset-to-built-in); the "Run a live search" panel seeds its whole form from it.
  Verified: partial PUT persists + surfaces in meta; all 6 bad-input cases → 400.
- **U1 — Triage card board.** `db.list_triage_states` + `GET /api/triage/board` (funnel summary,
  mutually-exclusive states with bid-live precedence); TriageStage dropdown → filtered card board (chips +
  counts + keyword); card → form with a "← Board" back header + selected-opp title; board refreshes after
  a save. The Search→Triage "Triage this" handoff already existed. User confirmed S5/S3/U1 in the browser.
- **U2 — dismiss from Triage (reversible) + demo cleanse.** New `triage_dismissals` side table (kept OUT
  of `opportunities` so Search + the record shape are unchanged) + `db.dismissed_opportunity_ids` /
  `set_triage_dismissed`; `PUT /api/opportunities/{id}/triage-dismiss`; board flags `dismissed` + a
  "Dismissed (n)" chip; card ✕ Dismiss / ↩ Restore (stopPropagation so it doesn't open the form).
  **Dismissal hides from Triage only — the opp stays in Search** (user's explicit choice via
  AskUserQuestion). Also **cleansed the 4 seeded demo bids** (wiped qualifications/bids/bid_plans/
  bid_manage/bid_responses/bid_outcomes) → **24 real opps, empty pipeline**; `bids.db` backup left in the
  session scratchpad. Verified end-to-end: dismiss 2 → active 24→22 + dismissed 2 (sum 24); restore →
  24/0; 404 on missing opp; `create_all(checkfirst=True)` auto-creates the new table.

**Verification.** `python3 -c import api` clean after every backend change; each feature exercised live over
HTTP against the bypass API on :8000; `npm run build` clean at each step (final 486.8 kB / 134.3 kB gz);
Vite HMR compiled cleanly. DB left at 24 opps / empty pipeline / 0 dismissals for the user to test.

**Decisions.** (1) "Remove from Triage" = **reversible dismiss**, not delete; **stays in Search** (user).
(2) Cleanse the seeded demo bids now so the user tests a real bid on a clean pipeline (user). (3) Dismissal
lives in a **side table**, not an `opportunities` column, to leave Search and the shared record shape
untouched — mirrors how per-stage state hangs off separate tables.

**Open questions raised.** If the user later wants a dismissed opp to vanish from Search too, it's a
one-line filter add on the Search query (parked). The C-series still needs a scoping conversation before build.

**Next.** Scope the **C-series "Compliance & Renewals" view** *with the user* (don't start cold), then build.
See the handover Active task.

## 2026-07-10 (session 12) — UI walkthrough with the user: quick-win fixes + a findings punch-list

**Context.** New workstream, separate from the Azure migration. The user did a live click-through of the
running app to note changes/fixes, then had me ship the quick wins as we went. Preference stated:
**quick wins first.** All work committed as we went (7 commits).

**Work done (all committed, live-verified).**
- **B1 + B2** (`2bfd948`) — Fixed two Triage→Plan walkthrough gaps. **B1:** a bid promoted from Triage
  *looked* missing on the Plan board because the card rendered only the opportunity title, not the buyer;
  the bid was always there (verified: bid 12/opp 15 in the "Qualifying" column). Fix = show buyer as a
  sub-line (`PlanStage.jsx`). Ruled out a stale-board bug (stages remount → board refetches). **B2:** the
  Triage AI draft never populated Response Dates — the schema had **no** date fields; dates come from the
  notice. Added `response_open_date`/`clarification_deadline`/`submission_deadline` to the schema+prompt so
  AI extracts them from the notice **text** when the structured record is blank; authoritative dates win.
  Live-verified: extracted 10 Jul/24 Jul/7 Aug from a dateless record; structured dates override.
- **F4** (`2b16cc3`) — Editable **bid day rates** in Settings. Was a flat £500/day for all 5 FOR001 roles.
  New `app_settings` key→JSON table in `bids.db` (travels with data, editable on Azure — unlike the .env
  LLM config); `compute_bid_economics(complexity, rates)` reads per-role rates; GET/PUT
  `/api/settings/day-rates` (Admin, positive-only). Snapshot semantics kept. Verified: default Medium =
  £8,250/16.5d (matches FOR001); raising a role re-snapshots on save and the Plan board reflected it.
- **S1** (`bd09e3b`) — Editable **AI prompts** in Settings + **two-column Settings redesign**. The FWF
  **profile** (shared by Triage+Complete) and optional per-stage **guidance** are editable, persisted in
  `app_settings`; `triage_ai.resolve_profile` (blank→default) + `_guidance_block` (appended, no data-injection
  change); mirrored into `complete_ai`. GET/PUT `/api/settings/ai-prompts` (Admin, length-capped). Verified:
  a stored guidance marker appeared verbatim in a live draft.
- **S1+** (`aac5ff4`) — Made the **Triage extraction prompt itself editable** (user asked specifically).
  Base instructions → an editable template with named tokens the app fills: `{opportunity}` (required, the
  notice data), `{rag_criteria}`, `{complexity_levels}`. Guarded: `{opportunity}` validated on save
  client-side (Save disabled + warning) **and** server-side (400); literal token replace so stray braces
  survive. Renders **byte-identical** to the old hardcoded prompt on default. Verified: custom template's
  marker in a live draft; `{opportunity}`-less template → 400.
- **F3** (`4326fd4`) — Native **date-pickers** for the Plan start/complete fields (main + per phase). `dateOnly()`
  coerces ISO→date and rejects non-ISO so the picker never jams; widened phase-timeline date columns.
  Verified via API round-trip; **user confirmed live in the UI.**
- **S4** (`d74b7a6`) — **Team capacity** is now a persisted Setting (`app_settings`), replacing the
  hardcoded `DEFAULT_TEAM_CAPACITY_DAYS`. `/api/plan/reference` returns it so the board seeds from it;
  `/api/plan/board` uses it when no query param (explicit param still = ad-hoc what-if). Verified: 40
  propagates to board+reference; `?capacity_days=10` still overrides; 0 rejected.
- **Layout** (`8535877`) — Rebalanced the Settings two-column grid (moved Team capacity under AI prompts on
  the right). **Screenshot-verified** via Playwright (chromium installed by the user); user confirmed pass.

**New infra this session.** `app_settings` (key→JSON) table + `db.get_setting`/`set_setting` — the home for
tunable business settings that must travel with the data and stay editable on Azure (day rates, AI prompts,
team capacity all use it). Distinct from `src/.env`/`config.py` (LLM secrets, read-only on Azure).

**Round-2 findings (captured, NOT yet built) — logged in todo.md "Session 12 walkthrough queue".** Checked
against the code first; the honest split matters:
- **C1 clarifications** — the FOR003 register already exists on Manage (Stage 5): click a bid → question/
  channel/deadline/response/status. The user couldn't find it → **discoverability** fix (board shows only a
  count). NEW: AI ingest/dedupe of incoming CQs + "already answered?" check.
- **C2** — per-bid workspace + slim per-bid KB (net-new; aligns with the `skills/` 3-library design).
- **C3 compliance docs — MOSTLY ALREADY EXISTS.** The user's whole list (ISO, Insurance, Cyber Essentials,
  H&S, GDPR, EDI, Environmental, **and Modern Slavery** via "Anti-Bribery & Modern Slavery Policies") is
  already tracked in the real library (`library.py`, *Company Credentials*) + surfaced in Complete's evidence
  ledger + Manage pre-flight. **Real gaps:** (1) renewal dates — only **ISO** has an extracted expiry and it
  reads **2025-10-31 = EXPIRED in the live data** (the exact founding failure); the rest carry no extractable
  date. (2) surfacing — the ledger is buried per-bid, not an org-level view.
- **C4** — framework/contract membership-period tracker (net-new; org-level twin of C3; RM6263-expired
  precedent). **Synthesis:** C3+C4 → a cross-cutting **"Compliance & Renewals" view**; expiry plumbing
  already in `library.py`, missing = structured dates + frameworks + a screen. Highest founding-purpose payoff.

**Decisions.** Quick-wins-first, ship-as-we-go. Business settings live in a new `app_settings` DB table, not
`.env`. AI prompt editing kept safe by templating (data injection stays in code; required-token guard).

**Open questions raised.** Does the compliance-view idea (C3+C4) jump the quick-wins queue? (User leaning
wrap-up + fresh session.) How to source real renewal dates for the credential register.

**Next.** New session, quick wins first. Candidates in priority order: **S5** (team roster → owner dropdown),
**S3** (search defaults), then the **C-series compliance-view** (scope before building). Punch-list detail in
todo.md "Session 12 walkthrough queue".

## 2026-07-10 (session 11) — Commit Phase C; confirm + verify Wave 0/1 remediation already shipped

**Context.** User asked for three things: commit the Phase C milestone, do the code-review Wave 0 (security)
blockers, and do the Wave 1 (Azure-promotion) blockers. Session 10 left everything uncommitted.

**Work done.**
- **Committed Phase C** as `0f35c70` ("Azure Phase C: Entra ID auth (API guard + SPA MSAL sign-in)") —
  the auth backend (`src/auth.py`), SPA MSAL gate, env templates, `docs/design/entra-app-registration.md`
  (new admin hand-off doc, written this session), and the two `docs/code_reviews/` reports. Deliberately
  **excluded `_session/`** from that commit so the "Nothing committed yet" handover line wasn't baked in as
  a false record.
- **Verified Wave 0 + Wave 1 against the actual code, not the plan.** Finding: **all 12 items were already
  implemented in the Phase C working tree** — the todo.md checklist was written as a plan and never
  reconciled after the fixes landed. So they shipped inside `0f35c70`, not as separate commits. Item-by-item
  confirmation (with file:line) is now recorded in `_session/todo.md` Waves 0–1.
- **Honest verification (real green, quoted):** backend `import auth, config, db, library, api` clean +
  FastAPI app constructs; `config.upsert_env({'ANTHROPIC_MODEL': '…\nLOCAL_AUTH_BYPASS=1'})` **raised
  `ValueError`** and wrote nothing (newline-injection blocker proven functionally, not just by inspection);
  `npm --prefix web run build` clean (472 kB / 130 kB gz); `python3 src/db.py` → 21 opps / 3 bids intact.
- **Corrected the stale records:** flipped the Wave 0/1 checkboxes to `[x]` with evidence; updated
  handover Status + Active task; this entry.

**Why one commit, not three.** The Wave 0/1 fixes were interleaved with the auth work in a single authored
tree, so they couldn't be cleanly split into separate commits after the fact without hunk surgery of little
value. The code is correct, committed, and verified; the debt that remains (Waves 2–6) is non-blocking.

**Next.** Unchanged from Phase C: pick the next Azure step (Phase C tail live sign-in needs a dev-tenant
app reg — see `docs/design/entra-app-registration.md`; or Phase D hosting scaffold, needs Azure). Remaining
code-review debt starts at Wave 2 (correctness bugs) — none are Azure-promotion blockers.

## 2026-07-09 (session 10) — Azure Phase C: Entra ID auth (backend guard + SPA MSAL), verified locally

**Context.** Session 9 finished Phase B (DB dual-mode). Handover's #1 next step was Phase C — close the
"no auth anywhere" gap. Chosen by the user. Plan of record: `docs/design/azure-target.md`. Built +
verified entirely locally, no Azure spend (per the design's "Phases B/C are independent of Azure being
provisioned").

**Work done.**
- **`src/auth.py`** (new) — clones TalentGrow's `aadAuth.ts` + `devAuth.ts` + `groupRoleMap.ts` in
  Python. `require_auth` FastAPI dependency validates a real Entra **v2 access token** via PyJWT +
  `PyJWKClient` (signature against the tenant JWKS, issuer, audience, expiry), resolves a role from the
  `groups` claim, returns an `Identity`. `require_roles("Admin")` factory for role-gated routes.
  `LOCAL_AUTH_BYPASS=1` → synthetic **Admin** identity, no token (offline/PoC dev, keeps Settings usable).
  `auth_status()` non-secret posture surfaced in `/api/meta`.
- **Wired app-wide** in `src/api.py`: `FastAPI(dependencies=[Depends(require_auth)])` guards **every**
  `/api/*` route (can't forget one); the two config-write endpoints add `Depends(require_roles("Admin"))`.
  CORS made env-driven (`CORS_ALLOWED_ORIGINS`, localhost fallback).
- **SPA** — `web/src/authConfig.js` (MSAL config, null when unconfigured); `main.jsx` wraps in
  `MsalProvider` + drains the redirect promise; `App.jsx` sign-in gate + `UserChip`/sign-out; **all 10
  fetch calls routed through one new `apiFetch`** in `web/src/api.js` that attaches the Bearer token
  (`acquireTokenSilent`, redirect fallback) + `VITE_API_BASE_URL`. `@azure/msal-browser`+`msal-react`
  added. When `VITE_AAD_*` are absent (local dev) it's a plain unauthenticated same-origin fetch — no
  behaviour change.
- **Two deliberate divergences from TalentGrow** (FWF bidding-tool Entra groups don't exist yet, so no
  invented IDs committed): `AAD_GROUP_ROLE_MAP` is env-driven JSON (empty default), and an authenticated
  caller with no mapped group gets a configurable `AAD_DEFAULT_ROLE` ("User"; set "" for strict).
  Roles kept small: Admin > User.

**Verified (all live, honest).**
- **Backend unit rig** (`scratchpad/verify_auth.py`, not committed) — self-minted RSA tokens against a
  local JWKS injected into `auth._jwks_clients`: **12/12 PASS** — bypass→Admin; no-token→401; valid→default
  User; mapped groups→most-privileged Admin; strict+unmapped→403; expired/wrong-aud/wrong-iss/tampered
  →401; unconfigured→500 fail-closed; `require_roles` blocks User / allows Admin.
- **HTTP** — bypass ON: `/api/meta` (21 opps, `auth.bypass:true`), `/api/plan/board`, `PUT /api/config`
  all 200. Bypass OFF + Entra configured + no token → **401 on every route**; garbage token → 401.
- **Frontend** — `npm run build` clean (MSAL bundled, 473 kB); full local stack (bypass API + Vite) serves
  the SPA and proxies `/api/meta` → 21 opps. Unauthenticated local path unchanged.

**One real fix mid-build:** the bypass shim initially inherited `AAD_DEFAULT_ROLE` (User), which would
403 the now-Admin-gated Settings endpoints locally. Changed bypass to always grant Admin (TalentGrow's
full-access local posture).

**Not done / needs the user (Tier-2, no emulator):** the actual MSAL **browser sign-in** flow can only be
click-tested against a real **dev-tenant app registration** — supply `VITE_AAD_CLIENT_ID/TENANT_ID/API_SCOPE`
(SPA) + `AAD_TENANT_ID`/`AAD_API_CLIENT_ID` (API), set `LOCAL_AUTH_BYPASS=0`, then sign in. The code path is
built and unit-proven; only the live redirect round-trip is unverified. Nothing committed yet.

**Follow-ups same session (user-directed).**
- **Renamed the non-admin role `Bidder` → `User`** to match the two real Entra security groups the user
  confirmed: **Admin** (god rights within the app) and **User** (employee working a bid through the
  stages). Swept code, `.env.example`, docs, session files, verify rig.
- **Auth model decided = shared team workspace** (user): every authenticated User works every bid; no
  per-user ownership → **no IDOR/row-scoping work** (the TalentGrow `dc469cd` hardening doesn't apply).
  **Admin-only powers = the Settings/LLM-config writes** only; the whole six-stage journey stays open to
  Users.
- **Added `LOCAL_AUTH_ROLE`** to the bypass shim (default Admin) so the running local app can be driven as
  a User to watch role-gating live — our stand-in for TalentGrow's SWA-CLI mock-auth role switch. Verified:
  rig now **15/15**; live HTTP `LOCAL_AUTH_ROLE=User` → journey routes 200, `PUT /api/config` → **403**.
- **Role-aware SPA (hide the Admin gear)** — new `GET /api/auth/me` (`{role, display_name, email, via}`);
  `App.jsx` fetches it, hides the ⚙ Settings gear for non-Admins and bounces a non-Admin off `#settings`.
  Backend gate still enforces (presentation only). Verified per-role over HTTP; `npm run build` clean.
- **Mined TalentGrow's real git history locally** — no repo exposure needed. The user's other-account clone
  (`/Users/…/talent_grow`) had a squashed 4-commit `main`, but the **full 47-commit history is intact in
  the `eek2020-old/main` remote-tracking ref** (`github.com/eek2020/talent_grow`), already fetched. Read the
  auth evolution offline: local-auth spike via **SWA-CLI mock** (`58e98de`) → real Entra env-gated to
  deploy-only (`737fd58`) → `VITE_AAD_*`-in-workflow gotcha (`ca2924e`) → real-auth 401 debugging only after
  deploy (`3fbddee`) → **retired local auth, went Azure-only** via `az login` (`d603028`) → security-review
  hardening for user-owned data (`dc469cd`). **Confirms real MSAL login was never localhost-tested there** —
  so ours verifies at deploy (Phase D/F), and `LOCAL_AUTH_BYPASS` is the honest local equivalent.

## 2026-07-09 (session 9) — Azure Phase B: db.py dual-mode port, verified on real SQL Server

**Context.** Session 8 designed the Azure migration; the handover's next action was Phase B — port
`src/db.py` off raw `sqlite3` to a SQLAlchemy Core dual-mode shim, verifiable locally against a SQL
Server container with no Azure spend. The user opened by asking whether this is better emulated in
Azurite. Answer (and a correction worth keeping): **Azurite is a Blob/Queue/Table emulator, not a SQL
emulator** — it cannot stand in for Azure SQL. The right local target is a SQL Server container. User
also flagged an existing SQL Server image in Docker to repurpose.

**Work done.**
- **Reused the existing local image.** `docker images` showed `mcr.microsoft.com/mssql/server:2022-latest`
  already pulled (no running container/volume). Used it as-is: 2022 speaks the identical `mssql` dialect
  to Azure SQL, so it verifies the whole port; 2025's only extra is the `VECTOR` type (retrieval Option B,
  deferred). Zero download.
- **`docker-compose.yml`** (repo root, new) — `db` (SQL Server) + `azurite` scaffold. Hit a real OOM: the
  container `Exited (137)` (SIGKILL) under Rosetta x64 emulation. Fixed with `MSSQL_MEMORY_LIMIT_MB=2048`
  + `mem_limit: 3g` (Docker VM = 7.8 GB). Then boots healthy, `1433` published, SA password from gitignored
  root `.env`.
- **Driver stack.** `pip install pyodbc` (5.3.0) + Homebrew `unixodbc` + `msodbcsql18`. First attempt
  failed (masked by `| tail`): Homebrew's untrusted-tap gate refused msodbcsql18. Fix: `brew trust
  microsoft/mssql-release` then install. Registered "ODBC Driver 18 for SQL Server".
- **Ported `src/db.py`** — the surgical part: only db.py changed, none of the 8 caller files. `connect()`
  returns a `_Conn` adapter over a SQLAlchemy Core connection; `exec_driver_sql` passes the existing `?`
  SQL straight to whichever driver (both qmark); a `_Row`/`_Result` pair mirrors `sqlite3.Row`/cursor so
  every call site is untouched. Schema declared once as SQLAlchemy metadata (`opportunities` + 7 tables,
  built DRY from the existing field-list constants) → `create_all()` emits per-dialect DDL, replacing the
  old `executescript`. Backend chosen by `DB_URL` env (unset = local sqlite, exact prior behaviour).
- **Fixed two real dialect bugs the live engine surfaced** — `ORDER BY (deadline_date IS NULL)` (T-SQL
  syntax error) → portable `CASE WHEN … THEN 1 ELSE 0 END` in all 4 list queries; `NVARCHAR(MAX)` can't be
  a unique-key column → `source`/`ocid` bounded to `Unicode(400)`.
- **`requirements.txt`** — added `SQLAlchemy` (always) + `pyodbc` (SQL Server/Azure only); fixed the stale
  "stdlib covers db.py" comment.

**Verification (all live, quoted).** `scratchpad/verify_dualmode.py` ran the SAME db.py functions against
a throwaway SQLite file and the live SQL Server container: **`IDENTICAL BEHAVIOUR: True`**, 4/4 PASS
(insert/update = `('inserted','updated')` on both; `Café … £120k … ✓` round-trips through NVARCHAR; JSON
`delivery_team`/`phases` decode to lists; `list_bids_for_board` JOIN + rewritten ORDER BY runs).
`python3 src/db.py` on the default path shows the real `opportunities: 21` etc. (cleaned the VerifyTest
rows the test leaked — was opp id 22). Over HTTP through the adapter: `/api/plan/board` → `count:3` with
real bids; `/api/opportunities` → `{count, results}` 21 rows. Audit: api.py runtime SQL is portable; only
the 4 `seed_*_demo.py` still use sqlite-only `LIMIT 1` (dev-local, deferred).

**Decisions.** Repurpose the existing **2022** image (not pull 2025) until `VECTOR` is needed. Keep the
port surgical via the qmark-compatible adapter rather than rewriting every call site to SQLAlchemy
`text()`/named params. Azurite scaffolded in compose but **not** used by Phase B (it's not a SQL emulator).

**Open questions raised.** Connection lifecycle under real multi-user cloud (api.py doesn't close per-request
connections — fine for local PoC, revisit pooling later). Whether to finish the seeder `LIMIT 1` tail now
or defer.

**Next.** Phase C (auth: MSAL + PyJWT/JWKS), per `docs/design/azure-target.md` — closes the "no auth
anywhere" gap; buildable/verifiable locally. (Or finish the Phase B seeder tail; or browser-walk Complete/Learn.)

## 2026-07-09 (session 8) — Azure + SPA target design

**Context.** The journey app (all 6 stages) has been feature-complete since session 7b, still running
purely local (FastAPI + SQLite + Vite dev server). The user asked what's needed to move it to Azure
plus a hosted SPA — specifically whether Azurite emulation is needed, what app registration(s) enable
SharePoint access, and what else is missing. No code was changed this session; this was pure
architecture/planning.

**Work done.**

- Explored the backend seams (`src/api.py`, `src/db.py`, `src/library.py`, `src/llm.py`,
  connectors/`src/sources.py`) and the frontend (`web/`) to ground the plan in what actually exists —
  confirmed three swappable seams already anticipate this move (LLM, bid library, sources), a
  whitelisted `.env` loader reading straight from `os.environ`, relative `/api` frontend paths, and a
  commented-out `AzureOpenAIProvider` skeleton in `llm.py`.
- Explored `/Users/erichook-marshall/Downloads/Code/talent_grow` — a sibling FWF app already deployed
  in the **same Entra tenant + resource-group family** (`fwf-rg-talentgrow-dev-westeur`). Its Azure
  blueprint (SWA Free + Azure Functions Flex Consumption + Azure SQL AAD-only + Managed Identity
  everywhere, no Key Vault, two path-filtered GitHub Actions workflows) is proven and **live in dev** —
  the target here is to clone it, adapted for a Python FastAPI backend (via `AsgiFunctionApp`) instead
  of TalentGrow's Node Functions.
- Wrote **`docs/design/azure-target.md`** — the design doc: target architecture diagram, answers to
  the framing questions (Azurite only needed for Blob, not SQL/Graph/Entra; app registrations needed —
  API app reg + SPA app reg for MSAL, no secret-bearing app reg for SharePoint since Managed Identity +
  `Sites.Selected` covers it; DB = Azure SQL free serverless offer, ported via a SQLAlchemy Core
  dual-mode shim so local dev keeps SQLite; Managed Identity + federated OIDC cred for CI/CD), a gap
  checklist against the current codebase (biggest gaps: no auth anywhere on the API today, `DB_PATH`
  hardcoded in `db.py:31`, CORS hardcoded to localhost), and a 6-phase path (A design → B DB
  portability → C auth → D hosting scaffold → E Azure-native providers → F provision/go-live).
- **Corrected a false record risk**: TalentGrow's own `infra/README.md` carries a self-note from
  authoring time that the Bicep "had not yet been run through `az bicep build`/`what-if`." The user
  confirmed this is stale — the Bicep **is** deployed and working in TalentGrow's dev environment.
  Recorded this correction in cross-session memory so it isn't resurfaced as a live caveat.

- **Cost + retrieval deep-dive (same session).** Web-verified three facts and folded them into the
  doc's new **Documents & AI retrieval** section: (1) Azure SQL free offer = 100k vCore-sec + 32GB per
  DB, **10 free DBs/subscription**, lifetime — confirmed cheapest, £0 for this workload; (2) docs stay
  in **SharePoint, no Blob** (only the unavoidable pennies-cost Functions deployment storage account);
  (3) AI retrieval without a paid vector store via three seam-swappable options — **A** M365 **Copilot
  Retrieval API** (`POST /copilot/retrieval`, reuses the existing Copilot index over SP, no embeddings
  — spike first), **B** native `VECTOR` type in the free Azure SQL DB (GA Jun-2025, embeddings via
  `AI_GENERATE_EMBEDDINGS`, pennies), **C** cached-text + Full-Text Search (£0 baseline). Cache
  past-response text into the DB regardless — the substrate for all three.
- **Local emulation / dev parity (same session).** Added a section splitting the stack into Tier 1
  (emulate: **SQL Server 2025 container** + Azurite + Functions Core Tools `func start`, optional SWA
  CLI — de-risks Phases B/D with no Azure spend; container's `VECTOR` type tests Option B too) and
  Tier 2 (no emulator — Entra/Graph/Copilot/OpenAI use the provider seams + a real free dev-tenant +
  `LOCAL_AUTH_BYPASS`). Mirrors TalentGrow's local SQL-container + auth-bypass pattern. **Corrected a
  stale fact:** Azure SQL **Edge retired 30-Sep-2025** — the doc's earlier "Azure SQL Edge / SQL Server
  container" line now points only at the SQL Server 2025 container (Rosetta needed on Apple Silicon).

**Decisions.** Entra ID sign-in via MSAL (not Easy Auth, matching TalentGrow's pattern of JWT
validation in app code). Mirror TalentGrow's build pattern (SWA + Functions Flex, not App Service/
Container Apps). Cheapest/free DB → Azure SQL free serverless offer. SharePoint/Graph access via
Managed Identity + `Sites.Selected`, not a secret-bearing app registration. **Docs stay in SharePoint,
no Blob.** AI retrieval: ship the Full-Text baseline, spike the Copilot Retrieval API, hold SQL-native
vectors as the self-contained fallback. Emulate Tier 1 services locally; use seams for Tier 2.

**Open questions raised.** None new beyond what's already tracked in `docs/design/azure-target.md`'s
"Open decisions" — timing of Phases D–F depends on when an Azure subscription/tenant admin access is
available; whether to keep Anthropic (needs one App Setting secret) or switch to Azure OpenAI
(MI-native, no secret) is deferred to Phase E.

**Next.** Start Phase B (DB portability — SQLAlchemy Core dual-mode for `src/db.py`) when the user
picks this thread back up; independent of Azure being provisioned, so it can be built and verified
locally first. See `docs/design/azure-target.md` for the full plan.

## 2026-07-09 (session 7b) — Complete (Stage 4): FOR006 matrix + LocalMirror library + AI pre-fill

**Context.** After Learn shipped (below), the user asked about using "a local file store" for
Complete in the interim. Investigating confirmed the block was overstated: `architecture.md` already
designed a `LocalMirror → GraphSharePoint` provider seam, and the real bid export exists gitignored at
`knowledge/SharePoint Folder/Bids/`. The user chose **LocalMirror over the repo export**. So Complete
was built for real against FWF's actual bid library — the last stage, closing the 6-stage journey.
Grounded to the real `FOR006 Tender Response Master` + `Bid Library Tracker` (data-model.md §4/§4b).

**Work done.**

- **`src/library.py`** (new) — the bid-library provider seam. `LocalMirrorProvider` reads the real
  `Bid Library Tracker.xlsx` (10 category sheets, 9 columns) → LibraryItem dicts. Key wrinkle the real
  data forced: **expiry lives in free-text `Notes`** ("9001 Expires: 09/01/2026"), not a column — so
  `extract_expiries()` mines it (dd/mm/yyyy, "31 Oct 2025", ISO), gated on expiry cues to avoid false
  positives, and surfaces a structured `expiry_date`/`expiry_status` (expired / expiring_soon ≤90d /
  ok). `search()` = lean keyword+tag retrieval; `evidence()` = the credential ledger soonest-expiry
  first; `master_template()` reads the FOR006 question set (fallback questions if the export is
  absent). Degrades cleanly to `available=False` when the file isn't present — never fakes.
  `get_provider()` mirrors llm/sources; GraphSharePoint slots in behind the same interface.
- **`src/response.py`** (new) — the FOR006 ResponseItem rig (18 real columns). Statuses To
  do→Drafted→In review→Approved; `word_count()` + `response_view()` compute the **live word-count
  compliance** (limit vs actual, recomputed from the answer text, never trusted); `matrix_summary()`
  = the completion readout incl. `over_word_limit` (the hard gate — an over-length answer can be
  discarded unread) and a `ready` flag.
- **`src/complete_ai.py`** (new) — retrieval-grounded AI drafting, same shape as `triage_ai.py`
  (reuses `FWF_PROFILE` + `llm.get_provider`). The model drafts one answer *from* the retrieved
  LibraryItems, must respect the word limit, cites `evidence_used`, and flags `gaps`. Never
  auto-saved; 503 if no LLM.
- **`src/db.py`** — `bid_responses` table (`items` JSON matrix, like bid_plans.phases); get/upsert;
  `list_bids_for_complete`; `bid_responses` count in `__main__`.
- **`src/api.py`** — `import library/response/complete_ai`; `/api/complete/reference`,
  `/api/complete/board`, `/api/library` (browse + evidence + provider status), `GET`/`PUT
  /api/bids/{id}/responses` (matrix auto-seeds from the master when unstarted; PUT recomputes word
  counts + validates status server-side), and `POST /api/bids/{id}/responses/{index}/ai-draft`
  (index-based, because `question_ref` repeats across lots).
- **`web/src/api.js`** — `getCompleteReference`/`getCompleteBoard`/`getLibrary`/`getBidResponses`/
  `saveBidResponses`/`aiDraftResponse`.
- **`web/src/stages/CompleteStage.jsx`** — replaced the mock. Board (per-bid completion bar + library
  provider strip) → a two-pane workspace: the compliance matrix (status dots + per-question word
  badges) + the selected question's editor (question text, live word-count check, status/owner, an
  "✦ AI draft" button that fills the answer + shows win-themes/evidence/gaps), plus the evidence
  ledger (credential expiry, expired in red). Reuses the mock's `.ws`/`.qlist`/`.draft`/`.ledger`/
  `.dotp` CSS.
- **`web/src/journey.js`** — Complete flipped `design → live` ("Works today (FOR006)"), asset updated.
- **`web/src/styles.css`** — added `.complete`/`.lib-strip`/`.complete-ws`/`.resp-text`/`.resp-foot`/
  `.ai-meta`/`.ai-gaps` + `.qi` button/scroll tweaks. Reused the mock Complete classes.
- **`src/seed_complete_demo.py`** (new) — seeds RTPI's matrix from the real 8-question master with a
  status spread + a placeholder answer (clearly marked DEMO). Library is read live, never seeded.

**Verification (honest).** `python3 src/library.py` → provider available, 42 items/10 categories, 1
expired (ISO Certifications 2025-10-31, parsed from Notes). `python3 src/response.py` → matrix maths +
over-limit detection. Over real HTTP: `/api/complete/board` 200 (library available, 42 items);
`/api/library` evidence ledger 19 items, expired first; GET matrix auto-seeds 8 real questions;
PUT an 800-word answer → `over_limit=True`, summary `over_word_limit=1` (word count recomputed
server-side); **AI draft retrieval-grounded** — 666–680 words within the 750 limit, cites real library
items, names win themes, honestly flags "no named case study cited" (claude-haiku-4-5, live `.env`
key); out-of-range index → 404. `cd web && npm run build` clean (37 modules). Removed the bid-8 test
matrix to restore the seed state; services stopped.

**Result.** The journey is feature-complete — all six stages (Search/Triage/Plan/Complete/Manage/
Learn) are real and wired to `bids.db`. No preview screens remain. CLAUDE.md spine + roadmap updated.

**Next.** Browser-walk Complete/Learn, commit the milestone, or polish. See handover Active task.

## 2026-07-09 (session 7) — Learn (Stage 6): B07 outcome + win-rate + library-feedback loop

**Context.** App ran through Stage 5; the open decision was what next. User confirmed the **browser
click-through was done and the stages look fine** (clearing the 5-session "0 human-reviewed" thread),
and chose to **build Learn (Stage 6)** — no external blocker, and it closes the journey loop (outcome
capture → library feedback). Built as a close parallel to Plan/Manage: new domain module, one new DB
table, reference/board/GET/PUT endpoints, a real board→detail UI replacing the mock, a demo seed.
Grounded to the authoritative B07/Outcome vocabulary in `docs/design/data-model.md §6` — not invented.

**Work done.**

- **`src/outcome.py`** (new) — the B07 Outcome rig, mirroring `clarification.py`/`bidplan.py`.
  `RESULTS` (Awaiting/Won/Not Won/Withdrawn — Awaiting = submitted-but-undecided, the honest
  pre-decision state), Lessons Learned categories, `LIBRARY_ACTIONS` (promote/refresh/retire).
  `score_pct()` tolerantly parses "88", "88/100" or a bare 0–100. `library_suggestions()` derives the
  loop-closing suggestions from the result (Won→promote headline, Not Won→refresh headline) + any
  lesson tagged with an action. `winrate_summary()` = won/(won+not_won), **withdrawals excluded** from
  the denominator (not a competitive loss), plus avg score % and by-result counts. `alerts()` nudges
  on submitted-but-unrecorded + decided-with-unapproved-suggestions (tolerant of both the board-card
  and raw-view shapes). `python3 src/outcome.py` self-checks the maths.
- **`src/db.py`** — `bid_outcomes` table (scalars + `lessons` JSON, like `bid_plans.phases`);
  `BID_OUTCOME_FIELDS`/`BID_OUTCOME_JSON_FIELDS`; `get_bid_outcome`/`upsert_bid_outcome`;
  `list_bids_for_learn` (joins opportunities + `bid_manage.submitted` + `bid_outcomes`, most-recently-
  closed first); `bid_outcomes` count in `__main__`. UNIQUE(bid_id) → re-record updates in place.
- **`src/api.py`** — `import outcome as L`; `/api/learn/reference`, `/api/learn/board` (win-rate +
  alerts + cards), `GET`/`PUT /api/bids/{id}/outcome`. `_learn_item` tracks `saved` so the win-rate
  only counts real records (an un-recorded bid sits at default Awaiting, not counted). The PUT
  validates `result` (→ 400 on unknown) and normalises `lessons` to the known shape.
- **`web/src/api.js`** — `getLearnReference`/`getLearnBoard`/`getBidOutcome`/`saveBidOutcome`.
- **`web/src/stages/LearnStage.jsx`** — replaced the mock. Win-rate panel (reuses `.cap`/`.bar`),
  loop-closing alert strips, a card grid, and a board→detail flow: outcome form (result/score/winner/
  dates/feedback), an editable Lessons Learned register, a read-only derived-suggestions list
  (promote ▲ / refresh ↻ / retire ▼), and Save + "Approve library updates" sign-off. Honest `.src-note`:
  approved updates flow to the Stage-4 library once SharePoint is stood up — nothing is written here.
- **`web/src/journey.js`** — Learn flipped `design → live` ("Works today (B07)"), asset text updated.
- **`web/src/styles.css`** — added `.p-wait` (Awaiting pill), `.winrate`/`.wr-facts`, `.lesson-row`/
  `.lesson-note`, `.km-sub`. Reused the existing `.lib-act`/`.ic-*`/`.outcome-head` mock styles.
- **`src/seed_learn_demo.py`** (new) — illustrative outcomes on the same demo bids: RTPI Won (88%,
  promote lessons, submitted), SPM Not Won (61%, lost to a named incumbent, retire lesson), SUMIT left
  unrecorded (Awaiting). Gives a 50% win rate tracked bid-by-bid. `--clear` resets.

**Verification (honest).** `python3 src/db.py` → `bid_outcomes: 2` (21/3/3/3/3 intact). `python3
src/outcome.py` self-check: 50% win rate, avg 74. Over real HTTP (`uvicorn` on :8000):
`/api/learn/reference` 200; `/api/learn/board` 200 — win rate 50% (1W/1L/0WD, 1 awaiting), avg 74%,
**2 alerts** (after fixing an initial shape mismatch where `alerts()` read `suggestions` but the board
passes `suggestions_count` — made `alerts()` tolerant of both); GET detail resolves RTPI→3 / SPM→2
suggestions; `PUT {result:"Maybe"}` → **400**; a valid Withdrawn PUT round-tripped and re-derived its
suggestion (then removed the stray test row to restore the seed state). `cd web && npm run build` →
clean, 39 modules. Services stopped.

**Finding — Complete (Stage 4) is NOT hard-blocked.** Investigating the user's "we have a local file
store" question: `docs/design/architecture.md` designed a **`LocalMirror` → `GraphSharePoint`
provider seam**, and the real bid export already exists (gitignored) at `knowledge/SharePoint
Folder/Bids/` — incl. `02 Bid Library/Bid Library Tracker.xlsx` (LibraryItem + expiry register),
`01 Bid Forms/FOR006 Tender Response Master.xlsx` (ResponseItem schema), and real per-bid `FOR006`
compliance matrices. A `LocalMirror` over this real export, behind the seam, is the **sanctioned**
path (the hard rule forbids *faking* SharePoint / *committing* confidential content, not reading a
real local export). So Complete can be built for real now — the "blocked" framing was overstated.
Recorded as the recommended next build.

**Next.** Build **Complete (Stage 4)** via `LocalMirror`, or pause. See handover Active task.

## 2026-07-09 (session 6) — Manage (Stage 5): FOR003 clarification register + pre-flight gate

**Context.** Structure was clean and the app ran through Stage 3; the open decision was which stage
to build next. User chose **Manage (Stage 5)** — no external blocker (unlike Complete, which needs
live SharePoint/MS Graph) and it directly encodes the missed-clarification failure this whole tool
exists to prevent. Built as a close parallel to Plan (Stage 3): a new domain module, one new DB
table, board + reference + detail endpoints, a real board→detail UI replacing the mock, and a demo
seed. Grounded to the authoritative FOR003 vocabulary in `docs/design/data-model.md §5/§5b` — not
invented.

**Work done.**

- **`src/clarification.py`** (new) — the FOR003 CQLOG + pre-flight domain rig, mirroring
  `bidplan.py`. Vocabularies (clarification statuses Open→Drafting→Submitted→Answered; the 9-item
  pre-flight checklist template from §5b). `resolve_preflight()` enforces the two items the tool
  won't let anyone tick past: the *auto* "clarifications resolved" item (derived from the register)
  and the *expiry* items (a credential past its `expiry_date` auto-fails — the expired-cert failure).
  `preflight_summary()` gates submission (blocked unless every mandatory item passes). `alerts()` is
  the founding-failure signal: clarification-deadline PASSED / imminent-with-no-owner / gate-blocked-
  near-submission. Reuses `bidplan.days_until` for the date maths (one shared utility, not re-derived).
- **`src/db.py`** — new `bid_manage` table (one row per bid, UNIQUE(bid_id)), holding the
  `clarifications` + `preflight` repeating groups as JSON exactly like `bid_plans.phases`. Added
  `BID_MANAGE_FIELDS`/`BID_MANAGE_JSON_FIELDS`, `get_bid_manage`/`upsert_bid_manage`, and
  `list_bids_for_manage` (bids ⋈ opportunities ⋈ bid_manage). Kept outside the connector path.
- **`src/api.py`** — `GET /api/manage/reference`, `GET /api/manage/board` (per-bid summaries +
  computed alerts), `GET`/`PUT /api/bids/{id}/manage`. The PUT **enforces the gate server-side**:
  `submitted:"yes"` is only honoured if pre-flight actually clears (else **409** with the reason) —
  never trusts the client. Register/checklist rows are normalised to known fields on write.
- **`web/src/`** — `api.js` client fns; `ManageStage.jsx` rewritten from the mock into a real
  board→detail view (bid cards with open-clarification counts + deadline badges + gate pills; a
  detail with an editable FOR003 register — owner, **backup**, deadline **with time + timezone** —
  and the pre-flight checklist with a submit button that stays disabled until the gate clears);
  `styles.css` Manage block (reuses kcard/alert-strip/checklist/pd-facts tokens); `journey.js` Manage
  flipped `design → live` with honest asset copy.
- **`src/seed_manage_demo.py`** (new) — hangs illustrative registers off the 3 existing demo bids,
  exercising every signal: SUMIT (clarification deadline PASSED, no owner → the founding failure),
  SPM (imminent but owned + backed up; gate blocked by an expired Cyber Essentials cert), RTPI
  (answered, gate clear, submitted — the done state). `--clear` resets.

**Verified (real HTTP, not just TestClient).** `python3 db.py` → `bid_manage: 3` after seed, other
counts intact (21 opps / 3 quals / 3 bids / 3 plans). `GET /api/manage/board` 200 — alerts ordered
most-urgent-first: "clarification CQ01 deadline PASSED 3d ago", gate-blocked-near-submission crits,
imminent-but-owned warn. `GET /api/bids/8/manage` shows the auto item ("1 clarification still open")
and the expiry item ("Cyber Essentials expired 24d ago") both enforced to fail → gate blocked ×2.
`PUT …/manage {submitted:"yes"}` on a blocked bid → **409**. RTPI reads submitted=true, gate clear.
`npm run build` compiles clean (39 modules). Services stopped; build artifact removed.

**Browser review + UI polish (first human click-through, at last).** User walked the running app in
the browser — the standing "0 stages reviewed" thread is now partly closed. Feedback was layout, not
logic: the screens were too tight and AI-filled textareas were clipping. Fixes, all in
`web/src/styles.css`: widened the shared `.wrap` container **1200px → 1600px** (28px gutter) so every
screen uses more of the viewport while keeping a margin; textareas now **auto-grow** (`field-sizing:
content`, min ~4.4em, max 260px) so AI pre-fill isn't clipped; the two Triage long-text fields
(Project requirement / Scope summary) changed from a narrow `auto-fill` grid to an explicit two-up
`1fr 1fr` that **stretches both to equal height** (each textarea `flex: 1`), and a lone `.fgrid.areas`
field (Plan/Manage Notes) now spans full width. User confirmed "this looks good now." No JS/logic
touched; verified live via Vite HMR.

**Not done / deferred.** Full stage-by-stage review still light (user focused on Triage's form); the
standing thread). Complete (Stage 4) remains the SharePoint-blocked one. The pre-flight gate
re-checks on *save* (server-authoritative), not live per-keystroke — a deliberate simplicity call
matching how Plan's capacity/alerts recompute on board reload.

## 2026-07-09 (session 5) — Repo restructured: flattened the nested sub-app

**Context.** A folder rename dropped the chat history; on re-orientation the user flagged that the
`discovery/` sub-folder had grown into the whole app yet still carried its own duplicated
project-discipline files (`_session/`, `.claude/`, `CLAUDE.md`) alongside the top-level set — and
that the name "discovery" no longer reflected a 6-stage bidding app. Their other projects
(`talent_grow`, `wa_poc`, `BFSIAgent`) all use one `CLAUDE.md` + `README.md` + `_session/` at the
repo root with code in `src/`/`web/`, never a nested self-contained sub-project. Asked which layout;
user chose **backend under `src/`, `web/` at root**.

**Work done.**
- Moved `discovery/*.py` → `src/`, `discovery/web` → `web/`, `discovery/support` → `support/`,
  `discovery/requirements.txt` → repo root. `bids.db`, `.env`, `.env.example` moved into `src/`
  because `db.py`/`config.py`/`api.py` resolve them relative to `__file__` — they must sit beside
  the code. Imports left untouched (all bare, e.g. `import db`): the app runs via
  `uvicorn api:app --app-dir src` and scripts via `python3 src/x.py`, both of which put `src/` on
  `sys.path` — zero import edits, zero code churn.
- Consolidated the duplicated discipline: deleted stale `discovery/.claude` (root `.claude` is the
  current project-wide set — the discovery copies were PoC-era), merged `discovery/CLAUDE.md`'s
  app/record-shape detail into root `CLAUDE.md`, merged `discovery/_session/` (session-4 hot state)
  into this top-level triad. Repointed root `.gitignore` `discovery/bids.db` → `src/bids.db`
  (+ `-wal`/`-shm`). Fixed `discovery/` path references in `CLAUDE.md`, `README.md`, the
  `_session/` triad, the `.claude/skills` and `docs/design/data-model.md`.
- `discovery/` folder removed entirely (`rmdir` clean).

**Verification — real, from the new layout.**
- `python3 src/db.py` → `DB ready at …/src/bids.db`, `opportunities: 21`, `qualifications: 3`,
  `bids: 3`, `bid_plans: 3` — all data intact, DB found via `__file__`-relative path.
- `import api` clean (bare imports resolve with `src/` on path); `.env` loads the Anthropic key from
  `src/.env` without an explicit export.
- Live HTTP: `uvicorn api:app --app-dir src --port 8011` → `/api/meta` 200 and the session-4
  `/api/plan/board` 200. Server killed after.

**Decisions.** Flat repo, no nested sub-app — one `CLAUDE.md` + one `_session/` triad + one
`.claude/` at root, matching the user's other projects. Backend grouped under `src/` (keeps the root
tidy next to `skills/`/`knowledge/`/`docs/`); `bids.db` + `.env` travel with the code in `src/`;
`--app-dir src` chosen over converting to a package so imports stay untouched.

**Open questions raised.** None new. Carried forward: which stage next (Manage vs. Complete); the
running shell is still unreviewed by a human in a browser (4 sessions now).

**Next.** Pick Manage vs. Complete for the next stage — or get the user's first browser
click-through of the shell (Search + Triage + Settings + Plan all real and server-side-verified).

---

## 2026-07-09 (session 4) — Plan (Stage 3) built: pipeline board + capacity + FOR002 timeline

**Context.** Resumed via `/resume-prompt`. The handover offered a fork: Plan (Stage 3, "highest-value
missing piece" per `journey.js`) vs. extending Complete with the AI-drafting pattern from session 3.
Asked the user directly; they chose **Plan**.

**Work done.** (Paths below are pre-restructure; the files now live under `src/` and `web/`.)
- `bidplan.py` (new) — FOR002 domain module mirroring `qualification.py`: the fixed 15-phase timeline
  (from `docs/design/data-model.md` §3b), 6 pipeline stages, owner roles, phase statuses. Two pure
  computations: `capacity_summary()` (committed FOR001 bid-effort vs a team-capacity default) and
  `alerts()` (deadline/owner/capacity warnings, crit-before-warn) — including the clarification-deadline
  alert, the direct encoding of the G-Cloud 15 founding failure. Default team capacity 25 person-days
  (a tuned placeholder, flagged as needing a real source).
- `db.py` — new `bid_plans` table (`UNIQUE(bid_id)`, JSON `phases`), `get_bid_plan`/`upsert_bid_plan`
  (same pattern as qualifications), `list_bids_for_board` (joins bid → opportunity → qualification).
  Migration re-ran against the live DB: `opportunities: 21` unchanged, idempotent.
- `api.py` — `GET /api/plan/reference`, `GET /api/plan/board` (`?capacity_days=` override; server
  computes days-to-deadline, groups into pipeline columns, returns capacity + alerts),
  `GET`/`PUT /api/bids/{id}/plan` (seeds a blank 15-phase timeline if unplanned).
- `web/src/api.js`, `web/src/stages/PlanStage.jsx` — real board (clickable cards, deadline badges,
  editable capacity input) replacing the mock; a per-bid FOR002 timeline detail view. Reused the
  mock's board/kcard/cap/alert-strip CSS; added board/badge/timeline CSS to `web/src/styles.css`.
- `web/src/journey.js` — Plan flipped `state: "gap" → "live"`.
- `seed_plan_demo.py` (new) — idempotent, `--clear`-resettable demo seeder: drives 3 real stored
  opportunities through the genuine Triage "Go" path so the board has real data to review. Never
  touches the underlying opportunities.

**Verification — real, not asserted.**
- `python3 db.py`: migration clean, counts correct before/after.
- FastAPI `TestClient`: full Triage→bid→Plan round trip (Go creates a bid, board groups it, GET seeds
  a blank plan, PUT persists a pipeline move + phase edit, board re-renders), cleaned back to `21/0/0/0`.
- Live `curl` against a running `uvicorn` with the demo seed: 3 bids grouped into 3 columns; capacity
  `28.5/25.0 → over` (RTPI in *Submitted* correctly excluded via `PIPELINE_DONE` filtering); alert
  stack led with over-commitment, then SUMIT's clarification-deadline-in-2d (crit), then a no-owner
  warning that **auto-downgraded** once an owner was assigned via a live PUT — confirms alerts are
  computed reactively, not cached.
- `npm run build` clean. Vite dev server verified serving (`200`) and proxying `/api` (`200`).
- Demo data reset to a clean state (`--clear` + reseed) before session end.

**Decisions.** Plan chosen over extending Complete (user's direct choice). Demo-data strategy for
reviewable-but-undecided stages: a small, clearly-labelled, idempotent, resettable seed script rather
than an empty board or hand-edited DB. Team capacity kept as a request-time override (not persisted) —
sufficient for a PoC demo, flagged as needing a real source.

**Open questions raised.** Which stage next: Manage (Stage 5, no external blocker, on-thesis) vs.
Complete (Stage 4, next in order but blocked on live SharePoint/MS Graph). Team capacity default needs
a real source.

**Next.** Pick Manage vs. Complete — or get the user's first browser click-through of the shell.

---

## 2026-07-09 (session 3) — Triage (B01) live + AI pre-fill + Settings screen

**Context.** Continued straight from session 2's Active task ("wire Triage for real"), then the
user asked to add AI pre-fill for the Triage form — flagged as the biggest time-saver in the whole
tool, with an explicit heads-up that the provider would need to move from Anthropic to Azure
OpenAI later, so the design had to plan for that swap up front. After it shipped, the user flagged
cost as a factor and asked to move off the default (more expensive) model, then asked for a
Settings screen to manage the AI config day-to-day.

**Work done.** (A more granular version of this entry lived in the old `discovery/_session/` log,
now folded away by the session-5 restructure — preserved in git history.) Summary: (1) Triage —
FWF's real FOR001 qualification form (go/no-go RAG scoring +
complexity→cost rig, verified against the source spreadsheet's totals exactly) wired to two new
`bids.db` tables and a real form in `TriageStage.jsx`, replacing the mock; a Go decision now
promotes an opportunity into a `Bid`. (2) AI pre-fill — a provider-agnostic seam (`discovery/llm.py`)
using forced tool/function calling (chosen because it maps identically onto Azure OpenAI's shape),
with `AnthropicProvider` built and an `AzureOpenAIProvider` skeleton deferred until Azure access
exists; `triage_ai.py` drafts the full FOR001 from a notice + a concise FWF profile, for human
review only — never auto-saved. Default model set to `claude-haiku-4-5` after the cost
conversation. (3) Settings — a new `#settings` screen (`config.py` + `SettingsView.jsx`) where a
non-technical user can pick provider/model, enter an API key (write-only — stored in gitignored
`discovery/.env`, never sent back to the browser), and hit **Test connection** for a live check.

**Decisions.**
- Structured AI output via forced tool/function calling, not a newer SDK-specific API — it is the
  shape common to both Anthropic and Azure OpenAI, which is what makes the seam thin.
- AI default model: Haiku 4.5, not Opus — an explicit, user-directed cost tradeoff for a
  review-before-save task, and validated live (the draft's reasoning held up on a real notice).
- Settings screen accepts and stores the API key itself (novice-friendly) rather than requiring
  hand-edited `.env` — user's explicit choice, weighed against a smaller secret-handling surface.
- Storage question from session 2 (extend `bids.db` vs. a separate store) is now resolved:
  extended `bids.db` in place.

**Open questions raised.** None new that block the project. Carried forward: Azure OpenAI provider
still to build (client will need it, timing depends on their Azure provisioning); the running
shell is still unreviewed by a human in a browser, now 3 sessions running.

**Next.** Plan (Stage 3) — `docs/design/data-model.md` §3 is fully specified and the app itself
flags it as the highest-value missing piece. (Built the following session — see the session-4
entry above.)

---

## 2026-07-09 (session 2) — Data model derived from FWF's real SharePoint bid store

**Context.** Resumed via `/resume-prompt` after the app-shell session. User had copied FWF's actual
SharePoint bid store (26 real bids, forms, trackers) into `knowledge/SharePoint Folder/` and asked what
could be derived from it to shape the data model — the open decision the previous session left behind.

**Work done.**
- Explored the SharePoint mirror (512 files, 26 per-bid folders under `03 FWF Bids/`, a repeated
  taxonomy `00 Bid Admin → ... → 07 Post Submission`). Parsed the key structured artifacts with
  openpyxl/python-docx: `FOR001` (Bid Qualification Questionnaire — incl. a real go/no-go scoring rig,
  complexity × day-rate → estimated bid cost), `FOR002` (BidPlan timeline), `FOR003` (CQLOG /
  clarification log), `FOR004` (Bid Opportunity Overview), `FOR006` (Tender Response Master — the
  compliance-matrix / AI-prefill schema), `Tender Pipeline.xlsx`, `Bid Library Tracker.xlsx`,
  `Bid_Discovery_Assessment.xlsx`, and the `Public Sector Bidding Framework.docx` process doc.
- Wrote `docs/design/data-model.md` — the shared bid record across all six journey stages, derived
  (not invented) from those real artifacts: `Opportunity` → `Qualification`/`Bid` → `BidPlan` →
  `ResponseItem`/`LibraryItem` → `Clarification`/`ComplianceCheck` → `Outcome`. Flags
  `clarification_deadline` and credential `expiry_date` as first-class fields — both tie directly to
  the admin-failure story that motivates this whole project.
- User said "go ahead and start" — applied the first slice (§1, `Opportunity` extension) to
  `db.py` (then `discovery/db.py`, now `src/db.py`). File-level detail preserved in git history
  (the old `discovery/_session/` log, folded away by the session-5 restructure).
- **Found and fixed a real exposure**: the copied SharePoint folder (financials, insurance certs,
  personal CVs, contract examples) was untracked and unignored in git — a direct hit against the
  CLAUDE.md hard rule on client-confidential content. Added `knowledge/SharePoint Folder/` to
  `.gitignore`; confirmed excluded via `git check-ignore -v` (first attempt failed because the pattern
  was mistakenly quoted — gitignore doesn't need shell-style quoting for spaces in paths).
- Found services left running from the prior session (`uvicorn`, `vite`) — stopped at this session's
  start; a gap in that session's end-session pass.

**Decisions.** The data model is derived from FWF's real usage, not designed fresh — this is treated as
higher-confidence than a from-scratch design since it reflects what a working bid team already does.
Triage-enrichment fields added as columns on the existing `opportunities` table (not a new table yet),
mirroring the existing `lifecycle` pattern.

**Open questions raised.** (1) Extend `bids.db` with further tables vs. a separate store for
`Qualification`/`Bid`/etc. — recommended to extend, not yet decided formally. (2) Enum vs. free-text for
fields FWF's own forms treat inconsistently (`opportunity_type`, `pipeline_stage`).

**Next.** Build the Triage (B01) entity for real: `Qualification`/`Bid` table(s) in `discovery/db.py`
per `data-model.md` §2, then wire `TriageStage.jsx` off it instead of the mock screen.

---

## 2026-07-09 — App shell built (definition step (b) chosen)

**Context.** Resumed via `/resume-prompt`. The standing question was data model vs. app shell; user
chose **app shell first**. Built it as an extension of the discovery front end per
`docs/design/architecture.md`. Mid-session feedback ("not enough mock data for future stages to get a
clear picture") drove a second pass adding populated mock screens.

**Work done.** All under the frontend (then `discovery/web/`, now `web/`; more granular detail in
git history via the old `discovery/_session/` log):
new `journey.js` (6-stage single source of truth), `App.jsx` rewritten into the journey shell (top bar,
stepper nav, hash routing, ←/→ keys, theme toggle), new `stages/` dir (SearchStage = real search UI
lifted out; MockStage + ScopeCard shared layout; Triage/Plan/Complete/Manage/Learn = populated
illustrative preview screens ported from the mockup; StagePlaceholder now dead code), `styles.css`
adopted the mockup's design tokens (light + dark) with legacy aliases, `index.html` title → Bidpath.

**Verification (real runs).** `npm run build` → 31 modules (first pass) then 38 (with mock stages),
no errors. Backend + dev server started for real: `db.py` → 21 rows; `curl :8000/api/meta` → total 21;
`curl :5173/api/opportunities` via Vite proxy → count 21; every changed module → HTTP 200, no transform
errors. Services stopped cleanly at end. **Not verified:** in-browser click-through — no browser tool
this environment; only compile/transform/data-plumbing observed. Handed user the running URL to check.

**Decisions.** App shell built on the discovery app (not a new codebase); stage selection in the URL
hash (no router dependency); not-yet-built stages show labelled populated preview screens, not abstract
scope text, so their intended shape is legible before real wiring.

**Open questions raised.** None new. The data model (shared bid record) is now the concrete blocker for
wiring the mock stages to real data.

**Next.** User reviews the shell in a browser; then build the data model as the next real step.

---

## 2026-07-09 — Session closed, no new work (question left open)

**Context.** User invoked `/end-session` immediately after the 2026-07-08 design session, without
answering the pending question (data model vs app shell next).

**Work done.** None — checked git status (clean, HEAD `85ac33a`, matches last commit) and confirmed no
files changed since. Nothing to verify beyond that; no code was run.

**Decisions.** None new.

**Open questions raised.** None new — the standing question (data model vs app shell) remains open.

**Next.** Get the user's answer on data model vs app shell, then proceed accordingly.

---

## 2026-07-08 — Definition: journey mockups + architecture direction

**Context.** User pushed back on jumping to build — architecture/UI/scope weren't decided. Switched to a
definition-first process. User chose **mockups-first**, starting at **Step 2 (journey & scope)**.

**Work done.**
- Built `docs/design/journey-mockups.html` — an interactive 6-stage journey strawman (Search → Triage →
  Plan → Complete → Manage → Learn), real FWF/procurement content, each stage = mock screen + scope card
  (what user does / where AI helps / human decides / v1 in-out). Published as an artifact. **User approved
  the style and shape.**
- Captured architecture direction in `docs/design/architecture.md` (Step 3): **local app now** (extend the
  discovery PoC — FastAPI + SQLite + React/Vite), **Azure SPA = budget-dependent longer-term goal**,
  SharePoint via a **library-provider seam** (`LocalMirror` now → `GraphSharePoint` later, mirroring the
  `sources.py` registry pattern). AI drives task completion.
- Noted **HubSpot integration** as a future feature (pipeline ↔ CRM) per user request — parked, not scoped.
- Updated handover + todo.

**Decisions.** Mockups-first method; six-stage journey + visual style approved; local-app-now / Azure-later;
library-provider seam for SharePoint; stack = extend discovery. "Bidpath" is a placeholder name only.

**Open questions raised.** Next step: data model vs app shell? How does `LocalMirror` get seeded (Graph
export vs manual vs samples — parked to Stage 4)?

**Next.** Confirm the next definition step with the user (data model, or start the local app shell).

---

## 2026-07-08 — Phase 0: consolidate, verify, and scaffold the project

**Context.** First working session. Started from three loose, unconnected folders (a working
"Public Sector Checker" PoC, a "Public Sector Bid Skills" B00–B07 library, and support docs) plus
FWF strategy docs. Goal: understand the whole, then consolidate into one useful, connected toolset.

**Work done.**
- Read everything of substance: FWF strategy docs (Current Position, Recovery Plan, Knowledge Base —
  all mislabelled `.docx`, actually markdown), the skills-review transcript, the B00–B07 skill chain +
  SharePoint architecture, and the discovery PoC (code, session notes, DB — 21 rows, 2 sources).
- Reorganised into clean structure: `Public Sector Checker` → `discovery/`, `Public Sector Bid Skills` →
  `skills/`, `support` → `knowledge/`. Renamed mislabelled `.docx` → `.md`.
- `git init` + `.gitignore` (excludes `bids.db`, `node_modules`, `__pycache__`, secrets), added remote
  `github.com/EricHookMarshall/public-sector-bidding-tool`. Absorbed the discovery PoC's nested `.git`
  (only a stale "Initial commit" + uncommitted work) into the one repo. Pushed to `main` (56 files).
- **Verified the volatile procurement facts** (live web search, dated 2026-07-08) → `knowledge/VERIFIED_FACTS.md`.
  Foundations sound (CCS→GCA 1 Apr 2026 ✓, PA23 24 Feb 2025 ✓, MEAT→MAT ✓, G-Cloud 15 autumn-2026 ✓).
  **Correction found:** RM6263 is expired/closing (successor DOS7) — the recovery plan's "assess RM6263"
  is stale. RM6190 Technology Services 4 (live Dec 2025) is a strong live candidate.
- Wrote `README.md` (the journey spine), then `CLAUDE.md` (working spine), this `_session/` triad
  (cleansed from the wa_poc reference project), and the `/resume-prompt` + `/end-session` skills.
  Second commit `ac80d80` pushed to `main`; working tree clean. Closed the session via `/end-session`.
- **Verification this session:** doc/scaffold work only — nothing code-executable to run beyond git
  (verified: clean tree, 2 commits on `main`, no `bids.db`/`node_modules`/secrets staged). The earlier
  fact-verification used live web search (recorded in `knowledge/VERIFIED_FACTS.md`). Discovery code
  was **not** re-run this session.

**Decisions.** Breadth-first (thin end-to-end) sequencing. One flattened repo (not submodules).
Clean lowercase folder names. Keep discovery's own sub-spine (`discovery/CLAUDE.md` + `_session/`)
alongside the new top-level project spine (two-tier, coexisting).

**Open questions raised.** Product form (grow discovery UI vs separate bid workspace)? SharePoint
timing — Phase 3 blocked on MS Graph credentials (only Google Drive connector available here).

**Next.** Phase 1 — wire discovery → triage (shared record → B01 bid/no-bid decision), breadth-first.
