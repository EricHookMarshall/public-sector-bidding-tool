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
- [x] **Manage (Stage 5) — FOR003 clarification register + pre-flight gate** (2026-07-09, session 6) —
      `src/clarification.py` (FOR003 rig: statuses, 9-item preflight, `resolve_preflight` enforcing
      auto+expiry items, `alerts`), `bid_manage` table, `/api/manage/*` + `GET`/`PUT /api/bids/{id}/manage`
      (gate enforced server-side → 409 if blocked), real board→detail UI, `seed_manage_demo.py`.
      Live-verified over HTTP.
- [x] **User review of the journey shell** (2026-07-09, session 7) — user confirmed the browser
      click-through was done and the stages look fine. Clears the 5-session "0 human-reviewed" thread.
- [x] **Learn (Stage 6) — B07 outcome + win-rate + library-feedback loop** (2026-07-09, session 7) —
      `src/outcome.py` (B07 rig: results, Lessons Learned, `library_suggestions`, `winrate_summary`,
      `alerts`), `bid_outcomes` table, `/api/learn/*` + `GET`/`PUT /api/bids/{id}/outcome` (result
      validated → 400), real win-rate board→outcome-detail UI replacing the mock, `seed_learn_demo.py`.
      Live-verified over HTTP; `npm run build` clean. Suggestions proposed + signed off, never written
      to a real library (honest boundary).
- [x] **Complete (Stage 4) — FOR006 matrix + LocalMirror library + AI pre-fill** (2026-07-09, session
      7b) — `src/library.py` (LocalMirror provider over the real gitignored export; expiry extracted
      from Notes; retrieval + evidence ledger; `master_template`), `src/response.py` (FOR006 rig + live
      word-count gate), `src/complete_ai.py` (retrieval-grounded drafting), `bid_responses` table,
      `/api/complete/*` + `/api/library` + matrix GET/PUT + index-based AI-draft, real matrix→workspace
      UI replacing the mock, `seed_complete_demo.py`. Live-verified over HTTP; `npm run build` clean.
      **The journey is now feature-complete — all 6 stages real.**
- [ ] **User browser walk of Complete + Learn** — the two stages built this session, verified
      server-side only. Open `#complete` / `#learn` at <http://localhost:5173> and flag anything wrong.
- [ ] **Commit the milestone** — Learn + Complete are uncommitted. Commit on the user's request.

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
