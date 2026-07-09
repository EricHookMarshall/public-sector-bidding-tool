# Handover — hot state

> **Read first when resuming.** The one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> `_session/progress.md`; reach it on demand, it does not auto-load.

## Status

`2026-07-09` (session 3) — **Triage (B01) fully wired to real data AND AI pre-fill built.** Two
big pieces landed this session: (1) the FOR001 qualification/bid schema + real UI, and (2) a
provider-agnostic AI drafting layer with a live Settings screen. Both are **verified against a
real Anthropic key the user provided during this session** (in `discovery/.env`, gitignored,
untracked — confirmed).

## Active task

**Nothing blocking — pick the next stage or polish item.** Recommended next: **Plan (Stage 3)** —
`docs/design/data-model.md` §3 (`BidPlan`: pipeline position + FOR002 phase timeline) is fully
specified and Plan is flagged "highest-value missing piece" in `journey.js`. Alternative: keep
building out Complete (FOR006 compliance matrix) since the AI-drafting pattern (`llm.py` +
provider seam) now exists and could extend there.

Still parked, unchanged: **user still hasn't clicked through the running shell in a browser**
(3 sessions now — Triage + Settings are both new UI surfaces worth a real look before more stages
get wired on top).

## What shipped this session

**1. Triage schema + UI** (`db.py`, `qualification.py`, `api.py`, `TriageStage.jsx`)
- `qualification.py` (new): FWF's FOR001 scoring rig as domain logic — the £500/day ×
  complexity effort table (verified against the Reference-sheet totals exactly: Low
  9d/£4,500 … Medium 16.5d/£8,250 … High 24d/£12,000), the 10 Win-Qualification RAG criteria,
  pricing models, delivery roles.
- `db.py`: two new tables outside the connector path — `qualifications` (full FOR001 schema,
  JSON for delivery-team/RAG repeating groups) and `bids` (the spine, born on a Go). Migration
  verified against the live DB: 21 opportunities intact, idempotent on rerun.
- `api.py`: `GET /api/triage/reference`, `GET`/`PUT /api/opportunities/{id}/qualification`.
  Derived fields (economics, RAG summary) **recomputed server-side**, never trusted from the
  client; a Go promotes the opportunity into a Bid.
- `TriageStage.jsx`: real form (opportunity picker, seeded FOR001 fields, live economics, RAG
  scoring, decision buttons) replacing the mock. `SearchStage.jsx` got a "▲ Triage this →"
  handoff button (sessionStorage-based, survives hash nav).

**2. AI pre-fill for Triage** (`llm.py`, `triage_ai.py`, `config.py`, `SettingsView.jsx`)
- `llm.py` (new): the provider seam — `complete_json()` via forced tool/function calling (chosen
  because it maps 1:1 to Azure OpenAI's shape). `AnthropicProvider` built; `AzureOpenAIProvider`
  is a documented skeleton, deliberately deferred (client requirement, not yet provisioned).
  Default model **`claude-haiku-4-5`** (cost decision — this is a review-before-save drafting
  task, not deep reasoning; ~5× cheaper than Opus). `ping()` added for live connection testing.
- `triage_ai.py` (new): drafts the whole FOR001 from the opportunity notice + a concise FWF
  profile (Microsoft Practice, the EFS/PCG gap, G-Cloud 15 framework-position gate). Schema-
  constrained to FWF's real vocabulary (10 RAG keys, 5 complexity levels, 3 decisions). Draft is
  **never auto-saved** — human reviews and clicks the decision.
- `POST /api/opportunities/{id}/qualification/ai-draft` — returns `{draft, meta}`; 503 (not a
  crash) if no LLM configured, so manual Triage always works.
- **Settings screen** (`config.py`, new; `SettingsView.jsx`, new; routed at `#settings`, ⚙ button
  in `TopBar`): provider/model dropdowns with cost hints, an API-key field that is **write-only**
  (saved to gitignored `discovery/.env`, never returned to the browser — only "configured
  ••••1234"), Save, and a **Test connection** button that does a real 8-token round-trip.
  `config.py` writes are whitelisted to 3 env keys only.

**Verification — all real, not asserted:**
- DB migration + write-path smoke tests (qualification upsert, JSON round-trip, whitelist
  ignoring a bogus field, idempotent bid promotion) — cleaned up after, DB left at 21/0/0.
- API endpoints exercised via FastAPI `TestClient` and live `curl` against a running `uvicorn`:
  triage reference, seeded qualification, PUT→Go→bid creation (Med-High → 19.5d/£9,750, RAG
  2.4→"2 Med"), 404s, config validation (400 on bad model / unbuilt provider).
- Frontend: `npm run build` clean at every stage; both the running Vite dev server and the API
  were driven live via `curl`.
- **Live model calls, with the user's real key**: `POST /api/config/test` → `{"ok": true,
  "provider": "anthropic", "model": "claude-haiku-4-5", "reply": "ok"}`; a full AI draft on a
  real opportunity ("SUMIT Project…") produced a schema-valid FOR001 draft whose rationale
  correctly named FWF's EFS/framework gap — validates both the prompt and the Haiku cost call.
- **Secret handling checked, not assumed**: `discovery/.env` (containing the real key) confirmed
  git-ignored via `git check-ignore` and untracked via `git status` before this handover was written.

## Surfaced / parked threads

- **HubSpot integration** — future feature (pipeline ↔ CRM). Not scoped.
- **`StagePlaceholder.jsx`** — still dead code (superseded by per-stage screens); not deleted yet.
- **SharePoint data path for `LibraryItem`** — parked to the Complete stage, per data-model.md.
- **Azure OpenAI provider** — skeleton written in `llm.py`, not implemented. Client requirement;
  build when Azure access is provisioned.
- **Cross-source dedupe** — unchanged, low priority.

## Open decisions

1. **Storage for bid-lifecycle tables** — **resolved this session**: extended `bids.db` in place
   (per data-model.md's recommendation), not a separate store.
2. **Enum vs free-text** — followed the text-tolerant recommendation throughout (qualification
   fields are TEXT; complexity/decision/pricing_model constrained only in the UI/API layer).
3. **Which stage next** — Plan (3) is the recommended next per `journey.js` ("highest-value
   missing piece"); no hard blocker either way.

Settled (carried forward, unchanged): mockups-first method; six-stage journey shape; local app
now, Azure SPA later; library-provider seam for SharePoint; stack = FastAPI + SQLite + React/Vite;
shared bid record shape from `docs/design/data-model.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [_session/todo.md](todo.md).
2. Confirm DB state: `python3 db.py` → should show `Find a Tender: 19`, `Contracts Finder: 2`,
   `qualifications: 0`, `bids: 0` (unless a prior session's manual testing left rows — check).
3. Spin up the stack: `uvicorn api:app --reload --port 8000` + `cd web && npm run dev` →
   `http://localhost:5173`.
4. `discovery/.env` already holds a real Anthropic key (gitignored) — AI drafting and Settings
   → Test connection should work live without setup.

## Resume prompt

Paste this as the first message in a new session:

```text
Continuing work on the Public Sector Bidding API Platform PoC.

Read these on resume:
1. CLAUDE.md               (project spine — what we're building, stack, constraints, hard rules)
2. _session/handover.md    (hot state — current status, next step, open decisions)
3. _session/todo.md        (active queue)

Pull deeper context on demand: support/brief.md (full brief), cpv_codes.md (relevance scope),
find_tender_filter.py + contracts_finder_filter.py + db.py (connectors + DB layer),
qualification.py (FOR001 scoring rig), llm.py + triage_ai.py (AI pre-fill provider seam),
config.py (Settings screen backend), sources.py (source registry), regions.py (NUTS/ITL glossary),
cpv_catalog.py (CPV descriptions), refresh_clean.py (refresh + lifecycle-flag cleanup),
api.py (FastAPI JSON API), web/src/journey.js (6-stage metadata + scope content),
web/src/App.jsx (journey shell + #settings route), web/src/SettingsView.jsx (AI config screen),
web/src/stages/ (SearchStage + TriageStage = real; Plan/Complete/Manage/Learn = illustrative
mock screens), web/src/api.js, web/src/styles.css, _session/progress.md (cold dated history),
../docs/design/data-model.md (the shared bid record spec).

Search (Stage 1) and Triage (Stage 2, incl. AI pre-fill) are built and working. The app is the
6-stage journey shell; Plan/Complete/Manage/Learn remain labelled preview screens. At session
end, REPLACE the hot-state file, append a dated entry to _session/progress.md, and update
_session/todo.md. Don't commit/push unless asked.
```

## End-of-session checklist

When wrapping up:

1. **Kill any running services** (`pkill -f "uvicorn api:app"`, `pkill -f "vite"`).
2. **Replace** the Status line and Active task above with the new current state — don't append.
3. Append a dated entry to `_session/progress.md` (cold history): work done, decisions, open questions.
4. Update the `_session/todo.md` active queue (tick/re-order; completed items belong in `progress.md`).
