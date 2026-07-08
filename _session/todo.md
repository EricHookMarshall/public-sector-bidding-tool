# TODO

> Active and in-flight work only. Completed items are cold history — see [progress.md](progress.md)
> (most-recent-first), which holds the full dated retrospective per session.

## Active queue

- [x] **Next definition step chosen: (b) app shell** (2026-07-09) — built on the discovery front end;
      6-stage shell with Search live + 5 illustrative preview stages. See `discovery/_session/`.
- [ ] **User review of the running shell** — click through all 6 stages + theme toggle, flag issues.
- [ ] **Data model** — now the next real build step (see below); blocks wiring the mock stages.

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
