# Progress — cold history

> Append-only, **most-recent-first**. One dated entry per session. The current hot state lives in
> [handover.md](handover.md); this is the retrospective trail behind it.

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
