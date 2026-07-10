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

## Code-review remediation (2026-07-09)

> Two reviews in [`docs/code_reviews/`](../docs/code_reviews/): **Codex quick** (2 High / 3 Med / 8 Low)
> and **Fable comprehensive** (6 High / 17 Med / 39 Low). Deduped into waves below — **ordered by
> dependency, each item decoupled** (independently pickable) unless a `↳` notes a coupling. Spot-verified
> real before filing: newline injection (`config.py:77`), compose 0.0.0.0 bind (`docker-compose.yml:28`),
> FTS lexicographic deadline compare (`find_tender_filter.py:155`). Nothing fixed yet — this is the plan.

### Wave 0 — Security blockers ✅ DONE (verified in commit `0f35c70`, session 11)

- [x] **Newline injection in `config.upsert_env`** (`src/config.py:104-109`) — control-char guard rejects
      any C0 char (incl. `\r`/`\n`) before writing `.env`; `PUT /api/config` maps the `ValueError` to a 400.
      **Functionally verified**: a live `upsert_env({'ANTHROPIC_MODEL': '…\nLOCAL_AUTH_BYPASS=1'})` call
      raised and wrote nothing.
- [x] **docker-compose binds 0.0.0.0** (`docker-compose.yml:30`, `49-52`) — SQL Server + the three Azurite
      ports are now published on `127.0.0.1` only (Azurite's in-container `0.0.0.0` bind is intentional +
      commented). Not LAN-reachable.

### Wave 1 — Azure-promotion blockers ✅ DONE (verified in commit `0f35c70`, session 11)

> All ten confirmed implemented against the actual code (not just the plan) and verified green: backend
> imports clean + FastAPI app constructs; `npm build` clean. These landed in the Phase C tree.

- [x] **`openpyxl` used-but-undeclared** — declared `openpyxl>=3.1` (`requirements.txt:18`); `library.py`
      `_openpyxl()` + `LocalMirror.available()` require BOTH the file AND the import, and `status()` returns
      `available:false` + a `reason` otherwise (no contradictory "connected, 0 items").
- [x] **`db.py` ALTER TABLE dialect bug** — `init_db` branches `add_kw = "ADD COLUMN" if sqlite else "ADD"`
      (`src/db.py:467`); T-SQL back-fill no longer emits the illegal `COLUMN` keyword.
- [x] **Connection lifecycle** — `get_conn` is a yielding FastAPI dependency with try/finally
      (`src/api.py:78`); `init_db` runs once at startup via a `lifespan` context manager (`api.py:65`).
      Every handler takes `conn=Depends(get_conn)`; error paths no longer leak connections.
- [x] **Settings persistence seam** — `config.persistence_mode()` ("env_file" local / "platform" on Azure
      via `WEBSITE_INSTANCE_ID`, `CONFIG_STORE` override) + `ConfigReadOnly`; `PUT /api/config` maps it to a
      409. The dotfile write is scoped to local mode.
- [x] **CSV export via the auth/base-URL seam** — `downloadExport()` (`web/src/api.js:106`) routes through
      `apiFetch` (Bearer + `VITE_API_BASE_URL`) and streams a Blob download; `SearchStage.jsx:197` calls it.
      No bare `<a href>`.
- [x] **`.catch` on the MSAL boot chain** — `web/src/main.jsx:41-49` catches any init/redirect rejection,
      logs it, and calls `render()` anyway so the deployed SPA can't go permanently blank.
- [x] **`AAD_DEFAULT_ROLE` default too broad** — `auth._auth_policy_error()` fails closed (500) under real
      auth when neither a group→role map nor an explicit `AAD_DEFAULT_ROLE` is set; no broad role is ever
      silently in force on Azure.
- [x] **Entra groups-overage handled** — `auth._has_group_overage()` detects the `hasgroups`/`_claim_names`
      marker and returns a loud 403 rather than silently downgrading (`src/auth.py:142,281`).
- [x] **`pyodbc` conditional** — commented out with install instructions (`requirements.txt:14`); clean
      SQLite-only `pip install` no longer breaks on missing unixODBC.
- [x] **`pool_pre_ping`** — `create_engine(..., pool_pre_ping=True)` (`src/db.py:432`); guards Azure SQL
      idle-connection drops, harmless for SQLite.

### Wave 2 — Correctness bugs (independent; real defects, not just Azure)

- [ ] **FTS deadline kept by string compare** (`src/find_tender_filter.py:155`) — `end >= now.isoformat()`
      lexicographic; an offset-stamped deadline already past UTC can be stored as **open** — in a deadline
      tool. CF already solves this with a parsed offset-aware `is_open`. Move `is_open` into
      find_tender and use it in both connectors. **Med** (Fable §2). `↳` also removes duplication (Wave 5).
- [ ] **`seed_learn_demo.py:115` is Python-3.12-only** — nested same-type quotes in an f-string field
      (PEP 701); `SyntaxError` at import on ≤3.11 while the rest of `src/` loads. Extract the fragment, or
      declare `requires-python>=3.12`. **Med** (Fable §2).
- [ ] **Seeders use `LIMIT 1`** (`seed_plan_demo.py:58`, `seed_complete_demo.py:48`, `seed_manage_demo.py:102`,
      `seed_learn_demo.py:79`) — SQLite-only; needs `OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY` for SQL Server.
      **Low** — *(was already the "Phase B tail" item below; folded here.)*
- [ ] **Seeder demo dates hard-coded to ~July 2026** (`seed_manage_demo.py:54,67,77`, `seed_plan_demo.py:44`,
      `seed_learn_demo.py:38,57`) — the advertised passed/imminent/done alert spread decays to all-OVERDUE
      within weeks. Compute from `date.today()` offsets. **Low** (Fable §1).

### Wave 3 — Doc/comment truth sweep (independent, cheap; batch in one pass)

- [ ] **Stale `discovery/.env` refs** (7×: `src/.env.example:1`, `src/config.py:4`, `src/api.py:26,455`,
      `web/src/SettingsView.jsx:111`, `web/src/journey.js:72,132`) — dir doesn't exist; `.env` lives in
      `src/`. Two are user-facing UI copy → make host-neutral ("stored server-side, never returned").
      **Med** (both).
- [ ] **"only Search is live" stale comments** (`web/src/App.jsx:19`, `web/src/journey.js:8-12`,
      `SearchStage.jsx:1`, `styles.css:207-209` banner) — all six stages are live; these contradict the code
      and point at dead MockStage. **Med/Low** (both).
- [ ] **Post-port / model stale comments** — `src/llm.py:5` docstring says Opus default (actually
      `claude-haiku-4-5`); `db.py:12-13,536` + `api.py:164` still say "sqlite3.Row"/"12-field sketch";
      `complete_ai.py:88` claims a non-existent import cycle; `api.py:2-16` docstring lists 3 of ~30
      endpoints + "SQLite" not dual-mode. **Low** (Fable §1).

### Wave 4 — Dead / orphaned code removal (independent, cheap; batch)

- [ ] **Delete MockStage + ScopeCard + their CSS** (`web/src/stages/MockStage.jsx`, `ScopeCard.jsx`;
      `styles.css:211-230,298-314`; strand the `scope`/`asset` data in `journey.js:24-193`) — preview-era
      orphans imported by nothing. Decide StagePlaceholder's fate (keep as defensive seam w/ a comment, or
      remove `STATE_MAP` design/gap + `.s-design/.s-gap` CSS too). **Med** (both). *(Supersedes the old
      StagePlaceholder/MockStage dead-code item below.)*
- [ ] **Unused imports / dead branches** — `src/clarification.py:26` unused `datetime`; `PlanStage.jsx:8`
      unused `useMemo`; `TriageStage.jsx:103-104` dead raw-value branch in `setField`;
      `db.py:1015` `bids` local shadows the Table; `SearchStage.jsx:88` no-op spread + `:259` inert
      eslint-disable (no ESLint in repo). **Low** (both).

### Wave 5 — Right-sizing / consistency refactors (quality; lower priority, some coupling)

- [ ] **Consolidate `web/src/api.js` error handling** (`:87-94` ×8 vs existing `sendJSON:299-314`) — route
      the stage helpers through one JSON helper; also make `getJSON:49-53` surface server `detail`. **Med**.
- [ ] **Collapse the 5 near-identical `db.py` upserts** (`:559-907`) into one `_upsert_one` + thin
      wrappers. **Med.** `↳` do alongside Wave 1 connection lifecycle; also the place to add the
      unique-violation retry (§7 upsert race, Low).
- [ ] **Extract shared web formatters** — `deadlineBadge`/`daysUntil`/`fmtMoney` duplicated 2-3× across
      Search/Triage/Plan/Manage/Complete; Complete hard-codes 7/14 thresholds while siblings read
      `imminent_days` from the server → silent disagreement on "urgent". `web/src/format.js`. **Med** (Fable §2).
- [ ] **De-dupe backend twins** — `api._derive_open` == `refresh_clean._open_closed` (move to `db.py`);
      connector `to_record`/`run`/`main` near-verbatim (extract a shared skeleton when a 3rd source lands);
      cache `LocalMirrorProvider.items()` (xlsx parsed twice per `/api/library` request). **Low/Med** (Fable §6).
- [ ] **Minor parity polish** — `refresh_clean.py:135` prints sqlite path even under `DB_URL`;
      `SettingsView.jsx:102` hard-codes "Anthropic API key" label; add a root `.env.example` documenting
      `MSSQL_SA_PASSWORD` (distinct from `src/.env`); split grouped imports in the two connectors. **Low**.

### Wave 6 — Deferred-behind-seam hardening + advisory security (lower priority)

- [ ] **Raise on unknown `LIBRARY_PROVIDER`** (`src/library.py:388`) — currently silently falls back to
      LocalMirror, so a typo'd `graph_sharepoint` in Azure config reads the absent local mirror and reports
      "not connected" with no hint. Mirror `llm.get_provider()`'s raise-with-valid-options. **High** per
      Codex / Low per Fable — cheap, do it now even before `GraphSharePointProvider` exists.
- [ ] **Advisory auth hardening** — `auth.py:216-219` return a generic 401 (log the real reason
      server-side); catch `jwt.PyJWTError` not bare `Exception` (JWKS outage ≠ 401 → 503);
      `authConfig.js:31` use `sessionStorage` not `localStorage` for MSAL; add `.env`/`.env.*`/`!.env.example`
      to `web/.gitignore`; the 4 dormant `dangerouslySetInnerHTML` sinks vanish with Wave 4's MockStage/ScopeCard
      deletion. **Low** (both / Fable §8).
- [ ] **Skills-chain vocabulary drift** (`skills/b01,b05,b06,b07/scripts/*`) — duplicate logic since built
      for real in `src/` with divergent enums (e.g. clarification statuses, outcome library actions). Declare
      `src/` canonical in each SKILL.md + align vocab now so folding them in is wiring, not reconciliation.
      Also: atomic writes (`os.replace`) in skills `_save`; drop `--break-system-packages` guidance
      (`build_matrix.py:60`). **Med/Low** (Fable §5) — parked until the chain is actually folded in.

## Surfaced / open

- [x] **Azure migration — Phase B (DB portability)** (2026-07-09, session 9) — `src/db.py` ported off raw
      `sqlite3` to a SQLAlchemy Core dual-mode shim (SQLite local / Azure SQL cloud via `DB_URL`); only
      db.py changed (qmark-compatible `_Conn`/`_Row` adapter, zero caller edits). `docker-compose.yml`
      (SQL Server 2022 + Azurite scaffold) added; two dialect bugs fixed (ORDER BY IS NULL; NVARCHAR(MAX)
      key columns). **Verified `IDENTICAL BEHAVIOUR: True` on both backends** vs a live SQL Server 2022
      container; app serves through the adapter. `requirements.txt` updated (SQLAlchemy + pyodbc).
- [x] **Azure migration — Phase C (auth)** (2026-07-09, session 10) — `src/auth.py` (`require_auth`
      PyJWT/JWKS guard + `groups`→role + `LOCAL_AUTH_BYPASS`), wired app-wide in `src/api.py`
      (`FastAPI(dependencies=[…])`; config writes `require_roles("Admin")`); env-driven CORS. SPA:
      `authConfig.js` + MSAL gate in `main.jsx`/`App.jsx` + Bearer at one `apiFetch` choke point in
      `api.js` + `VITE_API_BASE_URL`; `msal-browser`/`msal-react` added. Verified locally: 12/12 self-minted
      token checks + HTTP (bypass-off → 401 everywhere) + `npm run build` clean. `.env.example`s +
      `requirements.txt` (PyJWT) + `azure-target.md` updated. **Uncommitted.**
- [ ] **Phase C tail — live MSAL browser sign-in** — the redirect round-trip needs a real dev-tenant app
      reg (Tier-2, no emulator). Supply `VITE_AAD_*` + `AAD_TENANT_ID`/`AAD_API_CLIENT_ID`, set
      `LOCAL_AUTH_BYPASS=0`, sign in, confirm the Bearer reaches the API and role-gating works.
- [ ] **Phase B tail — seeder `LIMIT 1`** — the 4 `seed_*_demo.py` still use sqlite-only `LIMIT 1`; port to
      `OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY` so the seeders also run on SQL Server. Low priority (dev-local).
- [ ] **Azure OpenAI provider** — `src/llm.py` has a documented skeleton (`AzureOpenAIProvider`), not
      implemented. Now sequenced into the Azure migration's Phase E; build when Azure access is
      provisioned (client requirement).
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
