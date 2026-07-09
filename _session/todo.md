# TODO

> Active and in-flight work only. Completed items are cold history — see [progress.md](progress.md)
> (most-recent-first), which holds the full dated retrospective per session.

## Active queue

- [x] **Wire Triage (B01) for real** (2026-07-09, session 3) — FOR001 qualification/bid schema +
      real form in `TriageStage.jsx`. Storage decision resolved: extended `discovery/bids.db`.
- [x] **AI pre-fill for Triage** (2026-07-09, session 3) — provider-agnostic seam (Anthropic built,
      Azure OpenAI planned), FOR001 drafting, default model `claude-haiku-4-5` for cost. Live-verified
      with a real key. See `discovery/_session/todo.md` for file-level detail.
- [x] **Settings screen** (2026-07-09, session 3) — `#settings` view for AI provider/model/key,
      write-only key storage, live Test connection.
- [ ] **Plan (Stage 3)** — `data-model.md` §3 (`BidPlan`: pipeline position + FOR002 timeline) is
      fully specified; flagged as the highest-value missing piece. Recommended next.
- [ ] **User review of the running shell** — click through all 6 stages + the new Triage form and
      Settings screen, flag issues. Still outstanding after 3 sessions.

## Surfaced / open

- [ ] **Azure OpenAI provider** — the client will need AI drafting on Azure OpenAI, not just
      Anthropic. Seam is built (`discovery/llm.py`); implementation deferred until Azure access is
      provisioned outside the session.
- [ ] **Library-provider seam** — one interface for the bid library; `LocalMirror` now → `GraphSharePoint`
      later (see `docs/design/architecture.md`). `data-model.md` recommends seeding `LibraryItem` by
      parsing the mirrored `knowledge/SharePoint Folder/` trackers now (proven working this session) —
      decide when building the Complete stage.
- [ ] **HubSpot integration** — future feature (pipeline ↔ CRM). Noted, not scoped.
- [ ] **Cleanse FWF strategy docs** (`knowledge/01–03`) — strip `.docx` export artefacts. Low priority.

## Parked / optional

- [ ] **Third+ discovery source** — `discovery/sources.py` makes it a one-connector add (Scotland / Wales / TED).
- [ ] **Swap RM6263 → DOS7** in the recovery-plan alternative-framework shortlist (per VERIFIED_FACTS.md).

## Done

Completed items are cold history — see [progress.md](progress.md).

- [x] **Phase 0 — consolidate, verify, connect** (2026-07-08): clean repo structure, `.gitignore`, git
      init + remote + push, facts verified, README + CLAUDE + `_session/` + skills scaffolded.
