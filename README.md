# Public Sector Bidding Tool

A set of tools to help someone — **even a novice** — navigate UK public sector
bidding end to end: **find** relevant opportunities, **triage** them, **plan**
which to bid and when, **complete** the bids (AI-assisted from a library of past
work), and **manage** them through to award and learning.

Built for **FWF (Future WorkForce UK Ltd)**, a UK subsidiary of Arobs Group. See
[`knowledge/`](knowledge/) for the business context and why this exists.

> **Status:** the app is **feature-complete — all six stages are real, wired to
> `bids.db`, and live-verified.** Complete reads FWF's real bid library through the
> `LocalMirror` provider seam over a gitignored local export; live `GraphSharePoint`
> drops in behind the same seam once MS Graph is provisioned. The bid-lifecycle
> skills (`skills/`) are designed but not yet folded into the app.

---

## The journey (and where each stage stands)

```
1. SEARCH  →  2. TRIAGE  →  3. PLAN  →  4. COMPLETE  →  5. MANAGE  →  6. LEARN
```

| Stage | What the user does | Lives in | State |
|---|---|---|---|
| **1. Search** | Find relevant opportunities across sources | [`src/`](src/) + [`web/`](web/) | ✅ Live — Find a Tender + Contracts Finder + Public Contracts Scotland + Sell2Wales (upstream API recovering) |
| **2. Triage** | Bid / no-bid with clear reasons | [`src/`](src/) + [`web/`](web/) | ✅ Live — real FOR001 form + AI pre-fill |
| **3. Plan** | Which bids, when, with what capacity | [`src/`](src/) + [`web/`](web/) | ✅ Live — pipeline board + capacity + FOR002 timeline |
| **4. Complete** | Matrix → retrieve → draft → review → preflight | [`src/`](src/) + [`web/`](web/) | ✅ Live — FOR006 matrix + AI pre-fill over the real bid library (`LocalMirror`) |
| **5. Manage** | Clarifications, deadlines, sign-off | [`src/`](src/) + [`web/`](web/) | ✅ Live — FOR003 clarification register + pre-flight gate |
| **6. Learn** | Feed outcomes back into the library | [`src/`](src/) + [`web/`](web/) | ✅ Live — B07 outcome capture + win-rate + library-feedback loop |

**What remains external:** Complete runs today over a gitignored **local export** of
the bid library through the `LocalMirror` seam; the live `GraphSharePoint` provider
drops in behind the same seam once MS Graph is provisioned. The `skills/` B00–B07
chain is designed but not yet folded into the app.

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

- **Phase 0 — Consolidate & verify** ✅ one repo, clean structure, facts verified
  (`knowledge/VERIFIED_FACTS.md`).
- **Phase 1 — Search → triage** ✅ Triage (FOR001) wired to live data with AI
  pre-fill; a Go promotes an opportunity into a bid.
- **Phase 2 — Planning layer** ✅ pipeline board + capacity + FOR002 timeline +
  reactive deadline/owner/capacity alerts.
- **Phase 3 — Complete (Stage 4) + bid library** ✅ FOR006 compliance matrix + AI
  pre-fill over FWF's real bid library through the `LocalMirror` seam (word-count gate,
  evidence/expiry ledger, retrieval-grounded drafting).
- **Phase 4 — Manage & learn** ✅ Manage (Stage 5): FOR003 clarification register +
  pre-flight gate. Learn (Stage 6): outcome capture + win-rate + library-feedback loop.
- **Beyond the journey** *(optional / deferred)*: live `GraphSharePoint` provider (when
  MS Graph lands), Azure OpenAI provider, and the Azure hosting migration.

## Open decisions

1. **Live `GraphSharePoint` timing** — build the MS Graph provider behind the existing
   `LocalMirror` seam once real credentials are provisioned (this environment has Google
   Drive, not SharePoint). Complete already runs on the sanctioned local export.
2. **Azure migration** — Phases B (DB portability) + C (Entra ID auth) are done and
   locally verified; Phase D (hosting scaffold) needs an Azure subscription.

*Resolved:* product form — the discovery UI **was** grown into the whole 6-stage
journey app. Sequencing — **breadth first**; the journey is now feature-complete.
