# Public Sector Bidding Tool

A set of tools to help someone — **even a novice** — navigate UK public sector
bidding end to end: **find** relevant opportunities, **triage** them, **plan**
which to bid and when, **complete** the bids (AI-assisted from a library of past
work), and **manage** them through to award and learning.

Built for **FWF (Future WorkForce UK Ltd)**, a UK subsidiary of Arobs Group. See
[`knowledge/`](knowledge/) for the business context and why this exists.

> **Status:** early consolidation. The discovery engine works; the bid-lifecycle
> skills are designed but not yet grounded to live data. This repo brings the
> pieces into one place and defines the path between them.

---

## The journey (and where each stage stands)

```
1. SEARCH  →  2. TRIAGE  →  3. PLAN  →  4. COMPLETE  →  5. MANAGE  →  6. LEARN
```

| Stage | What the user does | Lives in | State |
|---|---|---|---|
| **1. Search** | Find relevant opportunities across sources | [`discovery/`](discovery/) | ✅ Working — Find a Tender + Contracts Finder |
| **2. Triage** | Bid / no-bid with clear reasons | [`skills/`](skills/) B01 | 🟡 Designed, not wired to discovery |
| **3. Plan** | Which bids, when, with what capacity | — | 🔴 Missing — the portfolio/calendar layer |
| **4. Complete** | Matrix → retrieve → draft → review → preflight | [`skills/`](skills/) B02–B05 | 🟡 Designed; needs live doc I/O + SharePoint |
| **5. Manage** | Clarifications, deadlines, sign-off | [`skills/`](skills/) B06 | 🟡 Designed; needs portal/mailbox link |
| **6. Learn** | Feed outcomes back into the library | [`skills/`](skills/) B07 | 🟡 Designed; depends on stage 4 |

The **gap** this project closes: today the two halves (discovery ↔ bid skills)
don't share a data model or a handoff, there's no planning layer, and the AI
pre-fill has no live **SharePoint** library behind it yet.

---

## Repository layout

```
.
├── discovery/     # Working PoC: pull → normalise → store → filter → display opportunities
│   ├── *.py       #   FastAPI + SQLite connectors (Find a Tender, Contracts Finder)
│   ├── web/       #   React/Vite UI (live search, filters, CSV export)
│   └── CLAUDE.md  #   Project spine for the discovery engine
├── skills/        # Bid-lifecycle skill chain B00–B07 (Claude skills + helper scripts)
│   └── bid_skills_v2/  #   Current version; targets a 3-library SharePoint bid store
├── knowledge/     # The "why": FWF situation + UK procurement reference
│   ├── 01-current-position.md      # G-Cloud 15 disregard, EFS gap, handover state
│   ├── 02-recovery-plan.md         # 3-horizon recovery plan (Arobs PCG, alt frameworks)
│   ├── 03-knowledge-base.md        # UK procurement primer (PA23, G-Cloud, EFS, PCG)
│   ├── 04-skills-review-2026-07-08.md  # Review that shaped the B00–B07 skill design
│   └── VERIFIED_FACTS.md           # ✅ Live-verified facts + sources (re-check before use)
└── README.md      # This file — the spine
```

## Running the discovery engine

```bash
cd discovery
python3 db.py                              # create/inspect bids.db
python3 find_tender_filter.py 120          # fetch → normalise → upsert
uvicorn api:app --reload --port 8000       # JSON API
cd web && npm install && npm run dev       # UI at http://localhost:5173
```

`bids.db` and `node_modules/` are gitignored (rebuildable from the connectors).

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
