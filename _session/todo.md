# TODO

> Active and in-flight work only. Completed items are cold history — see [progress.md](progress.md)
> (most-recent-first), which holds the full dated retrospective per session.

## Active queue

- [ ] **Confirm next definition step** — (a) data model (shared bid record across the 6 stages), or
      (b) start the local app shell from the approved mockup. Pick with user first.

## Surfaced / open

- [ ] **Data model** — define the record that flows Opportunity → Qualified Bid → Answers → Evidence →
      Clarifications → Outcome. Feeds every stage.
- [ ] **Library-provider seam** — one interface for the bid library; `LocalMirror` now → `GraphSharePoint`
      later (see `docs/design/architecture.md`). Decide how `LocalMirror` gets seeded (parked to Stage 4).
- [ ] **HubSpot integration** — future feature (pipeline ↔ CRM). Noted, not scoped.
- [ ] **Cleanse FWF strategy docs** (`knowledge/01–03`) — strip `.docx` export artefacts. Low priority.

## Parked / optional

- [ ] **Third+ discovery source** — `discovery/sources.py` makes it a one-connector add (Scotland / Wales / TED).
- [ ] **Swap RM6263 → DOS7** in the recovery-plan alternative-framework shortlist (per VERIFIED_FACTS.md).

## Done

Completed items are cold history — see [progress.md](progress.md).

- [x] **Phase 0 — consolidate, verify, connect** (2026-07-08): clean repo structure, `.gitignore`, git
      init + remote + push, facts verified, README + CLAUDE + `_session/` + skills scaffolded.
