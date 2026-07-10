# Code Review — 2026-07-09

**Scope:** full repo — `src/` (FastAPI + SQLAlchemy dual-mode backend, incl. the uncommitted Azure Phase C files `auth.py`, modified `api.py`), `web/` (React/Vite SPA, incl. uncommitted MSAL wiring), `skills/*/scripts/`, seed/demo scripts, `docker-compose.yml`, dependency manifests, gitignores.
**Build context:** runs fully locally today (SQLite by default; SQL Server container + Azurite as the local Azure stand-ins via `docker-compose.yml`; `LOCAL_AUTH_BYPASS=1` as the Entra stand-in). Promotion to a real Resource Group must be a configuration change, not a code change — anything violating that is a finding.
**Method:** inventory first, then module-by-module against the eight priorities in order; security reviewed last as a pass/fail gate. Every finding is grounded in file:line. No changes applied.

---

## 1. Notes and annotations

No `TODO`/`FIXME`/`HACK`/`XXX` markers exist anywhere in `src/`, `web/src/`, or `skills/` (verified by grep). The one large commented-out block — the `AzureOpenAIProvider` sketch at `src/llm.py:100-129` — is deliberate, labelled, and consistent with the project's "out of scope is explicit" rule; not a finding. The stale-comment findings below are the category's substance.

**Location:** `src/.env.example:1`, `src/config.py:4`, `src/api.py:26`, `src/api.py:455`, `web/src/SettingsView.jsx:111`, `web/src/journey.js:72`, `web/src/journey.js:132`
**Category:** notes | **Severity:** Medium
**Issue:** Seven references to `discovery/.env` — a directory that does not exist. The `.env` actually lives in `src/` (`config.py:12` resolves it next to the module). Two of the references are user-facing UI copy (`SettingsView.jsx:111` help text, `journey.js` asset text).
**Why it matters:** A novice following the on-screen instruction hits a nonexistent path — this project's stated audience is "even a novice". On Azure the key won't live in a local `.env` at all, so the copy is doubly wrong post-promotion.
**Suggested fix:** Change all seven to `src/.env`; make the two UI strings host-neutral ("stored server-side, never returned") so they survive the Azure move.

**Location:** `web/src/App.jsx:19-20`
**Category:** notes | **Severity:** Medium
**Issue:** Comment says "Only 'search' is live; the rest are labelled preview screens (see MockStage)". All six stages in `VIEWS` are live components, and MockStage is imported by nothing.
**Why it matters:** Actively contradicts the code three lines below it and points readers at a dead file.
**Suggested fix:** Replace with "All six stages are live; StagePlaceholder is the defensive fallback" (or delete).

**Location:** `web/src/journey.js:8-12`
**Category:** notes | **Severity:** Medium
**Issue:** Header claims "Only 'search' is real; the rest render the scoped placeholder until their stage is built." Every stage carries `state: "live"` and renders a real view.
**Why it matters:** A false record in the file the shell treats as its source of truth — CLAUDE.md explicitly warns against carrying false records forward.
**Suggested fix:** Rewrite the header to reflect journey-complete status.

**Location:** `web/src/stages/SearchStage.jsx:1`
**Category:** notes | **Severity:** Low
**Issue:** "The one live stage" comment is stale — all six stages are live.
**Why it matters:** Misleads about app status.
**Suggested fix:** Reword to "Stage 01 — Search: the discovery engine's search UI".

**Location:** `web/src/styles.css:207-209`
**Category:** notes | **Severity:** Low
**Issue:** Section banner "MOCK STAGE SCREENS (Triage → Learn — illustrative previews)… Not wired to live data" is stale; those stages are live and the mock components are orphaned (see §5).
**Why it matters:** Misleading section labelling in a 776-line stylesheet.
**Suggested fix:** Delete the banner along with the dead rules beneath it (§5).

**Location:** `src/llm.py:5`
**Category:** notes | **Severity:** Low
**Issue:** Docstring says "Today the tool runs on Anthropic (`claude-opus-4-8`)"; the actual default is `claude-haiku-4-5` (`llm.py:53`, `config.py:13`).
**Why it matters:** Misstates the default model and its cost profile.
**Suggested fix:** Update the docstring to name the Haiku default (or reference `config.DEFAULT_MODEL` instead of a literal).

**Location:** `src/db.py:12-13`, `src/db.py:536`, `src/api.py:164`
**Category:** notes | **Severity:** Low
**Issue:** Three stale references: db.py's header contrasts the schema against "the older 12-field sketch in CLAUDE.md" (CLAUDE.md now describes the ~18-field shape); `_row_dict`'s docstring and api.py's `meta()` comment still say "sqlite3.Row" though the Phase B shim replaced it with `_Row`.
**Why it matters:** Post-port comments describing the pre-port world; low individually, but this codebase leans heavily on comments as documentation.
**Suggested fix:** Drop the CLAUDE.md contrast; s/sqlite3.Row/_Row/ in both comments.

**Location:** `src/complete_ai.py:88`
**Category:** notes | **Severity:** Low
**Issue:** `import response as R  # local import avoids a cycle at module load` — no cycle exists: `response.py` imports only `re`; nothing in the chain imports `complete_ai`.
**Why it matters:** A false constraint that will stop the next reader from safely moving the import to the top.
**Suggested fix:** Move the import to module level and delete the comment.

**Location:** `src/api.py:2-16`
**Category:** notes | **Severity:** Low
**Issue:** The module docstring lists three endpoints; the file now defines ~30 across six stages, plus auth/config/search. It also says "Reads the shared SQLite store" though the layer is dual-mode.
**Why it matters:** The file's own map is ~90% incomplete.
**Suggested fix:** Replace the endpoint list with a one-line-per-stage summary and say "the shared store (db.py — SQLite locally, Azure SQL via DB_URL)".

**Location:** `src/seed_manage_demo.py:54,67,77`, `src/seed_plan_demo.py:44`, `src/seed_learn_demo.py:38,57`
**Category:** notes | **Severity:** Low
**Issue:** Demo choreography is hard-coded to absolute dates around July 2026, while the docstrings promise a spread of "passed / imminent / done" signals relative to today.
**Why it matters:** The demos decay — within weeks every deadline reads OVERDUE and the advertised alert spread collapses; the project's own "facts decay" rule.
**Suggested fix:** Compute dates from `datetime.date.today()` offsets (today−3, today+2, today+5, …).

## 2. Consistency

**Location:** `src/find_tender_filter.py:155` (vs `src/contracts_finder_filter.py:57-66`)
**Category:** consistency | **Severity:** Medium
**Issue:** FTS decides "still open" by lexicographic string compare — `end >= now.isoformat()` — while the CF connector solves the identical problem with a real parsed, offset-aware comparison (`is_open`), whose comment explicitly names the timezone pitfall. The FTS version is wrong for offset-stamped deadlines within the offset window (e.g. `2026-07-09T23:45:00+01:00` = 22:45 UTC, already past, compares lexically *after* a 23:30 UTC now and is kept as open).
**Why it matters:** Same problem, two solutions, and the older one has the bug the newer one documents. A just-closed notice can be stored as open — in a deadline tool.
**Suggested fix:** Move `is_open` into `find_tender_filter.py`, use it in both connectors, delete the string compare.

**Location:** `src/seed_learn_demo.py:115`
**Category:** consistency | **Severity:** Medium
**Issue:** `f"{f' · lost to {view['winner']}' if view.get('winner') else ''}"` nests same-type quotes inside an f-string replacement field — valid only on Python 3.12+ (PEP 701). No Python floor is declared anywhere; every sibling script avoids the construct.
**Why it matters:** On Python ≤3.11 this file is a `SyntaxError` at import while the rest of `src/` loads fine — a confusing, environment-dependent break.
**Suggested fix:** Extract `winner = view.get("winner")` and build the fragment outside the f-string, matching lines 113-114's style (or declare `requires-python >= 3.12`).

**Location:** `web/src/stages/CompleteStage.jsx:21-27` (vs `PlanStage.jsx:22-28`, `ManageStage.jsx:15-21`)
**Category:** consistency | **Severity:** Medium
**Issue:** Third copy of `deadlineBadge`, but with hard-coded thresholds 7/14 while Plan and Manage take `imminent` from the server reference (`ref?.imminent_days ?? 7`). `daysUntil` is also duplicated (`PlanStage.jsx:330-337`, `ManageStage.jsx:25-32`) and `fmtMoney` three ways (`SearchStage.jsx:23`, `TriageStage.jsx:42`, `PlanStage.jsx:14`).
**Why it matters:** If `imminent_days` is ever changed server-side, Complete silently disagrees with Plan/Manage on what "urgent" means — precisely the deadline signalling this tool exists for.
**Suggested fix:** Extract `deadlineBadge`/`daysUntil`/`fmtMoney` into a shared `web/src/format.js`; pass `imminent` into Complete's badge like its siblings.

**Location:** `web/src/api.js:49-53`
**Category:** consistency | **Severity:** Low
**Issue:** `getJSON` throws only `${status} ${statusText}` and never surfaces the server's `detail`, unlike every mutating helper in the same file.
**Why it matters:** GET failures — e.g. a 403 from the Entra role gate on Azure — show "403 Forbidden" instead of the API's actual reason.
**Suggested fix:** Parse `detail` in `getJSON` the same way `sendJSON` does (falls out of the §6 consolidation).

**Location:** `src/library.py:388-396` (vs `src/llm.py:137-145`)
**Category:** consistency | **Severity:** Low
**Issue:** `library.get_provider()` silently falls back to LocalMirror on an unknown `LIBRARY_PROVIDER` value; `llm.get_provider()` raises with the list of valid options for the same situation.
**Why it matters:** A typo'd `LIBRARY_PROVIDER=graph_sharepoint` in Azure config will silently read the (absent) local mirror instead of erroring — the app would report "library not connected" with no hint why.
**Suggested fix:** Mirror llm.py: raise on unknown values; keep the documented fallback only for the not-yet-built `graph_sharepoint` key if that's deliberate — and say so in the error/comment.

**Location:** `src/seed_plan_demo.py:62`
**Category:** consistency | **Severity:** Low
**Issue:** The seed calls the private helper `db._row_dict(row)` while all its other access goes through db.py's public API.
**Why it matters:** Couples a script to a leading-underscore internal the SQLAlchemy port could legitimately rename.
**Suggested fix:** Expose `db.row_dict` publicly (it already has four public callers' worth of utility) or add a public lookup helper.

**Location:** `skills/b04-response-drafter/scripts/check_answer.py:99` (vs `:102`), `skills/b06-clarification-management/scripts/clarification_log.py:92`, `src/find_tender_filter.py:13`
**Category:** consistency | **Severity:** Low
**Issue:** Small one-file-two-styles splits: check_answer lowercases one signal list by comprehension and the other inline three lines apart; clarification_log imports `timedelta` inside a function while its other datetime names are top-level; find_tender_filter uses a comma-separated multi-import where the rest of `src/` imports one-per-line.
**Why it matters:** Each invites divergence when one side changes; trivial individually.
**Suggested fix:** Pre-lowercase both constant lists at module level; hoist `timedelta`; split the multi-import.

## 3. Cleanliness

No stray `console.log`, `debugger`, or Python debug prints exist in app code (verified); the items below are the residue found.

**Location:** `src/contracts_finder_filter.py:45-46`
**Category:** cleanliness | **Severity:** Low
**Issue:** The 429-backoff prints to stdout. This function runs inside API requests (`/api/search` → `sources.SOURCES[...]["run"]`), not just the CLI.
**Why it matters:** Library-path code writing raw prints into uvicorn's stdout; invisible to the API caller who's actually waiting on the backoff.
**Suggested fix:** Use `logging` (the connectors currently have no logger); keep prints in `main()` only.

**Location:** `web/src/api.js:29,33`
**Category:** cleanliness | **Severity:** Low
**Issue:** `console.error` of raw MSAL error objects on token-failure paths. No tokens are logged, but full error objects (correlation ids, claims hints) reach the console in production.
**Why it matters:** Noise plus mild info exposure in prod devtools.
**Suggested fix:** Log `err.errorCode`/message only, or gate on `import.meta.env.DEV`.

**Location:** `web/src/stages/SearchStage.jsx:88`
**Category:** cleanliness | **Severity:** Low
**Issue:** `setSelected({ ...o, region_label: o.region_label })` — the explicit property is already included by the spread; the wrapper is a no-op.
**Why it matters:** Scratch code implying a transformation that isn't happening.
**Suggested fix:** `setSelected(o)`.

**Location:** `web/src/stages/SearchStage.jsx:259`
**Category:** cleanliness | **Severity:** Low
**Issue:** `// eslint-disable-next-line react-hooks/exhaustive-deps` — but the project has no ESLint (no config, no devDependency).
**Why it matters:** Inert directive suggesting tooling that doesn't exist.
**Suggested fix:** Remove the comment (or actually add ESLint — the repo has no web linter at all).

**Location:** `skills/b06-clarification-management/scripts/clarification_log.py:33` (pattern also at `build_records.py:51`, `build_matrix.py:103`, `rank.py:92`, `preflight.py:120`, `debrief.py:70`, `check_answer.py:64`)
**Category:** cleanliness | **Severity:** Low
**Issue:** `json.dump(d, open(p, "w"))` — no context manager, non-atomic whole-file overwrite; the same open-without-`with` pattern recurs across all skills scripts.
**Why it matters:** A crash mid-dump truncates the clarification register — the exact artifact this project exists to never lose. (Mitigated: these scripts are not yet wired into the app.)
**Suggested fix:** In `_save`, write to a temp file and `os.replace`; use `with open(...)` throughout.

**Location:** `skills/b02-compliance-matrix/scripts/build_matrix.py:60`
**Category:** cleanliness | **Severity:** Low
**Issue:** The ImportError message instructs `pip install openpyxl --break-system-packages`.
**Why it matters:** Bakes an environment-hostile flag into user-facing guidance; can damage a system Python.
**Suggested fix:** Say `pip install openpyxl` (in a venv).

**Location:** `src/db.py:1015`
**Category:** cleanliness | **Severity:** Low
**Issue:** In the `__main__` block, `bids = conn.execute(...)` shadows the module-level `bids` Table.
**Why it matters:** Harmless where it sits, but a copy-paste into module scope would break the schema object silently.
**Suggested fix:** Rename the local to `n_bids` (and siblings to match).

## 4. Unused code

`web/package.json` is clean — all four dependencies and both devDependencies are used. The Python manifest issues (a *used-but-undeclared* package and a *conditionally-needed-but-unconditional* one) are filed under §7 because their impact is promotion-shaped.

**Location:** `skills/b05-submission-preflight/scripts/preflight.py:51`
**Category:** unused | **Severity:** Medium
**Issue:** `run(cfg, stage)` never uses the `stage` parameter — the docstring promises two-stage behaviour ("readiness" at T-5 vs "final" at T-1), but both stages execute identical checks.
**Why it matters:** A user running `--stage readiness` believes they got a lighter midpoint gate; the advertised two-stage discipline silently doesn't exist.
**Suggested fix:** Implement stage-conditional checks, or delete the `--stage` flag and the two-stage claim.

**Location:** `web/src/stages/PlanStage.jsx:8`
**Category:** unused | **Severity:** Low
**Issue:** `useMemo` is imported and never used.
**Why it matters:** Unused import.
**Suggested fix:** Drop it.

**Location:** `web/src/stages/TriageStage.jsx:103-104`
**Category:** unused | **Severity:** Low
**Issue:** `setField` handles a non-event argument (`… ? e.target.value : e`) but every call site passes it as an onChange handler; the raw-value branch is dead (complexity is set via `setForm` directly at line 288).
**Why it matters:** Dead branch complicating a one-liner.
**Suggested fix:** Simplify to `(e) => setForm((f) => ({ ...f, [k]: e.target.value }))`.

**Location:** `web/src/journey.js:198-202` with `web/src/styles.css:141-142,171-172`
**Category:** unused | **Severity:** Low
**Issue:** `STATE_MAP`'s `design` and `gap` entries are unreachable — every stage is `state: "live"` — so the `.s-design/.s-gap/.dot-design/.dot-gap` CSS is dead too.
**Why it matters:** Dead branches implying stages can still be un-built.
**Suggested fix:** Remove the entries and rules (or comment why they're kept if a new stage is genuinely planned).

**Location:** `skills/b06-clarification-management/scripts/clarification_log.py:23,43`
**Category:** unused | **Severity:** Low
**Issue:** `timezone` is imported and never used; the `strptime(s, "%Y-%m-%d")` fallback is unreachable (`fromisoformat` already parses everything it would accept).
**Why it matters:** Dead import + dead branch implying a parsing case that doesn't exist.
**Suggested fix:** Remove both.

**Location:** `skills/b02-compliance-matrix/scripts/build_matrix.py:74`
**Category:** unused | **Severity:** Low
**Issue:** `keys = [k for k, _ in COLUMNS]` is computed and returned (line 94) but the sole caller discards the return value.
**Why it matters:** Dead computation, misleading contract.
**Suggested fix:** Delete the variable and the return.

## 5. Orphaned code

**Location:** `web/src/stages/MockStage.jsx:8`, `web/src/stages/ScopeCard.jsx`
**Category:** orphaned | **Severity:** Medium
**Issue:** MockStage is imported by no file (verified — the only mention outside itself is the stale comment at `App.jsx:20`); ScopeCard is imported only by MockStage, so it is transitively orphaned. ScopeCard's markup is anyway duplicated inline in `StagePlaceholder.jsx:24-46`.
**Why it matters:** Two dead component files from the preview era, plus their dead CSS (below), with a live comment still pointing readers at them.
**Suggested fix:** Delete both files (and fix the App.jsx comment, §1).

**Location:** `skills/b01-bid-qualification/scripts/score.py:53-71`, `skills/b05-submission-preflight/scripts/preflight.py:96-98`, `skills/b06-clarification-management/scripts/clarification_log.py:25`, `skills/b07-outcome-learning/scripts/debrief.py:36-63`
**Category:** orphaned | **Severity:** Medium
**Issue:** Four skills scripts duplicate logic that has since been built for real in `src/`, with divergent vocabularies, and nothing in `src/` or `web/` references any of them: B01's `economics()` parallels `qualification.compute_bid_economics` (`src/qualification.py:71`); B05's gate parallels `clarification.resolve_preflight`/`PREFLIGHT_ITEMS` (`src/clarification.py:53,114`); B06's register uses statuses `open/drafting/with_reviewer/sent/closed` vs the app's `Open/Drafting/Submitted/Answered` (`src/clarification.py:36`); B07's `library_actions()` emits `promote/flag_do_not_reuse/review/refresh_before` vs the app's `["", "promote", "refresh", "retire"]` (`src/outcome.py:59,117`).
**Why it matters:** CLAUDE.md records the skills chain as "designed but not yet folded in", so their existence is sanctioned — but the duplication is now real drift: outputs of one implementation can't round-trip into the other's fields, and there are two competing registers for the founding-failure artifact.
**Suggested fix:** Declare `src/` canonical in each SKILL.md and align the skills' vocabularies to the `src/` enums now (cheap), so folding them in later is a wiring job, not a reconciliation.

**Location:** `web/src/App.jsx:99` with `web/src/journey.js:24-193`
**Category:** orphaned | **Severity:** Low
**Issue:** The `StagePlaceholder` fallback is unreachable — `VIEWS` covers all six `stage.component` values — which also strands the ~150 lines of `scope`/`asset` preview data in journey.js that only StagePlaceholder/ScopeCard render (including the stale `discovery/.env` strings, §1).
**Why it matters:** A large block of dead data shipped in the bundle.
**Suggested fix:** Either keep StagePlaceholder as a deliberate defensive seam (one comment) and delete the scope/asset fields, or remove all of it.

**Location:** `web/src/styles.css:211-230, 298-314`
**Category:** orphaned | **Severity:** Low
**Issue:** Rules used only by the orphaned MockStage/ScopeCard (`.preview-note`, `.screen*`, `.dots`, `.addr`, `.asset`) or by no JSX at all (`.mono`, `.reg`, `.reg-row`, `.cnote`, `.outcome-head`, `.res`) — verified by grep across web/src.
**Why it matters:** Dead CSS weight under a misleading "mock screen chrome" banner.
**Suggested fix:** Delete alongside the mock components.

**Location:** `docker-compose.yml:39-50`
**Category:** orphaned | **Severity:** Low
**Issue:** The `azurite` service is declared but nothing in the repo connects to it (no code references ports 10000-10002 or a storage connection string). Its own comment admits it's for Phase D/E.
**Why it matters:** `docker compose up -d` starts an unused emulator; scaffold shipped ahead of need — though it is honestly documented as such.
**Suggested fix:** Acceptable as documented scaffold; optionally comment the service out until Blob/queue work lands so `up -d` matches what's exercised.

## 6. Right-sized, not bloated

**Location:** `src/api.py:142-143` (pattern repeated at 258-259, 279-280, 417-418, 489-490, 514-515, 670-671, 684-685, 743-744, 761, 821-822, 904-905, 951, 987-988, 1000-1001, 1038-1039, 1108-1109, 1125, 1159-1160, 1174-1175, 1202-1203)
**Category:** right-sizing | **Severity:** High
**Issue:** Every endpoint hand-rolls `conn = db.connect(); db.init_db(conn); …; conn.close()`. Two consequences: (a) `init_db` runs `metadata.create_all` + an inspector query **on every request** — cheap-ish on SQLite, a set of extra network round-trips per request against Azure SQL; (b) there is no try/finally, so every error path leaks the connection — e.g. `_qualification_payload` raises 404 at `api.py:385` while the caller at `api.py:417-421` never reaches `conn.close()`; same shape in the plan/manage/responses/outcome GET/PUT handlers and the 409 gate at `api.py:857`. Against pooled Azure SQL, leaked connections on 404/409 paths exhaust the pool.
**Why it matters:** ~20 copies of boilerplate whose failure mode is invisible locally (SQLite + GC forgive it) and real on the promoted target.
**Suggested fix:** One FastAPI dependency: `def get_conn(): conn = db.connect(); try: yield conn; finally: conn.close()`, and run `init_db` once at startup (lifespan handler). This deletes ~60 lines and fixes the leak class wholesale.

**Location:** `src/db.py:559-602, 652-693, 705-746, 787-827, 866-907`
**Category:** right-sizing | **Severity:** Medium
**Issue:** `upsert_qualification`, `upsert_bid_plan`, `upsert_bid_manage`, `upsert_bid_responses`, `upsert_bid_outcome` are five near-identical ~40-line functions differing only in table, key column, field list, and JSON-field set. The four `get_*` twins and the INSERT-then-SELECT-id tail repeat likewise.
**Why it matters:** ~200 lines where ~50 would do; the SELECT/UPDATE/INSERT/re-SELECT choreography must be fixed in five places if it ever changes (e.g. for the §7 race).
**Suggested fix:** One `_upsert_one(conn, table, key_col, key_val, fields, field_list, json_fields)` plus thin named wrappers preserving the public API and docstrings.

**Location:** `web/src/api.js:87-94` (repeated at 116-123, 134-141, 166-173, 199-206, 235-242, 254-261, 286-293)
**Category:** right-sizing | **Severity:** Medium
**Issue:** The identical "parse `res.json().detail` else statusText, throw" block is copy-pasted eight times, while `sendJSON` (`api.js:299-314`) already implements exactly this and is used only by saveConfig/testConfig.
**Why it matters:** ~60 lines of duplication; any change to the error shape must be made in nine places.
**Suggested fix:** Move `sendJSON` above the stage helpers and route `runSearch`/`saveQualification`/`aiDraftQualification`/`saveBidPlan`/`saveBidManage`/`saveBidResponses`/`aiDraftResponse`/`saveBidOutcome` through it.

**Location:** `src/library.py:250-257, 275-304` (called from `src/api.py:908-913, 917-936, 962-964`)
**Category:** right-sizing | **Severity:** Medium
**Issue:** `LocalMirrorProvider.items()` re-parses the whole tracker workbook on every call, and `status()` calls `items()` just to count — so `/api/library` and `/api/bids/{id}/responses` each parse the xlsx **twice per request** (`status()` then `items()`).
**Why it matters:** Wasted work per request locally; behind the future GraphSharePoint provider the same call pattern becomes two full Graph fetches per request.
**Suggested fix:** Cache `items()` per provider instance (the API constructs a fresh provider per request, so an instance-level memo is safe), and have `status()` reuse it. An mtime-keyed module cache is the next step if profiling warrants.

**Location:** `src/contracts_finder_filter.py:79-161` (vs `src/find_tender_filter.py:94-180`)
**Category:** right-sizing | **Severity:** Low
**Issue:** `to_record`/`run`/`main` are near-verbatim twins across the two connectors (~120 duplicated lines), differing in endpoint, date param name, published-date field, URL derivation, and pacing.
**Why it matters:** The docstring documents the near-drop-in deliberately, and CF already reuses the CPV/region helpers — but the loop/upsert/summary skeleton is now duplicated too, and §2's tz bug shows the copies already diverging.
**Suggested fix:** Low priority: extract a shared `run_connector(fetch_page, to_record, window_param, pace)` skeleton when a third source lands (the registry's stated growth path); at minimum share `is_open` now (§2).

**Location:** `src/refresh_clean.py:94-104`
**Category:** right-sizing | **Severity:** Low
**Issue:** `clean()` fetches every row into Python and issues one UPDATE per row for flags that are pure functions of `deadline_date`/`last_seen_at`.
**Why it matters:** O(rows) round-trips — harmless at PoC scale, the slow path over the network on Azure SQL.
**Suggested fix:** Acceptable now; replace with 3-4 set-based UPDATEs when row counts grow.

**Location:** `skills/b04-response-drafter/scripts/check_answer.py:86`
**Category:** right-sizing | **Severity:** Low
**Issue:** Stale terms are matched with `whole_word=False`, so short tokens like `CCS` and `MEAT` match inside any word ("meatball").
**Why it matters:** False-positive flags force exit 1 and human triage on clean text.
**Suggested fix:** Match stale terms whole-word.

**Location:** `src/api.py:104-115` and `src/refresh_clean.py:55-66`
**Category:** right-sizing | **Severity:** Low
**Issue:** `_derive_open` and `_open_closed` are the same function twice; refresh_clean's comment acknowledges the mirror ("Mirrors api._derive_open so the persisted flag and the live API agree").
**Why it matters:** The comment is the only thing keeping them in agreement.
**Suggested fix:** Move one copy into `db.py` (both files already import it) and delete the other.

## 7. Local / Azure parity and migration readiness

What's *right*: backend selection (`DB_URL`, `src/db.py:427`), auth (`LOCAL_AUTH_BYPASS`/`AAD_*`, `src/auth.py`), CORS (`CORS_ALLOWED_ORIGINS`, `src/api.py:78-80`), library root (`BID_LIBRARY_ROOT`, `src/library.py:86`), LLM provider (`LLM_PROVIDER`), and the SPA (`VITE_AAD_*`, `VITE_API_BASE_URL`, `web/src/authConfig.js:16-18`, `web/src/api.js:11`) are all env-driven with sane local defaults. The Vite proxy target `http://127.0.0.1:8000` (`web/vite.config.js:11`) is dev-server-only config — checked, correct place, no finding. The findings below are the exceptions that would currently force code edits (or silent misbehaviour) on promotion.

**Location:** `web/src/api.js:77` (consumed at `web/src/stages/SearchStage.jsx:196`)
**Category:** parity | **Severity:** High
**Issue:** `exportUrl` returns a bare `/api/export?...` used as an `<a href>` — it bypasses both `resolveUrl` (no `VITE_API_BASE_URL` prefix) and `authHeader` (an anchor cannot carry a Bearer token). Every other API call goes through `apiFetch`.
**Why it matters:** On Azure (SPA on SWA, API on a separate origin, Entra enforced) the CSV export 404s against the SWA origin; with the prefix it would still 401. The one API call that is not config-switchable.
**Suggested fix:** Replace the anchor with a click handler that calls `apiFetch("/api/export?...")`, reads the blob, and triggers a download via `URL.createObjectURL`.

**Location:** `web/src/main.jsx:28-40`
**Category:** parity | **Severity:** High
**Issue:** The `initialize().then(handleRedirectPromise).then(render)` chain has no `.catch` — if MSAL init or the redirect drain rejects (bad config, AADSTS error, user cancels), `render()` never runs.
**Why it matters:** An Azure-only failure mode: the deployed SPA shows a permanently blank page with no message. It cannot occur locally (msalInstance is null there), so it will first appear in production.
**Suggested fix:** `.catch((e) => { console.error(e); render(); })` so the app still mounts and the sign-in gate/error is visible.

**Location:** `src/config.py:12,84-88` with `src/api.py:453-469` and `src/api.py:25-41`
**Category:** parity | **Severity:** High
**Issue:** The Settings write path persists LLM config by rewriting a `.env` file next to the code, and `_load_dotenv` reads it at import. On Azure App Service/Functions the deployment filesystem is read-only or ephemeral: the write either fails or silently evaporates on restart/scale-out, and app settings come from the platform, not a dotfile.
**Why it matters:** The Settings screen — an Admin-facing feature — silently stops persisting on the promoted target. This is a code change hiding behind a config feature.
**Suggested fix:** Introduce a settings-store seam now (env-file backend locally; App Configuration / Key Vault or platform app-settings backend on Azure, selected by env), or scope PUT `/api/config` to local mode and document that Azure config is platform-managed.

**Location:** `requirements.txt` (absent entry) vs `src/library.py:119,279`
**Category:** parity | **Severity:** High
**Issue:** `openpyxl` is imported by the library provider and the FOR006 master reader but is not declared in `requirements.txt`. On ImportError the code degrades: `master_template()` returns the generic fallback questions and `items()` returns `[]` — while `status()` still reports `available: True` (the tracker file exists) with `count: 0`.
**Why it matters:** Any fresh install — including the Azure host — silently loses the real bid library and real question master, and the UI shows a contradictory "connected, 0 items" state instead of an honest failure. It works on the dev machine only because openpyxl happens to be present.
**Suggested fix:** Add `openpyxl>=3.1` to `requirements.txt`; additionally make `status()` report `available: False` (with a reason) when the import fails.

**Location:** `src/db.py:463`
**Category:** parity | **Severity:** Medium
**Issue:** The column back-fill emits `ALTER TABLE opportunities ADD COLUMN {col} {type}` — T-SQL does not accept the `COLUMN` keyword (`ALTER TABLE … ADD col type`). The surrounding code (`_text_ddl`) explicitly targets mssql, so the intent is dual-dialect but the statement isn't.
**Why it matters:** The migration path for a pre-existing database fails on SQL Server/Azure SQL with a syntax error. Fresh databases are unaffected (create_all emits complete tables), which is exactly why this will surface late.
**Suggested fix:** `add_clause = f"ADD COLUMN" if conn.dialect == "sqlite" else "ADD"` (or emit the ALTER via SQLAlchemy DDL).

**Location:** `requirements.txt:10`
**Category:** parity | **Severity:** Medium
**Issue:** `pyodbc>=5.1` is unconditional, while its own comment says "only when DB_URL points at SQL Server / Azure SQL". pyodbc compiles against system ODBC headers; on a machine without unixODBC/Driver 18 the entire `pip install -r requirements.txt` fails — including for pure-SQLite local dev that never needs it.
**Why it matters:** The manifest contradicts its own comment and breaks the documented local quickstart on clean machines.
**Suggested fix:** Comment it out with instructions (matching how Azure OpenAI is handled at line 17), or split a `requirements-azure.txt` / extras.

**Location:** `src/auth.py:161-164`
**Category:** parity | **Severity:** Medium
**Issue:** `_identity_from_claims` reads the `groups` claim only. Entra omits `groups` and emits an overage marker (`hasgroups` / `_claim_names.groups`) when a user is in more than ~200 groups (JWT); the code treats that as "no groups" and silently assigns `AAD_DEFAULT_ROLE`.
**Why it matters:** On the real tenant, a group-overaged Admin silently becomes a User (or is rejected under strict gating) with no signal that group data was truncated — an Azure-only, user-specific failure that's very hard to diagnose from the 403.
**Suggested fix:** Detect the overage claim and fail loudly (403 with a "group overage — configure app-role assignment or Graph lookup" detail), and note the constraint in the module docstring; app roles are the long-term fix.

**Location:** `src/db.py:482-506` (same shape in every upsert, and INSERT-then-SELECT at 598-600, 636-638, 689-691, 742-744, 823-825, 903-905)
**Category:** parity | **Severity:** Low
**Issue:** All upserts are SELECT-then-INSERT/UPDATE with no transaction guard; concurrent writers can race to the unique constraint and one request 500s. The INSERT-then-re-SELECT-id pattern is dialect-portable but widens the window.
**Why it matters:** Unobservable in the single-user local PoC; possible under multi-worker/multi-instance Azure once real users arrive. Not a promotion blocker at current scale.
**Suggested fix:** Accept for now; when consolidating the upserts (§6), catch the unique-violation and retry as UPDATE, or use dialect upserts (`INSERT … ON CONFLICT` / `MERGE`).

**Location:** `src/db.py:429`
**Category:** parity | **Severity:** Low
**Issue:** `create_engine(url, future=True)` with no `pool_pre_ping`. Azure SQL drops idle connections (gateway idle timeout); a pooled stale connection surfaces as a mid-request operational error.
**Why it matters:** Intermittent 500s on the promoted target that never reproduce locally.
**Suggested fix:** `create_engine(url, future=True, pool_pre_ping=True)` — harmless for SQLite, standard for Azure SQL.

**Location:** `src/refresh_clean.py:135`
**Category:** parity | **Severity:** Low
**Issue:** The summary unconditionally prints `DB: {db.DB_PATH}` (the sqlite path) even when `DB_URL` pointed the run at SQL Server.
**Why it matters:** Misleading operational output during the migration — a refresh against the container reports a sqlite path.
**Suggested fix:** Print `os.environ.get("DB_URL") or db.DB_PATH`, redacting any password in the URL.

**Location:** `web/src/SettingsView.jsx:102`
**Category:** parity | **Severity:** Low
**Issue:** The key-field label is hard-coded "Anthropic API key" while the provider `<select>` above it is dynamic (Azure OpenAI is the planned second provider).
**Why it matters:** Wrong label the day the Azure OpenAI provider lands.
**Suggested fix:** Derive the label from the selected provider.

**Location:** `docker-compose.yml:10,20`
**Category:** parity | **Severity:** Low
**Issue:** Compose requires `MSSQL_SA_PASSWORD` from a repo-root `.env` (fails fast without it), but no committed example documents it — `src/.env.example` covers LLM/auth/CORS only, and no root `.env.example` exists. Two different `.env` files (root for compose, `src/` for the app) now coexist undocumented.
**Why it matters:** A fresh clone following "Password comes from .env" has no template naming the file or the var.
**Suggested fix:** Add a root `.env.example` with `MSSQL_SA_PASSWORD=` and a comment distinguishing it from `src/.env`.

## 8. Security (final gate)

**Verified clean (checked-negatives, so they aren't re-audited):** no secrets, keys, connection strings, or tokens in any tracked file or in git history (pattern scan over the full tree + `git log --diff-filter=A` for `.env` paths: nothing was ever committed); `.env`/`.env.*` are git-ignored with `!.env.example` (root `.gitignore:38-40`), and `src/bids.db*` likewise; the two `.env.example` files ship empty placeholders only; no real credentials disguised as emulator defaults — the only credential in the emulation stack is the operator-supplied `MSSQL_SA_PASSWORD`, required from an ignored `.env` (`docker-compose.yml:20`), and Azurite runs with its public well-known dev key implicitly (nothing committed); the LLM API key is write-only through the API (`config.current()` returns set/last4 only, `src/config.py:39-54`) and the SPA never receives it back; all SQL is parameterized with column names drawn from server-side whitelists (`db.COMMON_FIELDS` etc.), sort columns whitelisted (`api.py:219`); every JSON-blob write path normalises rows to known keys so clients can't smuggle fields (`api.py:826-842, 1006-1020, 1187-1192`); derived compliance numbers are recomputed server-side, never trusted from the client (`api.py:520-533, 1016`); auth fails closed when enabled-but-unconfigured (`auth.py:202-208`); `npm audit` reports 0 vulnerabilities (prod and dev); Python deps are floor-pinned to current majors.

**Location:** `src/config.py:68-88` (reachable via `src/api.py:466-468`)
**Category:** security | **Severity:** High — **blocking**
**Issue:** `upsert_env` writes `f"{key}={val}"` without validating the value. A value containing a newline defeats the `_ALLOWED_KEYS` whitelist: `PUT /api/config` with `api_key: "sk-x\nLOCAL_AUTH_BYPASS=1"` appends an attacker-chosen line to `.env`, which `_load_dotenv` faithfully loads on the next boot. Any env var the app trusts is settable this way — `LOCAL_AUTH_BYPASS=1` (disable auth for everyone, persistently), `AAD_GROUP_ROLE_MAP`, `DB_URL`, `LLM_PROVIDER`. The value is also pushed straight into `os.environ` at line 88.
**Why it matters:** The endpoint is Admin-gated, but "Admin can change the LLM key" must not imply "Admin can persistently disable authentication or repoint the database". Locally today (bypass on, single user) the impact is nil, which is exactly why it would ride into Azure unnoticed.
**Suggested fix:** Reject values containing `\r` or `\n` (and strip leading/trailing whitespace) in `upsert_env` before writing; optionally constrain each whitelisted key to its expected charset (provider/model against the option lists — already done in `put_config` — and the key to a printable single line).

**Location:** `docker-compose.yml:27-28` (also 45-48)
**Category:** security | **Severity:** Medium — **blocking (one-line fix)**
**Issue:** SQL Server's port is published as `"1433:1433"`, binding 0.0.0.0 — the sa-enabled dev database is reachable from the local network, not just the machine (Azurite likewise on 10000-10002).
**Why it matters:** A weak `MSSQL_SA_PASSWORD` plus an open LAN port is a real exposure, and this container will hold real (confidential-adjacent) bid-pipeline data during parity testing.
**Suggested fix:** Bind loopback only: `"127.0.0.1:1433:1433"` (and the same for the three Azurite ports).

**Location:** `web/src/authConfig.js:31`
**Category:** security | **Severity:** Medium
**Issue:** `cacheLocation: "localStorage"` persists MSAL token artefacts in localStorage — readable by any XSS, surviving browser restarts. MSAL's default is sessionStorage.
**Why it matters:** Enlarged token-theft blast radius once Entra is live. The `dangerouslySetInnerHTML` sites below make the XSS pairing non-theoretical.
**Suggested fix:** Use `sessionStorage` unless cross-tab SSO persistence was a deliberate requirement — if it was, record that in the comment.

**Location:** `src/auth.py:216-219` (also `src/api.py:340-344`)
**Category:** security | **Severity:** Low
**Issue:** The 401 detail interpolates the raw JWT exception (`f"Invalid or expired token: {exc}"`), and `/api/search` returns raw connector exception text (`f"{type(e).__name__}: {e}"`) to the client.
**Why it matters:** Token-validation internals and upstream error details (URLs, library messages) reach callers; standard practice is a generic client message with the specifics logged server-side.
**Suggested fix:** Return "Invalid or expired token." / "source fetch failed" and log the exception with the request id.

**Location:** `src/auth.py:218`
**Category:** security | **Severity:** Low
**Issue:** The bare `except Exception` around `_validate_token` also catches PyJWKClient network failures (JWKS endpoint unreachable), reporting a transient outage as a 401 "Invalid or expired token".
**Why it matters:** Misdiagnosis under an Entra/JWKS outage — every caller looks unauthenticated instead of the service looking degraded; also invites credential-flailing.
**Suggested fix:** Catch `jwt.PyJWTError` (and the JWKS client's fetch errors separately → 503) instead of `Exception`.

**Location:** `web/src/stages/StagePlaceholder.jsx:15,58`, `web/src/stages/ScopeCard.jsx:33,47`
**Category:** security | **Severity:** Low
**Issue:** Four `dangerouslySetInnerHTML` sites rendering `journey.js` scope/asset strings. Today the source is a static literal, so there is no injection path — but they are the app's only unsanitised HTML sinks.
**Why it matters:** If that text ever moves server-side (or the orphaned components are revived), these become XSS sinks feeding the localStorage token cache above.
**Suggested fix:** Deleting the orphaned components (§5) removes three of four; for StagePlaceholder, replace bold-tags-in-strings with JSX.

**Location:** `web/.gitignore:1-3`
**Category:** security | **Severity:** Low
**Issue:** `web/.gitignore` does not itself ignore `.env` — coverage comes only from the root `.gitignore` (verified via `git check-ignore`). `web/.env.example`'s claim that "`.env*` is git-ignored" is true today but fragile.
**Why it matters:** Extracting `web/` into its own repo (a plausible SWA direction) would silently start tracking `web/.env`.
**Suggested fix:** Add `.env`, `.env.*`, `!.env.example` to `web/.gitignore`.

---

## Summary

**Total findings: 62** — High 6 · Medium 17 · Low 39

| Category | Findings | High | Medium | Low |
|---|---|---|---|---|
| 1. Notes | 10 | — | 3 | 7 |
| 2. Consistency | 7 | — | 3 | 4 |
| 3. Cleanliness | 7 | — | — | 7 |
| 4. Unused | 6 | — | 1 | 5 |
| 5. Orphaned | 5 | — | 2 | 3 |
| 6. Right-sizing | 8 | 1 | 3 | 4 |
| 7. Parity | 12 | 4 | 3 | 5 |
| 8. Security | 7 | 1 | 2 | 4 |

The six High findings in one line each: per-request `init_db` + connection leaks on error paths (`api.py`); CSV export bypasses the auth/base-URL seam (`api.js:77`); no `.catch` on the MSAL boot chain (`main.jsx:28`); Settings persistence writes a `.env` beside the code (`config.py:84`); `openpyxl` used but undeclared (`requirements.txt`); newline injection through the Settings whitelist (`config.py:68-88`).

## Migration readiness

The architecture genuinely is config-switched: `DB_URL`, `LOCAL_AUTH_BYPASS`→`AAD_TENANT_ID`/`AAD_API_CLIENT_ID`/`AAD_GROUP_ROLE_MAP`, `CORS_ALLOWED_ORIGINS`, `LLM_PROVIDER`+keys, `BID_LIBRARY_ROOT`/`LIBRARY_PROVIDER`, and the SPA's `VITE_AAD_CLIENT_ID`/`VITE_AAD_TENANT_ID`/`VITE_AAD_API_SCOPE`/`VITE_API_BASE_URL` cover the promotion. **But the list is currently longer than configuration.** Code changes required before the move:

1. **`web/src/api.js:77`** — route the CSV export through `apiFetch` (401/404s on Azure otherwise).
2. **`web/src/main.jsx:28-40`** — add `.catch` to the MSAL boot chain (blank page on any Azure auth error otherwise).
3. **`src/config.py:84-88` / `PUT /api/config`** — settings persistence can't be a code-adjacent `.env` file on App Service/Functions; add a store seam or scope the feature to local.
4. **`requirements.txt`** — declare `openpyxl`; make `pyodbc` conditional/documented.
5. **`src/db.py:463`** — dialect-correct the `ALTER TABLE … ADD` back-fill (breaks on Azure SQL for pre-existing DBs).
6. **`src/api.py` connection lifecycle** — try/finally (or a yielding dependency) + startup-time `init_db`; leaked-on-error connections will exhaust the Azure SQL pool.
7. **`src/auth.py:161-164`** — handle the Entra groups-overage claim (silent role downgrade on the real tenant otherwise).
8. **`src/config.py:68-88`** — the security blocker below.

Two planned builds are correctly deferred behind seams and are *not* code-change violations: the `GraphSharePoint` library provider and the `AzureOpenAIProvider` (both documented, both drop in behind existing interfaces). Recommended alongside (not blocking): `pool_pre_ping` on the engine, sessionStorage for MSAL, and the stale `discovery/.env` copy which will misdirect users about where Azure config lives.

## Security verdict

**Not a clean pass — two blocking concerns, both small fixes:**

1. **Newline injection through `config.upsert_env`** (`src/config.py:68-88` via `PUT /api/config`) — an Admin-role caller can persist arbitrary environment variables, including `LOCAL_AUTH_BYPASS=1`, defeating the whitelist and, on Azure, the entire auth layer. Fix: reject control characters in values (a two-line change).
2. **`docker-compose.yml:27-28,45-48`** — sa-enabled SQL Server (and Azurite) published on 0.0.0.0, exposing the parity database (which will hold real bid-pipeline data) to the local network. Fix: bind `127.0.0.1`.

Everything else stands as advisory (localStorage token cache, error-detail leakage, JWKS-outage-as-401, the dormant `dangerouslySetInnerHTML` sinks, web-local `.gitignore` hardening). No secrets are committed anywhere in the tree or its history; dependency audits are clean. Clear the two items above and the security gate passes.

---

*Review completed by Claude Fable 5 (`claude-fable-5`).*
