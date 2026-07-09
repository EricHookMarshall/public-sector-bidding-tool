# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-09` (session 8) — **No app code changed this session.** The journey remains feature-complete
(all six stages, session 7). This session was pure forward planning: the user asked what's needed to
move the tool to Azure + a hosted SPA. Produced a design doc, `docs/design/azure-target.md` (not
started, nothing provisioned) — target is to **clone TalentGrow's** (a sibling FWF app) proven Azure
blueprint: SWA (Free) + Azure Functions (Flex Consumption, Python) + Azure SQL free serverless (AAD-
only) + Managed Identity everywhere, no Key Vault. Locked decisions: Entra ID sign-in (MSAL), mirror
TalentGrow's build pattern, cheapest/free DB, Managed Identity + federated cred for SharePoint/Graph.

Prior status (session 7), unchanged: **All six journey stages are built, wired to `bids.db`, and
live-verified.** Complete (Stage 4) shipped via the `LocalMirror` provider seam over the real gitignored
bid export — so the full **Search → Triage → Plan → Complete → Manage → Learn** loop is real.

Complete = the FOR006 tender-response compliance matrix + **AI pre-fill grounded in FWF's real bid
library**. New backend: `src/library.py` (the LocalMirror provider — reads the real
`Bid Library Tracker.xlsx`, extracts expiry from free-text Notes, retrieval + evidence ledger),
`src/response.py` (FOR006 matrix rig + live word-count compliance), `src/complete_ai.py` (retrieval-
grounded answer drafting), the `bid_responses` table, `/api/complete/*` + `/api/library` +
`GET`/`PUT /api/bids/{id}/responses` + index-based AI-draft, a real matrix→workspace UI replacing the
mock `CompleteStage.jsx`, and `src/seed_complete_demo.py`.

Verified over **real HTTP**: `/api/complete/board` 200 (library provider available, **42 items**);
`/api/library` evidence ledger surfaces the real **expired** "ISO Certifications" (2025-10-31, parsed
from Notes); GET matrix auto-seeds 8 real questions from the FOR006 master; a PUT with an 800-word
answer flags `over_limit` server-side (word count recomputed, not trusted); the **AI draft is
retrieval-grounded** (680/666 words within the 750 limit, cites real library items, names win themes,
honestly flags gaps — `claude-haiku-4-5` via the live `.env` key); out-of-range index → **404**.
`npm run build` clean (37 modules). DB: `bid_responses: 1` (RTPI seeded), all other stages intact.

## Active task

**Nothing blocking — the journey is feature-complete; Azure migration is now designed but not started.**
Sensible next moves (user's call), roughly in priority order:

1. **Start the Azure migration at Phase B (DB portability)** per `docs/design/azure-target.md` — port
   `src/db.py` off raw `sqlite3` to a SQLAlchemy Core dual-mode shim (SQLite local / Azure SQL cloud).
   This and Phase C (auth) are the substantive code work and can be built + verified locally, no Azure
   subscription needed yet.
2. **User browser walk of Complete (+ Learn)** (still open from session 7) — these were verified
   server-side only. Spin up `uvicorn api:app --app-dir src --port 8000` + `cd web && npm run dev` →
   localhost:5173, open `#complete` and `#learn`.
3. **Commit the outstanding milestone.** Nothing has been committed since session 6 — Learn + Complete
   (session 7) are still uncommitted. The user hasn't asked to commit; offer it.
4. **Polish / harden Complete** — e.g. persist AI-draft provenance (win themes/evidence) with the
   answer, richer retrieval, or a cross-bid completion view. All optional.
5. **Deferred externals** — Azure OpenAI provider; live `GraphSharePoint` (drops in behind the
   `library.py` seam when MS Graph is provisioned); HubSpot.

## What shipped

**Azure/SPA target design — session 8** (`docs/design/azure-target.md` new) — no code; a design doc
answering "what does Azure + a hosted SPA need?" Grounded in the existing seams (`llm.py`, `library.py`,
`sources.py`) and in **TalentGrow** (sibling FWF app, same Entra tenant/RG family), whose Bicep is
**already live and deployed in dev** — treat it as a proven blueprint, not a draft (its own
`infra/README.md` has a stale "not yet validated" note from authoring time; ignore it). Gap checklist,
phased path (A design → B DB portability → C auth → D hosting scaffold → E Azure-native providers →
F provision/go-live), and file-level touch list captured in the doc. Also settled this session (all in
the doc, web-verified): **cheapest data** = Azure SQL free offer (£0; 10 free DBs/sub) + **docs stay in
SharePoint, no Blob**; **AI retrieval** without a paid vector store — three seam-swappable options
(A: M365 Copilot Retrieval API over the existing Copilot index — spike first; B: native `VECTOR` in the
free Azure SQL DB, GA Jun-2025; C: cached-text + Full-Text baseline); and a **local emulation** strategy
(Tier 1 emulate: SQL Server 2025 container + Azurite + `func start`; Tier 2 use the seams — Entra/Graph/
Copilot have no emulator). Corrected: Azure SQL **Edge retired 30-Sep-2025** — use the SQL Server 2025
container for local DB parity.

**Complete (Stage 4) — session 7** (`src/library.py` new, `src/response.py` new, `src/complete_ai.py`
new, `src/db.py`, `src/api.py`, `web/src/api.js`, `web/src/stages/CompleteStage.jsx` (was a mock),
`web/src/journey.js`, `web/src/styles.css`, `src/seed_complete_demo.py` new) — the `LocalMirror`
library provider (architecture.md's seam; reads the real gitignored export, extracts expiry from
Notes, keyword retrieval + evidence ledger, `master_template()` for the question set), the FOR006
matrix rig (statuses, live word-count gate, completion summary), retrieval-grounded AI drafting, the
`bid_responses` table, the Complete endpoints (board / library browse / matrix GET-PUT / index-based
AI-draft), and a real matrix→workspace UI. Honest boundary: if the export is absent the UI says
"library not connected" — it never fakes content; `GraphSharePoint` swaps in behind the same seam.

**Learn (Stage 6) — session 7** (`src/outcome.py` new, `bid_outcomes` table, `/api/learn/*`) — B07
outcome + win-rate + promote/refresh/retire library-feedback loop (human-approved, no library write
faked). Full detail in [progress.md](progress.md) session 7.

**Manage (Stage 5) — session 6** (`src/clarification.py`, `bid_manage` table) — FOR003 CQLOG +
pre-flight gate (409 on a blocked submit).

## Surfaced / parked threads

- **`web/src/stages/MockStage.jsx` + `StagePlaceholder.jsx` are now dead code** — every stage is real,
  so nothing imports them (the build dropped from 39→37 modules). Safe to delete.
- **AI-draft provenance isn't persisted** — the win-themes/evidence/gaps meta shows in the UI after a
  draft but isn't saved with the answer (only `supplier_response` persists). Fine for the PoC; a
  natural enhancement.
- **`question_ref` repeats across lots** in the FOR006 master (Lot2/Q1, Lot3/Q1) — handled by
  identifying matrix rows by index, not qref. Don't reintroduce qref as a key.
- **`GraphSharePoint` provider** — not built (no MS Graph here). Slots into `library.get_provider()`
  behind the same interface; set `LIBRARY_PROVIDER` + `BID_LIBRARY_ROOT` to point elsewhere.
- **Azure OpenAI provider** — skeleton in `src/llm.py`, not implemented.
- **Team capacity default (25 days, `src/bidplan.py`)** — placeholder, not a real FWF number.
- **Google Drive MCP connector** is authenticated here (SharePoint/MS Graph is not) — an alternative
  `LocalMirror` feed if the local folder export isn't the chosen source.
- **Azure migration is designed, not started** — `docs/design/azure-target.md`. Biggest lift: `db.py`
  off raw `sqlite3`. No auth exists on the API today at all — that's the #1 gap the design closes.

## Open decisions

1. **What next** — start Azure Phase B, browser-review Complete/Learn, commit the milestone, or polish.
   Not decided.
2. **Commit cadence** — Learn + Complete are uncommitted; the user commits on request only.
3. **AI-draft provenance persistence** (see threads) — save the evidence/win-themes with the answer?
4. **Azure OpenAI / GraphSharePoint timing** — build when the respective access is provisioned (now
   sequenced into Azure migration Phase E, see `docs/design/azure-target.md`).

Settled this session: **Azure/SPA target design** — clone TalentGrow's blueprint (SWA plus Functions
Flex plus Azure SQL free plus Managed Identity everywhere, no Key Vault); Entra ID/MSAL for sign-in;
Azure SQL free serverless for DB.

Settled session 7, unchanged: **Complete (Stage 4) built via LocalMirror** — the journey is
feature-complete, all 6 stages real; **Learn (Stage 6) built**; **browser review of stages 1–3/5 done,
looks fine**.

Settled earlier, unchanged: Manage (Stage 5) FOR003 + pre-flight gate; flat repo structure; Plan
(Stage 3) real; Triage (B01) + AI + Settings; mockups-first method; six-stage journey shape + visual
style approved; local app now, Azure SPA later; library-provider seam; AI drives task completion;
stack = FastAPI + SQLite + React/Vite; shared bid record from `docs/design/data-model.md`. Facts
verified in `knowledge/VERIFIED_FACTS.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. Confirm DB state: `python3 src/db.py` → `opportunities: 21`, `qualifications: 3`, `bids: 3`,
   `bid_plans: 3`, `bid_manage: 3`, `bid_responses: 1`, `bid_outcomes: 2` (the demo seed) — unless a
   prior session's testing left different rows; check before assuming.
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev` →
   `http://localhost:5173`. Demo data: `python3 src/seed_plan_demo.py` (Plan bids) +
   `seed_manage_demo.py` (Manage) + `seed_complete_demo.py` (Complete matrix) + `seed_learn_demo.py`
   (Learn outcomes); each takes `--clear`.
4. Complete's library reads the real gitignored export at `knowledge/SharePoint Folder/Bids/` — if
   absent (e.g. fresh clone), the Complete UI shows "library not connected" and AI-draft is disabled;
   that's honest, not a bug. `src/.env` holds a real Anthropic key for AI drafting.
5. If picking up the Azure migration, read `docs/design/azure-target.md` first — it's the plan of
   record for that thread.

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`).
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
