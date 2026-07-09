# Progress — cold history

> Append-only, **most-recent-first**. One dated entry per session. The current hot state lives in
> [handover.md](handover.md); this is the retrospective trail behind it.

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
