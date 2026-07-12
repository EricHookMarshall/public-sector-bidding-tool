# TODO — active queue

> **Unfinished work only.** Completed items are cold history — see [`progress.md`](progress.md)
> (most-recent-first, full dated retrospective per session). Everything through **session 13 is
> committed** (`9c31fa8`). When an item ships, note it in `progress.md` and delete it here.

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
- [ ] **G1 "bids we lost" (user req)** — NOT in public OCDS (award notices name only the winner). Source lost
      bids from the app's internal **Learn/outcome capture (Stage 6) + bid library**, not the connector. (Same
      internal-sourcing pattern the manual-award capture above now establishes.)
- [ ] **G2 membership from G1 data** — corroborate the radar's `fwf_status` (member/not) from real own-awards
      data once populated, instead of the curated VERIFIED_FACTS claim (currently flagged "confirm").
- [ ] **Click the 3 new views in a live browser** — API + build verified only so far.

> **Noted (already built — no action):** Modern Slavery is already a Manage pre-flight item + a library
> credential ("Anti-Bribery & Modern Slavery Policies") — don't re-add.

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
