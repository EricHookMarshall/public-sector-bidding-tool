# TODO

> Active and in-flight work only. Completed items are cold history — see [progress.md](progress.md)
> (most-recent-first), which holds the full dated retrospective per session.

## Active queue

- [x] **Restructure repo — flatten the nested sub-app** (2026-07-09, session 5) — `discovery/` removed;
      backend → `src/`, frontend → `web/`, brief → `support/`, `requirements.txt` → root; `bids.db` +
      `.env` moved into `src/`. Duplicated `_session/`/`.claude/`/`CLAUDE.md` consolidated to one set at
      root. App live-verified running from the new layout.
- [x] **Plan (Stage 3)** (2026-07-09, session 4) — `src/bidplan.py` (FOR002 rig), `src/db.py`
      (`bid_plans` table), `src/api.py` (reference/board/GET/PUT), `PlanStage.jsx` (real pipeline board +
      capacity + FOR002 timeline). `src/seed_plan_demo.py` for reviewable demo data. Live-verified.
- [x] **Triage (B01) + AI pre-fill + Settings** (2026-07-09, session 3) — FOR001 form wired to `bids.db`;
      provider-agnostic AI seam (`src/llm.py`, Anthropic live, Azure OpenAI skeleton); `#settings` screen.
- [ ] **User review of the journey shell** — click through all 6 stages, Triage's form, Settings, and
      Plan's board + timeline in the browser (<http://localhost:5173>) and flag anything wrong.
      **Still not observed by a human across 4 sessions** — only build/curl/TestClient verified so far.
- [ ] **Manage (Stage 5) or Complete (Stage 4)** — next stage to build. Manage (FOR003 clarification log)
      has no external blocker and directly encodes the clarification-deadline failure; Complete (FOR006)
      is next in journey order but blocked on live SharePoint/MS Graph. Not decided — see handover.

## Surfaced / open

- [ ] **Azure OpenAI provider** — `src/llm.py` has a documented skeleton (`AzureOpenAIProvider`), not
      implemented. Build when Azure access is provisioned (client requirement).
- [ ] **`web/src/StagePlaceholder.jsx` is dead code** — superseded by the per-stage screens; not
      referenced in `App.jsx`'s `VIEWS` map. Delete or repurpose.
- [ ] **Team capacity (Plan)** — `bidplan.DEFAULT_TEAM_CAPACITY_DAYS` (25) is a tuned placeholder, not a
      real FWF number, and isn't persisted — only overridable per-request. Needs a real source.
- [ ] **Cross-source dedupe** — `(source, ocid)` dedupes within a source; cross-source matching (same
      notice on FTS and CF) not yet handled. Low priority given the value-band split.

## Parked / optional polish

- [ ] **CPV label badge on cards** — `src/cpv_catalog.py` has descriptions; could show a labelled chip.
- [ ] **Third API source** — `src/sources.py` registry makes it a one-connector-plus-one-line add
      (TED, Scotland eTender, Crown Commercial Service).
- [ ] **Lifecycle badge on cards** — `stale`/`closed` flag is in the filter + detail view, not the card.
- [ ] **CPV scope widen** — currently IT/software only. Widen `TARGET_CPV` + `src/cpv_catalog.py`.

## Done

Completed items are cold history — see [progress.md](progress.md).

- [x] **Phase 0 — consolidate, verify, connect** (2026-07-08): clean repo structure, `.gitignore`, git
      init + remote + push, facts verified, README + CLAUDE + `_session/` + skills scaffolded.
