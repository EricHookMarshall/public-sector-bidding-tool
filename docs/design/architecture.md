# Architecture — direction

*Decided 2026-07-08 (Step 3). Agreed **direction**, not final detail — captured from the design conversation. Refine as we build.*

## Product form

- **Local app now.** Runs on a local machine, no cloud infra. **Extend the existing discovery PoC**
  (Python/FastAPI + SQLite + React/Vite) into the full journey rather than starting over.
- **Longer-term goal (budget-dependent): an Azure SPA.** A hosted single-page app in Azure is the
  aspiration *if this proves out and budget appears* — not built for now. Choices today shouldn't
  block that migration, but we don't design for Azure yet.
- **Shape:** one **end-to-end, easily navigable** journey across the six stages, where **AI
  facilitates completion and drives tasks** (not a passive dashboard). The left-to-right journey nav
  from the approved [journey-mockups](journey-mockups.html) is the spine; the visual style is approved.

## Data & SharePoint

- The bid library must eventually live in **SharePoint** (3 libraries: Submissions / Approved Answer
  Bank / Evidence Register — see `skills/bid_skills_v2/SHAREPOINT.md`).
- MS Graph / SharePoint is **not available in this environment**, and may not be soon.
- **Approach: a "library provider" seam** — one interface the app reads/writes the bid library
  through, with swappable backends (same pattern as the discovery `sources.py` registry already in the repo):
  - **`LocalMirror` (now)** — real exported SharePoint data, or hand-seeded samples, held locally
    (folder + SQLite) mirroring the 3-library structure. Lets us build Stage 4 (AI pre-fill) for real,
    against realistic data, today.
  - **`GraphSharePoint` (later)** — the live MS Graph connection, dropped in behind the same interface
    with no app changes.
- **Open:** how we get real data local — Graph export vs manual export vs a curated sample set.
  Decide when we reach Stage 4; don't block earlier stages on it.

## Stack (working assumption)

- **Backend:** Python / FastAPI (matches discovery). **Store:** SQLite (local, one file).
  **Frontend:** React / Vite (matches discovery + the approved mockup style).
- **AI:** Claude, driving task completion — the B-series skill logic (B01–B07) made app-callable.

## Future features — noted, not scoped

- **HubSpot integration** *(user request, 2026-07-08)* — connect the bid pipeline and buyer
  relationships with HubSpot CRM so opportunities map to accounts/deals and sales + bidding stay
  aligned. Good feature; **parked for later**, not in current scope.
