# TODO — active queue

> **Unfinished work only.** Completed items are cold history — see [`progress.md`](progress.md)
> (most-recent-first, full dated retrospective per session). Everything through **session 13 is
> committed** (`9c31fa8`). When an item ships, note it in `progress.md` and delete it here.

## 🔴 ESCALATE — business-urgent, cannot be fixed in code (session 25)

> Surfaced by the deep read of the bid library ([`docs/bid-library-deep-review.md`](../docs/bid-library-deep-review.md)).
> **These outrank every code item below.**

- [ ] **🔴 The ISO certificates belong to a different legal entity.** ISO 9001 *and* ISO 27001 are issued to
      **Future Work Force SRL** (Romania) — **not** Future Work Force **Limited** (UK, CH 11934102) — and both
      are **also expired**. The files are named `FUTURE WORK FORCE - ISO 9001.pdf` in FWF's own credentials
      folder, so they read as *ours*. **Attaching one to a UK selection question is a misrepresentation.**
      FWF Ltd holds **no ISO cert of its own**. For 27001 the honest answer is the **Arobs *group*** position
      (BV letter `L/BUH/06.11.2025/423/BCT`, ISO 27001:2022, Oct 2025) — stated as *group* certification.
      **Decide the standing answer, then reconcile every portal to it.**
- [ ] **🔴 CCS MI returns — possible live breach.** The portal tracker says *"must submit MI **monthly**,
      AI DPS RM6200, SPARK DPS RM6094"*; `07 CCS MI Reports/` holds **only a blank template**. Monthly MI
      (**incl. nil returns**) is mandatory — non-submission attracts charges and can **suspend an appointment**.
      **Verify whether returns are being filed elsewhere.**
- [ ] **🟠 Rotate the portal passwords.** Cleartext in `Portal Registration Tracker.xlsx`, **reused across
      portals**, on a **departed employee's** accounts. Rotating — not re-filing — is the fix.
- [ ] **Cyber Essentials has lapsed** (due 06/06/2026). Renew, then update the **AI DPS + Spark** Q155 answers
      (they still say *No* while RM6173 says *Yes*).
- [ ] **Reconcile the four `KNOWN_CONFLICTS`** (turnover £100m vs <£36m · PI £10m declared vs £2m actual ·
      Cyber Essentials · the three company-name variants) **and the reference-contract mismatch** (Close
      Brothers: library £1m/Jag Bassi vs portal £2m/Steve Durnin). **Delete each entry from `answers.py` once
      reconciled** — a stale conflict flag is its own kind of lie.

## A-series — the standard-answer bank (session 25)

- [x] **A1 — deterministic answer bank** (session 25) — SHIPPED. `src/answers.py` + `standard_answers` table +
      `/api/answers/{reference,board,lookup}` + `PUT /api/answers/{key}` + `POST /api/answers/sync-from-library`
      + `tests/test_answers.py` (24). Docs: [`docs/standard-answers.md`](../docs/standard-answers.md).
      **A lookup, never a generator** — answers from record with provenance, or refuses. Question definitions
      committed; **values live only in the gitignored `bids.db`**, re-seeded from the library on every startup
      (never overwriting a human-verified value). Readiness gate: only `ready` is auto-fillable.
      **33 answers: 16 ready · 7 gap · 4 conflict · 4 confirm-per-bid · 2 wrong-entity.**
- [ ] **A2 — the Answers UI** ⭐ **NEXT CODE TASK.** The bank is **API-only**. Build a panel that takes a
      buyer's question *in their own words*, shows the answer + **the file to attach**, and **refuses loudly**
      on `wrong_entity` / `conflict` / `gap`. Wire it into Complete (Stage 4) beside the compliance matrix.
- [ ] **A3 — fill the 7 gaps.** No document exists for: **Modern Slavery policy** (the user's own example —
      the honest answer today is *No*), **Anti-Bribery**, **Environmental & Sustainability**, **Carbon
      Reduction Plan (PPN 06/21** — often *mandatory* on central-gov work**)**. Plus **CDP identifier**, **SME
      status**, **parent-company guarantee** — all answered on the portals but nowhere in the library; confirm
      once via `PUT /api/answers/{key}` and they stick.
- [ ] **A4 — answer the "narrative" questions properly.** The bank deliberately excludes anything needing
      judgement (H&S arrangements, GDPR technical measures, technical ability). Those belong to Complete's AI
      pre-fill, grounded on the library — **not** the bank. Keep the boundary.

## Feature backlog (needs scoping with the user)

- [x] **C3 — "Compliance & Renewals" view** ⭐ (session 19) — SHIPPED. App-owned `compliance_assets`
      register + gitignored file store (`compliance_store.py`, SharePoint seam later) + org-level view
      (`ComplianceView.jsx`, `#compliance`). Uploads, updatable, expiry derived live; seeded from the real
      library incl. the EXPIRED ISO. Full retrospective in `progress.md`.
- [ ] **C-series follow-ons** (from the C3 MVP) — **phase-2:** extract expiry from uploaded **PDF/docx
      bytes** (today mined from name/notes text only); **file-replace** in the edit form (delete+re-add now).
      **C4:** framework/contract membership-period tracker (RM6263-expired precedent) — the `Frameworks`
      category exists but has no data source yet; scope with the user. **SharePointStore** behind the
      `compliance_store` seam when MS Graph lands.
- [ ] **C1 — clarifications: discoverability + AI dedupe** — the FOR003 register exists on Manage (click a
      bid); make the drill-in obvious (board shows only a count). NEW: AI-ingest incoming CQs, dedupe, flag
      "already answered by CQ #n".
- [ ] **C2 — per-bid workspace + slim per-bid KB** — opportunity visible, edits saved, a bid-specific KB the
      AI grounds on. Net-new; aligns with the `skills/` 3-library design. Needs a design pass.
- [ ] **F-series — more sources / search** — F1: **Public Contracts Scotland ✅ + Sell2Wales ✅ built
      (session 20)** — 4 connectors now behind the `sources.py` seam. **PCS** (`public_contracts_scotland.py`)
      live-verified, returns real Scottish IT opps; TLS resolved securely (server omits its intermediate cert
      → pinned the public Sectigo intermediate `src/certs/sectigo_dv_r36_intermediate.pem`, kept FULL
      verification — `verify_mode=CERT_REQUIRED`, no `verify=False`; proven default ctx rejects / pinned ctx
      accepts; cert valid to 2036; refresh note in the `_ctx` comment). **Sell2Wales** (`sell2wales.py`) built
      as a **resilient per-partition adapter** (month×noticeType partitions, bounded retry+backoff, structured
      error record, degrades not-drops) — **its upstream `/Notices` list API is currently broken (HTTP 500
      "nvarchar to float" on every query incl. their own doc example — confirmed their bug, not ours), so it
      ingests 0 live but recovers automatically when they fix it**. Shares the same pinned cert (same CA).
      **Partition-error surfacing shipped (session 21)** — `/api/search` now passes `incomplete` +
      `failed_partitions` through to the UI (raw errors stay server-side-only).
      F1 remainder / follow-ons: **Sell2Wales bulk-download fallback** (their official monthly JSON — an
      aspx-postback form, needs reverse-engineering) + **Find a Tender cross-publish recovery**; **extract a
      shared Proactis base** once a 3rd Proactis source lands (PCS+S2W are ~twins today — see the dedup note
      below); **eTendersNI** (different platform — Jaggaer, separate effort), G-Cloud. F2: multi-criteria
      search. **F5: ITT ingestion → auto-build the compliance matrix** (biggest; matrix schema is already
      per-bid dynamic, just no parser).

## G-series — GCA / Frameworks intelligence (user reqs, 2026-07-12)

- [x] **G1 — public data on OUR awarded contracts** (session 22) — SHIPPED. `src/own_awards.py` pulls FWF's
      OWN awards from the OCDS *award* packages (FTS + Contracts Finder), matched by **Companies House number**
      (GB-COH) so no false records. New `awards` sibling table + `upsert_award`/`list_awards`. CH number is app
      config (`own_org`), never hardcoded. `web/src/AwardsView.jsx` (`#awards`). Matcher live-verified on real
      FTS data (Softcat Plc). See `progress.md` session-22.
- [x] **G2 — Framework radar** (session 22) — SHIPPED. `src/frameworks_radar.py`: curated GCA agreements,
      lifecycle + recommendation computed LIVE against today (act/pursue/prepare/maintain/watch/skip).
      `web/src/FrameworksView.jsx` (`#frameworks`).
- [x] **G3 — "How to supply" reference** (session 22) — SHIPPED. `src/supply_reference.py` + `SupplyGuideView`
      (`#supply`): 5 routes to market + getting-started + help links, source-per-route + verified date.

**G-series follow-ons (open):**

- [x] **G1 clean award refresh** (session 23) — RESOLVED, but not as hoped. The 429s were the **VPN's shared
      exit IP** (a clean 930-notice probe ran with zero 429s once the VPN was off). BUT FWF's real NHS Barnsley
      win is **not in public OCDS under CH 11934102** (CH verified = "FUTURE WORK FORCE LIMITED"; no award found
      via Contracts Finder supplier search or web under either spelling — the notice likely named FWF without a
      CH id, was sub-threshold, or FWF was a subcontractor). The website search and OCDS feed read the same data,
      so more scanning won't change it. Full retrospective in `_session/award_refresh_log.md`.
- [x] **G1 manual award capture** (session 23) — SHIPPED. `POST /api/awards/manual` + `DELETE /api/awards/{id}`
      (Admin), `db.delete_award`; source `Internal record (manual)`, scheme `MANUAL` (never GB-COH), status
      `unverified` — honest provenance, untouched by the OCDS refresh. `AwardsView` "Record a known award" form +
      badge + remove control. NHS Barnsley record seeded into bids.db. `tests/test_manual_awards.py` (5).
- [ ] **G1 manual-award edit** (follow-on) — the form does create + delete; no in-place edit yet (delete+re-add).
      Refine the seeded NHS Barnsley record (title/date/value) when FWF's internal records surface.
- [x] **G1 "bids we lost" (user req)** — **PARTLY SOLVED (session 24), and the earlier premise was wrong.** It
      *is* recoverable from public data — not by searching for FWF (award notices name only the winner), but by
      finding the **buyer's award notice for a procurement we bid on** and reading off who won. New:
      `src/cf_bulk.py` (daily bulk OCDS CSVs from the CDP S3 feed — **47,797 notices in 12 min**, because the
      OCDS *APIs* have no text search and 429 under any parallelism) + `src/bid_outcomes.py` (folder → notice →
      verdict; **proposes, never asserts**) + `src/bid_manifest.json` + `tests/test_bid_outcomes.py` (7).
      **Confirmed loss: `22 UK BS (ACAS)` → Informed Solutions Ltd, £100k.** Probable: `25 Home Office PPPT` →
      Police Digital Services, £426,873 *(confirm)*. See `progress.md` session-24.
- [ ] **G1 — mine tender refs/titles from INSIDE the bid documents** ⭐ **NEXT ACTION.** 20 of 27 bids stall at
      "buyer seen, bid not identifiable": folder names (`18 DWP`) carry no subject words, and only 6 folders
      yield a tender ref from *filenames*. `ref` is the only tier that produced a clean result. The refs + real
      titles are inside `00 Bid Admin/FOR001 …xlsx` and `01 Customer Documents/` ITT files. **The feed is
      already cached (`src/.cache/`) — this needs no crawling.**
- [ ] **G1 — human confirm step → Stage 6 (Learn)** — `bid_outcomes.py` deliberately only proposes. Design the
      accept/reject UI that writes a confirmed verdict through outcome capture so the win-rate loop is fed.
      **Never auto-import** (see the `D365 Awards.xlsx` near-miss below).
- [ ] **G1 — devolved coverage gap** — the bulk feed is CF/CDP only. Scottish (Forestry and Land Scotland,
      Scottish Water) and Welsh (Cardiff Uni) bids may never appear. A `NO MATCH` there is a **coverage gap,
      not a loss**. Needs a PCS/Sell2Wales bulk equivalent before those can be resolved either way.
- [ ] **Market-intel ingest (NOT our awards)** — `D365 Awards.xlsx` and Tender Pipeline → *Contracts Ending* /
      *Upcoming Tenders* in the bid library are **awards to OTHER companies** + expiring incumbent contracts.
      Genuinely valuable (a re-compete pipeline), but they belong next to **Search/G2, labelled MARKET** —
      **never** in the `awards` table. An importer pointed at the filename would have written 10 false FWF
      records.
- [x] **G2 — FWF's real framework/DPS position** (session 24) — SHIPPED. `src/framework_positions.py` reads
      FWF's own framework folders from the bid-library export (LocalMirror seam; `available: false` without it)
      and annotates the radar. **The two disagreed:** radar said *"prepare"* for G-Cloud 15 while the library
      held **108 files + a drafted response** → now flagged `⚠ Already in flight`. **Six agreements FWF is
      working on were invisible to the radar** (Bluelight, DDaT-NSW, KCC, Spark RM6094, AI DPS RM6200,
      Automation Marketplace RM6173) → *"Also in flight"* section. Two empty scaffolds (MOD AI & Edge, RM6396)
      = intent, not work. `GET /api/frameworks/positions` + `tests/test_framework_positions.py` (8).
      **Honesty ceiling:** a folder proves WORK, never MEMBERSHIP — the ladder stops at `response_drafted`.
- [ ] **G2 — framework outcomes + true membership** — the export tops out at "response drafted": it cannot tell
      us a response was *submitted*, let alone accepted onto the framework. Real membership needs the Digital
      Marketplace listing (or G1 own-awards data). Same human-confirm step as the G1 outcomes item above.
- [ ] **G2 membership from G1 data** — corroborate the radar's `fwf_status` (member/not) from real own-awards
      data once populated, instead of the curated VERIFIED_FACTS claim (currently flagged "confirm").
- [ ] **Click the 3 new views in a live browser** — API + build verified only so far.

> **⚠️ CORRECTION (session 25):** the note below was a **false record**. The library credential
> *"Anti-Bribery & Modern Slavery Policies"* is a **tracker row with no owner, no date and no file** — the
> policy **does not exist**. A tracker row is an intention, not a policy. See the A3 gap list above.

## Harness follow-ups (from the 2026-07-10 harness-design review — `docs/harness_design/`)

- [x] **Canonical verification command** (2026-07-11) — `make check` (`scripts/check.sh`): backend
      pytest (deadline / CPV / qualification / preflight / auth-roles + app-construct = **29 tests**) →
      doc-state consistency guard → Vite build. `make check-fast` skips the build. `tests/` + `pytest.ini`
      + `requirements-dev.txt`. **Next extension:** add live-source tests behind an explicit flag (rung 4).
- [ ] **Fold the `skills/` B00–B07 chain into the app** — declare `src/` domain vocab canonical (done in
      CLAUDE.md), align skill enums/handoff schemas to it, route skill calculations through shared code.
      Resolve the duplicate `fwf-tender-sweep` skill-name collision (two `tender_sweep/` variants). Parked
      until the chain is actually folded in.

## Code-review remediation — ✅ FULLY CLEARED (Waves 0–6)

> Two reviews in [`docs/code_reviews/`](../docs/code_reviews/). **All waves are now done** — Waves 0–1
> (`0f35c70`), Wave 2 (session 14, `33980dd`), Waves 3–4 (session 15), Waves 5–6 (session 16). Several late
> items turned out to be false records (already implemented); full per-wave retrospectives + the false-record
> list live in `progress.md`. Nothing left to pick here.

## Surfaced / open (parallel tracks + polish)

- [ ] **Structural rot in `03 FWF Bids/`** (session 25) — three names for one folder (`02 Response
      Docs`/`Drafts`/`Documents` = 13/7/6), an index collision (`05` used twice: GCloud14 + Scottish Water), a
      botched duplicate tree in `11 Efficiency East Midlands`, a stray `.claude/` in `26 Office for Students`,
      two empty bid folders, `AI DPS RM62000` (typo for RM6200). **Any automation walking this structure
      silently misses a third of it.** Also: only **2 of 27** bids have anything in `07 Post Submission` —
      and both are **loss letters with full scoresheets** (Stage-6 data going to waste).
- [ ] **Pipedrive vs HubSpot** (session 25) — the bid-management handover names the CRM as **Pipedrive** (and
      **BidStats** as the discovery source); `CLAUDE.md`'s deferred roadmap says **HubSpot**. One is wrong —
      ask the user before building either integration.
- [ ] **Azure Phase C tail — live MSAL browser sign-in** — redirect round-trip needs a real dev-tenant app
      reg (no emulator). Supply `VITE_AAD_*` + `AAD_TENANT_ID`/`AAD_API_CLIENT_ID`, set `LOCAL_AUTH_BYPASS=0`,
      sign in, confirm the Bearer reaches the API and role-gating works.
- [ ] **Azure Phase D — hosting scaffold** per `docs/design/azure-target.md`. NOTE (2026-07-12): the **FWF
      Intern subscription is live** (verified `az account list`; TalentGrow blueprint RGs exist) — so the
      blocker is no longer access, it's the net-new **Bicep/IaC (A1)**. There is still **no resource group
      for this app** — creating one is a one-liner, but the real work is the IaC.
- [ ] **Azure OpenAI provider** — `src/llm.py` has a documented skeleton, not implemented; build when Azure
      access is provisioned (sequenced into Phase E).
- [ ] **Cross-source dedupe** — `(source, ocid)` dedupes within a source; cross-source matching (same notice
      on FTS + CF) not yet handled. Low priority given the value-band split.
- [ ] **AI-draft provenance persistence** — win-themes/evidence shown in the UI but not saved with the answer.
- [ ] **Triage ✕ semantics (session 18 follow-on)** — Triage board is now explicit-pull (`triage_selections`);
      the board's ✕ still `dismiss`es (reversible hide) rather than de-selecting. In a pull model these
      overlap — decide whether ✕ should remove the selection outright. Cosmetic/UX, scope with user.
- [ ] **Connector `to_record`/`run`/`main` dedup** (deferred from Wave 5; revisit — now 4 connectors) — FTS/CF
      are near-verbatim, and PCS/Sell2Wales are near-verbatim *with each other* (same Proactis platform);
      extract a shared base per family rather than one dedup across all four.
- [ ] **Parked polish** — CPV label badge on cards · lifecycle (`stale`/`closed`) badge on cards · widen CPV
      scope beyond IT/software (`TARGET_CPV` + `src/cpv_catalog.py`).
