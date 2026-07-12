# TODO — active queue

> **Unfinished work only.** Completed items are cold history — see [`progress.md`](progress.md)
> (most-recent-first, full dated retrospective per session). Everything through **session 13 is
> committed** (`9c31fa8`). When an item ships, note it in `progress.md` and delete it here.

## Feature backlog (needs scoping with the user)

- [ ] **C-series — "Compliance & Renewals" view** ⭐ (highest founding-purpose payoff — the missed-renewal
      failure the tool exists to prevent). **C3:** compliance docs already exist + are expiry-tracked in
      `library.py` (*Company Credentials*; ISO reads **EXPIRED 2025-10-31** in live data) — gap = structured
      renewal dates for the rest + an **org-level** view (today buried per-bid in Complete). **C4:**
      framework/contract membership-period tracker (RM6263-expired precedent). **Scope with the user first.**
- [ ] **C1 — clarifications: discoverability + AI dedupe** — the FOR003 register exists on Manage (click a
      bid); make the drill-in obvious (board shows only a count). NEW: AI-ingest incoming CQs, dedupe, flag
      "already answered by CQ #n".
- [ ] **C2 — per-bid workspace + slim per-bid KB** — opportunity visible, edits saved, a bid-specific KB the
      AI grounds on. Net-new; aligns with the `skills/` 3-library design. Needs a design pass.
- [ ] **F-series — more sources / search** — F1: Public Contracts Scotland, Sell2Wales, eTendersNI, G-Cloud
      behind the normalise→`bids.db` seam. F2: multi-criteria search. **F5: ITT ingestion → auto-build the
      compliance matrix** (biggest; matrix schema is already per-bid dynamic, just no parser).

> **Noted (already built — no action):** Modern Slavery is already a Manage pre-flight item + a library
> credential ("Anti-Bribery & Modern Slavery Policies") — don't re-add.

## Harness follow-ups (from the 2026-07-10 harness-design review — `docs/harness_design/`)

- [x] **Canonical verification command** (2026-07-11) — `make check` (`scripts/check.sh`): backend
      pytest (deadline / CPV / qualification / preflight / auth-roles + app-construct = **29 tests**) →
      doc-state consistency guard → Vite build. `make check-fast` skips the build. `tests/` + `pytest.ini`
      + `requirements-dev.txt`. **Next extension:** add live-source tests behind an explicit flag (rung 4).
- [ ] **Fold the `skills/` B00–B07 chain into the app** — declare `src/` domain vocab canonical (done in
      CLAUDE.md), align skill enums/handoff schemas to it, route skill calculations through shared code.
      Resolve the duplicate `fwf-tender-sweep` skill-name collision (two `tender_sweep/` variants). Parked
      until the chain is actually folded in.

## Code-review remediation — ✅ FULLY CLEARED (Waves 0–6)

> Two reviews in [`docs/code_reviews/`](../docs/code_reviews/). **All waves are now done** — Waves 0–1
> (`0f35c70`), Wave 2 (session 14, `33980dd`), Waves 3–4 (session 15), Waves 5–6 (session 16). Several late
> items turned out to be false records (already implemented); full per-wave retrospectives + the false-record
> list live in `progress.md`. Nothing left to pick here.

## Surfaced / open (parallel tracks + polish)

- [ ] **Azure Phase C tail — live MSAL browser sign-in** — redirect round-trip needs a real dev-tenant app
      reg (no emulator). Supply `VITE_AAD_*` + `AAD_TENANT_ID`/`AAD_API_CLIENT_ID`, set `LOCAL_AUTH_BYPASS=0`,
      sign in, confirm the Bearer reaches the API and role-gating works.
- [ ] **Azure Phase D — hosting scaffold** per `docs/design/azure-target.md` (needs an Azure subscription).
- [ ] **Azure OpenAI provider** — `src/llm.py` has a documented skeleton, not implemented; build when Azure
      access is provisioned (sequenced into Phase E).
- [ ] **Cross-source dedupe** — `(source, ocid)` dedupes within a source; cross-source matching (same notice
      on FTS + CF) not yet handled. Low priority given the value-band split.
- [ ] **AI-draft provenance persistence** — win-themes/evidence shown in the UI but not saved with the answer.
- [ ] **Triage ✕ semantics (session 18 follow-on)** — Triage board is now explicit-pull (`triage_selections`);
      the board's ✕ still `dismiss`es (reversible hide) rather than de-selecting. In a pull model these
      overlap — decide whether ✕ should remove the selection outright. Cosmetic/UX, scope with user.
- [ ] **Connector `to_record`/`run`/`main` dedup** (deferred from Wave 5) — the two connectors are near-verbatim;
      extract the shared body **when a 3rd source lands** (doing it against 2 sources is speculative).
- [ ] **Parked polish** — CPV label badge on cards · lifecycle (`stale`/`closed`) badge on cards · widen CPV
      scope beyond IT/software (`TARGET_CPV` + `src/cpv_catalog.py`) · a 3rd source via `src/sources.py`.
