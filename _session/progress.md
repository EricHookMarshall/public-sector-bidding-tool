# Progress — cold history

> Append-only, **most-recent-first**. One dated entry per session. The current hot state lives in
> [handover.md](handover.md); this is the retrospective trail behind it.

## 2026-07-09 (session 3) — Triage (B01) live + AI pre-fill + Settings screen

**Context.** Continued straight from session 2's Active task ("wire Triage for real"), then the
user asked to add AI pre-fill for the Triage form — flagged as the biggest time-saver in the whole
tool, with an explicit heads-up that the provider would need to move from Anthropic to Azure
OpenAI later, so the design had to plan for that swap up front. After it shipped, the user flagged
cost as a factor and asked to move off the default (more expensive) model, then asked for a
Settings screen to manage the AI config day-to-day.

**Work done.** Full file-level detail lives in `discovery/_session/progress.md` (this session's
entry there). Summary: (1) Triage — FWF's real FOR001 qualification form (go/no-go RAG scoring +
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
flags it as the highest-value missing piece. See `discovery/_session/handover.md` for the
file-level starting point.

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
  `discovery/db.py`. See `discovery/_session/progress.md` (2026-07-09, session 2) for the file-level
  detail and verification.
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

**Work done.** All under `discovery/web/` (full file-level detail in `discovery/_session/progress.md`):
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
