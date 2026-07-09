# Public Sector Bidding Tool

A set of tools to help someone — **even a novice** — navigate UK public sector
bidding end to end: **find** relevant opportunities, **triage** them, **plan**
which to bid and when, **complete** the bids (AI-assisted from a library of past
work), and **manage** them through to award and learning.

Built for **FWF (Future WorkForce UK Ltd)**, a UK subsidiary of Arobs Group. See
[`knowledge/`](knowledge/) for the business context and why this exists.

> **Status:** the app is a working 6-stage journey shell. Search, Triage (with
> AI pre-fill) and Plan are built and wired to live data; Complete, Manage and
> Learn are labelled preview screens. The bid-lifecycle skills (`skills/`) are
> designed but not yet grounded to live data.

---

## The journey (and where each stage stands)

```
1. SEARCH  →  2. TRIAGE  →  3. PLAN  →  4. COMPLETE  →  5. MANAGE  →  6. LEARN
```

| Stage | What the user does | Lives in | State |
|---|---|---|---|
| **1. Search** | Find relevant opportunities across sources | [`src/`](src/) + [`web/`](web/) | ✅ Live — Find a Tender + Contracts Finder |
| **2. Triage** | Bid / no-bid with clear reasons | [`src/`](src/) + [`web/`](web/) | ✅ Live — real FOR001 form + AI pre-fill |
| **3. Plan** | Which bids, when, with what capacity | [`src/`](src/) + [`web/`](web/) | ✅ Live — pipeline board + capacity + FOR002 timeline |
| **4. Complete** | Matrix → retrieve → draft → review → preflight | [`skills/`](skills/) B02–B05 | 🟡 Preview screen; needs live doc I/O + SharePoint |
| **5. Manage** | Clarifications, deadlines, sign-off | [`skills/`](skills/) B06 | 🟡 Preview screen; needs portal/mailbox link |
| **6. Learn** | Feed outcomes back into the library | [`skills/`](skills/) B07 | 🟡 Preview screen; depends on stage 4 |

The **gap** this project still closes: the AI pre-fill for Complete has no live
**SharePoint** library behind it yet, and the `skills/` B00–B07 chain isn't yet
grounded to the app's live data.

---

## Repository layout

```
.
├── src/           # App backend: FastAPI + SQLite. Connectors (Find a Tender,
│   │              #   Contracts Finder) → normalise → bids.db; Triage (FOR001)
│   │              #   + Plan (FOR002) logic + AI pre-fill seam.
│   ├── bids.db    #   Local SQLite store (gitignored, rebuildable)
│   └── .env       #   Local secrets — Anthropic key etc. (gitignored)
├── web/           # App frontend: React/Vite — the 6-stage journey shell
├── support/       # The PoC brief + the API catalogue the record shape came from
├── skills/        # Bid-lifecycle skill chain B00–B07 (Claude skills + helper scripts)
│   ├── b00…b07/   #   One folder per skill (SKILL.md + scripts/ + references/)
│   ├── INDEX.md · STANDARD.md · SHAREPOINT.md  #   Chain map, writing standard, 3-library architecture
│   └── tender_sweep/  #   Standalone sweep skill (me / team variants)
├── knowledge/     # The "why": FWF situation + UK procurement reference
│   ├── 01-current-position.md      # G-Cloud 15 disregard, EFS gap, handover state
│   ├── 02-recovery-plan.md         # 3-horizon recovery plan (Arobs PCG, alt frameworks)
│   ├── 03-knowledge-base.md        # UK procurement primer (PA23, G-Cloud, EFS, PCG)
│   ├── 04-skills-review-2026-07-08.md  # Review that shaped the B00–B07 skill design
│   └── VERIFIED_FACTS.md           # ✅ Live-verified facts + sources (re-check before use)
├── docs/          # Design docs (architecture, data-model, journey mockups)
├── CLAUDE.md      # The working spine (read this first)
└── README.md      # This file — the outward-facing spine
```

## Running the app

```bash
python3 src/db.py                                   # create/inspect src/bids.db
python3 src/find_tender_filter.py 120               # fetch → normalise → upsert
uvicorn api:app --app-dir src --reload --port 8000  # JSON API (src/ on the path)
cd web && npm install && npm run dev                # UI at http://localhost:5173
```

`src/bids.db`, `src/.env` and `node_modules/` are gitignored (rebuildable / secret).

---

## Context, in one paragraph

FWF's G-Cloud 15 bid was **disregarded at the financial-standing gate** (missing
accounts + a missed clarification) — an administrative failure, not a quality
one. G-Cloud 14 expires **28 Oct 2026**, leaving a ~16-month gap before the
G-Cloud 15 re-entry window (~Mar 2028). The structural fix is a standing **Arobs
Parent Company Guarantee**. The lesson — *a missed deadline kills a bid* — is why
stages 3 and 5 (planning + deadline management) matter as much as the drafting.
Full detail and verified facts in [`knowledge/`](knowledge/).

## Roadmap

- **Phase 0 — Consolidate & verify** *(in progress)*: one repo, clean structure,
  facts verified (`knowledge/VERIFIED_FACTS.md`).
- **Phase 1 — Search → triage**: shared record; promote an opportunity into a
  qualified bid/no-bid decision (wire discovery ↔ B01).
- **Phase 2 — Planning layer**: bid pipeline + calendar (deadline, owner, effort,
  win-probability, capacity, alerts). The highest-value missing piece.
- **Phase 3 — SharePoint + AI pre-fill**: stand up the 3-library bid store (MS
  Graph) and run B00/B03/B04. Biggest external dependency.
- **Phase 4 — Manage & learn**: preflight gate, clarification register, outcome loop.

## Open decisions

1. **Product form** — grow the discovery UI into the whole journey, or keep
   discovery separate and run the bid workspace via skills + SharePoint?
2. **SharePoint timing** — Phase 3 needs real MS Graph credentials (this
   environment currently has Google Drive, not SharePoint).
3. **Sequencing** — chosen: **breadth first** (thin end-to-end), consolidate & verify first.
