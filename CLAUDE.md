# CLAUDE.md — Public Sector Bidding Tool

Project spine. Read this first; it stays accurate as the repo grows. The
outward-facing overview is [README.md](README.md); this file is the working
spine for anyone (human or agent) doing the work.

## What we're building

A set of tools to help someone — **even a novice** — run the full UK public
sector bidding journey:

```
1. SEARCH → 2. TRIAGE → 3. PLAN → 4. COMPLETE → 5. MANAGE → 6. LEARN
```

Find relevant opportunities, triage them (bid/no-bid), plan which to bid and
when (capacity + deadlines), complete them (AI-assisted from a library of past
bids), manage them through clarifications to award, and learn from outcomes.
Built for **FWF (Future WorkForce UK Ltd)**, a UK subsidiary of Arobs Group.
The *why* — FWF's G-Cloud 15 disregard, the EFS/PCG gap, the framework
timeline — lives in [`knowledge/`](knowledge/).

## Current phase: the journey app is live through Stage 3

The repo is one connected git repo (remote:
`github.com/EricHookMarshall/public-sector-bidding-tool`) with a clean structure
and live-verified facts. The app is the **6-stage journey shell**; **Search
(1), Triage (2, incl. AI pre-fill) and Plan (3)** are built, wired to `bids.db`,
and live-verified. **Complete (4), Manage (5) and Learn (6)** are still labelled
preview screens. The `skills/` B00–B07 chain is designed but not yet grounded to
live data. Roadmap and status live in
[`_session/handover.md`](_session/handover.md) and [README.md](README.md).

## Repo map

```
src/         The app backend. FastAPI + SQLite. Connectors (Find a Tender +
             Contracts Finder) → normalise → bids.db; Triage (FOR001) + Plan
             (FOR002) domain logic + AI pre-fill seam. bids.db + .env live here
             (both resolved relative to the code, so they travel with it).
web/         The app frontend. React/Vite — the 6-stage journey shell + per-stage
             screens (Search/Triage/Plan real; Complete/Manage/Learn preview).
support/     The PoC brief + the API catalogue the record shape was drawn from.
skills/      B00–B07 bid-lifecycle skill chain (Claude skills + helper scripts).
             Designed; targets a 3-library SharePoint bid store (not yet stood up).
knowledge/   The "why" + reference. FWF situation + UK procurement primer.
             VERIFIED_FACTS.md = live-verified facts (re-check before relying on them).
docs/        Design docs (architecture, data-model, journey mockups).
_session/    Working discipline — the project's single cross-session memory.
.claude/     Project skills: /resume-prompt, /end-session.
README.md    Outward-facing spine (the journey + where each stage stands).
CLAUDE.md    This file — the working spine.
```

The backend is a flat set of modules under `src/` imported by bare name
(`import db`, `import bidplan as P`). `bids.db` and `.env` are resolved relative
to the module files, so they live in `src/` and move with the code.

## The record shape (src/)

Every source normalises into the fields owned by [`src/db.py`](src/db.py)
(`COMMON_FIELDS`, ~18 fields: `source`, `ocid`, `title`, `buyer_name`,
`cpv_codes`, `region`, `value_min/max`, `deadline_date`, `status`, `url`,
`raw_json`, …). The upsert/dedupe key is **`(source, ocid)`** — re-running a
connector updates rows instead of duplicating. `raw_json` keeps the source
payload for re-mapping. Relevance scope is IT/software CPV codes
([`src/cpv_codes.md`](src/cpv_codes.md)); connectors strip trailing zeros so a
group code matches its sub-codes. Triage adds `qualifications`/`bids` (FOR001),
Plan adds `bid_plans` (FOR002) — same DB, same patterns.

## How to run

```bash
python3 src/db.py                                 # create/inspect src/bids.db
python3 src/find_tender_filter.py 120             # fetch → normalise → upsert
uvicorn api:app --app-dir src --reload --port 8000  # JSON API (src/ on the path)
cd web && npm install && npm run dev              # UI at http://localhost:5173
```

`src/bids.db`, `src/.env` and `node_modules/` are gitignored (rebuildable /
secret). Kill services when done: `pkill -f "uvicorn api:app"; pkill -f vite`.

## Ways of working (delivery discipline)

- **The `_session/` triad is the memory.** Three files track work across sessions:
  - [`_session/handover.md`](_session/handover.md) — **hot state**: one page, current status + the single next action. **Replace** it, don't append.
  - [`_session/progress.md`](_session/progress.md) — **cold history**: dated entries, most-recent-first. **Append** one per session.
  - [`_session/todo.md`](_session/todo.md) — the **active queue**.
  Use `/resume-prompt` to start a session and `/end-session` to close one.
- **Honest verification.** Quote real results. If something failed, was skipped, or wasn't run, say so — never claim green you didn't observe. This project exists because an admin failure (a missed clarification) killed a real bid; accuracy is the whole point.
- **Check for false records.** If a `_session/` entry or a doc claims something exists, verify before carrying it forward.
- **Facts decay — verify, don't hardcode.** Procurement dates, EFS thresholds, framework statuses and RM codes move. Re-check against `knowledge/VERIFIED_FACTS.md` and live sources before relying on them; prefer wiring live checks into the tool over baking numbers into code. (Precedent: RM6263 was already expired when the recovery plan still listed it — see VERIFIED_FACTS.md.)
- **Every dependency earns its place.** Keep it lean, single-responsibility, and comment the *why*, not the *what*. Match the surrounding code's style.
- **Out of scope is explicit.** When something is deferred, say so and where it goes, rather than half-building it.

## Hard rules

- **No secrets in git.** SharePoint / MS Graph credentials, API keys, and portal
  logins live in `.env` / local config only (git-ignored) — never in chat, code, or docs.
- **No client-confidential bid content committed** to this repo. The bid library
  (past submissions, evidence) lives in SharePoint, not here.
- **PoC boundaries** still hold: local-only (no cloud infra, auth, or multi-user),
  keep the DB lean (store only open, relevant opportunities), always record
  provenance, and normalise every source before storing — never let a raw source
  shape leak into the DB or UI.
- **SharePoint isn't available in this environment yet** (only a Google Drive
  connector is). Anything depending on the live bid library (Phase 3, B00/B03/B04)
  is blocked until real MS Graph access is set up outside the session — don't fake it.

## Roadmap

- **Phase 0 — Consolidate & verify** ✅ one repo, clean structure, facts verified.
- **Phase 1 — Search → triage**: shared record; promote an opportunity into a bid/no-bid decision (wire discovery ↔ skills B01).
- **Phase 2 — Planning layer**: bid pipeline + calendar (deadline, owner, effort, win-probability, capacity, alerts). Highest-value missing piece.
- **Phase 3 — SharePoint + AI pre-fill**: stand up the 3-library bid store (MS Graph); run B00/B03/B04. Biggest external dependency.
- **Phase 4 — Manage & learn**: preflight gate, clarification register, outcome loop.
