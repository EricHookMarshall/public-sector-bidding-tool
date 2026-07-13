# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-13` (session 25) — **A-series standard-answer bank shipped. Then the deep read of the library found
three things that outrank it.**

Full retrospective in [`progress.md`](progress.md) session-25. Two docs carry the detail:
[`docs/standard-answers.md`](../docs/standard-answers.md) (the store) and
[`docs/bid-library-deep-review.md`](../docs/bid-library-deep-review.md) (all 504 files, 812 MB, read in 4 batches).

**Built — the answer bank (A-series).** The questions every bid asks that need **no reasoning**
("do you have a Modern Slavery policy? attach it"). A **lookup, never a generator**: it answers from record
with provenance, or it **refuses**. `src/answers.py` + `standard_answers` table + 4 endpoints +
`tests/test_answers.py` (24). Seeds from the real library through the `LocalMirror` seam on **every** startup.
**33 answers: 16 ready · 7 gap · 4 conflict · 4 confirm-per-bid · 2 wrong-entity.**
**`make check` green: 142 backend tests** + doc-consistency + vite build.

**The three findings that matter more than the code:**

1. **🔴 The ISO certificates belong to a different company.** ISO 9001 *and* ISO 27001 are issued to **Future
   Work Force SRL — the ROMANIAN sister company** (Cluj-Napoca; the 9001 even annotates the address *"no
   activity"*) — **not** to Future Work Force **Limited** (UK, CH 11934102), which is what bids. Both are
   **also expired**. The files are named `FUTURE WORK FORCE - ISO 9001.pdf` and sit in FWF's own credentials
   folder, so they read as *ours* to every automated check and every hurried human. **Attaching one to a UK
   selection question is a misrepresentation.** Truth: **FWF Ltd holds no ISO certification of its own.**
   For 27001 there *is* a real mitigation — BV letter `L/BUH/06.11.2025/423/BCT` confirms **Arobs Group,
   explicitly naming "Future Work Force"**, passed the **ISO 27001:2022** transition audit (Oct 2025) — but
   that is **group** certification evidenced by a **letter**. Say exactly that; never attach the lapsed SRL cert.
2. **🔴 CCS MI returns look unfiled.** The portal tracker says *"Must submit MI **monthly**, AI DPS RM6200,
   SPARK DPS RM6094"* — but `07 CCS MI Reports/` holds **only a blank template**. No returns, any month, any
   agreement. Monthly MI (**including nil returns**) is mandatory; non-submission attracts charges and can
   **suspend an appointment**. Verify whether they're filed elsewhere.
3. **🟠 Portal passwords in cleartext**, **reused across portals**, on a **departed employee's** accounts.
   Known since session 24 — but they need **rotating**, not just re-filing.

**Two earlier conclusions were WRONG, and are now corrected:**

- **The insurance has NOT lapsed.** Both the GCA review and my own first cut said cover expired 27/05/2026.
  The **certificates** show policy `.../11` running **28/05/2026 → 27/05/2027** (EL £5m, Public *and Products*
  Liability £10m, PI £2m, Cyber £1m). `Insurance Tracker.xlsx` was never updated at renewal. Reading it made
  the bank raise a **false alarm** — as damaging as a missed expiry. **Fix: the bank now reads the
  certificates; the tracker is only a fallback.** A document issued by the insurer beats a spreadsheet row
  typed by someone who has since left. Knock-on: **Product Liability is not a gap** — same £10m certificate.
- **Cyber Essentials *has* lapsed** (correct entity, but certified 06/06/2025 → due 06/06/2026).

**And the founding failure, in files:** `G Cloud 15/03 Pricing/FVRA/AROBS/` contains the **Arobs annual reports
and the completed FVRA Gold workbook**. The parent-company financials that would have answered the FVRA **were
prepared and sitting in the folder** — they just never got submitted, and the clarification went unanswered.

## Active task

**Escalate the three findings above — they are business-urgent and cannot be fixed in-session.** Nothing in the
backlog outranks a misrepresentation risk or a possible framework suspension.

Then, in the code: **build the Answers UI** — the bank is **API-only** today
(`/api/answers/board` · `/lookup?q=` · `PUT /api/answers/{key}` · `POST /api/answers/sync-from-library`).
A Stage-4 panel that answers a buyer's question in their own words, shows the file to attach, and **refuses
loudly** on `wrong_entity` / `conflict` / `gap` is the obvious next step.

Carried from session 24 (both still open, both still cheap): fold the GCA portal facts into
`framework_positions` as an authoritative overlay; mine tender refs from **inside** the bid documents.

## Blockers / prerequisites

- **The bulk feed is CF/CDP only — devolved notices are absent.** Scottish (Forestry and Land Scotland,
  Scottish Water) and Welsh (Cardiff Uni) bids may never appear in it. A `NO MATCH` for those buyers is a
  **coverage gap, not a loss** — never record it as one.
- **⚠️ Plaintext portal passwords** — `04 Portal Registrations/Portal Registration Tracker.xlsx`. Gitignored,
  so nothing reached git. **Session 25 raised the severity: they are REUSED across portals and belong to a
  departed employee's accounts — they need ROTATING, not just re-filing.** Not a code fix.
- **The ISO certs cannot be used** (wrong legal entity + expired) — see Status. Any bid answering "are you ISO
  certified?" must go via the Arobs **group** position, stated as such. Blocks nothing in code; blocks bids.
- **Insurance/CE dates are read from the CERTIFICATES, not `Insurance Tracker.xlsx`** — the tracker is stale
  and will mislead you. If a cert is reissued, re-check `answers.py` `WRONG_ENTITY_EVIDENCE` (image scans, so
  no parser can see the entity).
- **Sell2Wales upstream is down**, not us — re-check periodically; no code fix possible on our side.
- **Empty *bid* pipeline is expected** (session-13 cleanse). Compliance register separate, seeded (19).
- **Live `GraphSharePoint`/`SharePointStore`** — no MS Graph here. **Azure:** subscription live, no resource
  group; Bicep/IaC (A1) is the real gap. Neither blocks the Active task.

## Open decisions

1. **How a confirmed outcome gets recorded.** `bid_outcomes.py` only proposes. Does an accepted verdict write
   to `bids.db` via Stage 6 (Learn) outcome capture, or via the G1 manual-award path (session 23)? Both exist;
   pick one so there's a single way in. **Never auto-import** — see the `D365 Awards.xlsx` near-miss.
2. **Cert pin maintenance** — `src/certs/sectigo_dv_r36_intermediate.pem` is shared by PCS + Sell2Wales;
   refresh instructions live in the module docstrings + `src/certs/README.md` if either site changes CA.
3. **`KNOWN_CONFLICTS` / `WRONG_ENTITY_EVIDENCE` in `answers.py` are dated snapshots** (in the manner of
   `VERIFIED_FACTS.md`). **Delete an entry once reconciled** — a stale conflict flag is its own kind of lie.
4. **Pipedrive vs HubSpot.** The bid-management handover names the CRM as **Pipedrive** (and BidStats as the
   discovery source). `CLAUDE.md`'s deferred roadmap says **HubSpot**. One is wrong — ask the user.
5. Carried from session 19 (untouched): compliance write-gating, file-content expiry extraction —
   see `progress.md` session-19 entry.

## Auth quick-reference

Unchanged this session. Local dev default `LOCAL_AUTH_BYPASS=1`. Full config: `src/.env.example` +
`web/.env.example`.

## Start-of-session checklist

1. Read [`state.yaml`](state.yaml), [`CLAUDE.md`](../CLAUDE.md), this file, and [`todo.md`](todo.md).
2. Confirm DB: `python3 src/db.py` → `opportunities: 24` (unchanged this session). The `standard_answers`
   bank (33) re-seeds itself from the library on every server start — no action needed.
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev`. Search now
   default-hides closed opps (toggle in the Filters panel) and shows a partial-results warning if a source
   (e.g. Sell2Wales) returns `incomplete`.
4. `git status` for the true commit state (this doc doesn't duplicate it).

## End-of-session checklist

1. Kill services: `pkill -f "uvicorn api:app"; pkill -f vite`.
2. Update [`state.yaml`](state.yaml) first, then **replace** the Status + Active task above (don't append).
3. **Prepend** a dated entry to [`progress.md`](progress.md) (most-recent-first).
4. Update the [`todo.md`](todo.md) active queue; commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
