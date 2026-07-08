# Progress — cold history

> Append-only, **most-recent-first**. One dated entry per session. The current hot state lives in
> [handover.md](handover.md); this is the retrospective trail behind it.

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
