# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-09` (session 9) — **Azure migration Phase B (DB portability) is DONE and dual-mode verified.**
`src/db.py` is ported off raw `sqlite3` to a **SQLAlchemy Core dual-mode shim**: SQLite locally by
default, Azure SQL / SQL Server when `DB_URL` is set — the same code, same call sites. Verified against a
**real local SQL Server 2022 container** (repurposed the already-pulled image; no download, no Azure
spend) with `IDENTICAL BEHAVIOUR: True` across both backends. The journey remains feature-complete (all
six stages, session 7); this session was infra + the db.py port only, no stage/UI logic changed.

**How the port works (surgical — only `src/db.py` changed, zero of the 8 caller files):** `db.connect()`
now returns a thin adapter over a SQLAlchemy Core connection. Both `sqlite3` and `pyodbc` use `?` (qmark)
placeholders, so every existing `conn.execute("… ?", params).fetchone()["col"]` call site works
untouched via `exec_driver_sql`. The schema is declared once as SQLAlchemy metadata → `create_all()`
emits the right DDL per dialect (`AUTOINCREMENT` on SQLite / `IDENTITY` on SQL Server), replacing the old
hand-written `executescript`. Rows come back as a dict-like `_Row` that mirrors `sqlite3.Row`
(`row["col"]`, `row[0]`, `.keys()`).

**Two real dialect bugs the live engine caught** (both would have passed a SQLite-only test): (1)
`ORDER BY (deadline_date IS NULL)` — valid in SQLite, **syntax error in T-SQL** — rewritten to the
portable `CASE WHEN … THEN 1 ELSE 0 END` in all 4 list queries; (2) `NVARCHAR(MAX)` **can't be a
unique-key column** in SQL Server — bounded `source`/`ocid` to `Unicode(400)` (still TEXT on SQLite, no
behaviour change).

## Verified this session (all live, honest)

- **`db.py` on both backends → `IDENTICAL BEHAVIOUR: True`**, 4/4 checks PASS: insert/update semantics,
  `£`/`✓` unicode round-trip through NVARCHAR, JSON-field decode, JOIN + rewritten ORDER BY. (Test rig:
  `scratchpad/verify_dualmode.py` — throwaway sqlite file + the live container; not committed.)
- **Default sqlite path intact** — `python3 src/db.py` → the real 21 opportunities / 3 bids / etc.
  (cleaned up the VerifyTest rows the test leaked into `bids.db`).
- **App serves through the adapter** — `uvicorn` up, `/api/plan/board` (`count:3`, real bids) and
  `/api/opportunities` (21 rows) both 200.
- **Follow-on audit**: api.py's runtime SQL is fully portable (no LIMIT/OFFSET, no IS-NULL ordering).
  Only remaining sqlite-ism = `LIMIT 1` in the **dev-only `seed_*_demo.py`** scripts (4 of them) — not on
  the Azure path; would need `OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY` for SQL Server. Deferred.

## Active task

**Phase B done — pick the next Azure-migration step (user's call), roughly in priority order:**

1. **Phase C — auth** per `docs/design/azure-target.md`: Entra ID / MSAL sign-in on the SPA + PyJWT/JWKS
   validation on the API (closes the "no auth anywhere" gap, the #1 gap). Buildable + verifiable locally
   against a dev-tenant app reg + a `LOCAL_AUTH_BYPASS` shim — no Azure subscription needed.
2. **Finish Phase B tail** — port the 4 `seed_*_demo.py` `LIMIT 1` queries to portable OFFSET/FETCH so the
   seeders also run on SQL Server (they only run locally today, so low priority).
3. **User browser walk of Complete + Learn** — still open from session 7; verified server-side only.
4. **Deferred externals** — Azure OpenAI provider; live `GraphSharePoint`; HubSpot.

## Local SQL Server parity stack (new this session)

- **`docker-compose.yml`** (repo root, new) — `db` = SQL Server **2022** (`mcr.microsoft.com/mssql/server`,
  the image already local; identical `mssql` dialect to Azure SQL, so it verifies the whole port —
  bump to `:2025-latest` only when the native `VECTOR` type is needed for retrieval Option B) + `azurite`
  scaffold (Blob/Queue/Table, for later Phase D/E; **not** a SQL emulator). Run `db` alone for Phase B.
- **Memory caps matter**: without them the container `Exited (137)` (OOM/SIGKILL) under Rosetta x64
  emulation. Set `MSSQL_MEMORY_LIMIT_MB=2048` + `mem_limit: 3g` (Docker VM is 7.8 GB). Now boots healthy.
- **Runtime**: x64 image via Docker Desktop **Rosetta** (already enabled). Container reachable on
  `localhost:1433`; SA password in gitignored root `.env` (`MSSQL_SA_PASSWORD`, local dev only).
- **Deps**: `pip install pyodbc` + Homebrew `unixodbc` + `msodbcsql18` (needs `brew trust
  microsoft/mssql-release` first — the newer untrusted-tap gate). `requirements.txt` now lists
  `SQLAlchemy` (always) + `pyodbc` (SQL Server/Azure only). pyodbc 5.3.0, driver "ODBC Driver 18".
- Local SQL Server URL used for verify: `mssql+pyodbc://sa:<pw>@localhost:1433/bids?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes` (password `!` → `%21`).
- **Container may still be running** — `docker compose down` to stop (keeps the volume).

## Surfaced / parked threads

- **`seed_*_demo.py` use `LIMIT 1`** — sqlite-only; needs OFFSET/FETCH for SQL Server (Phase B tail, low
  priority — seeders are dev-local).
- **Connection lifecycle** — api.py opens a `db.connect()` per request and mostly doesn't close it (same
  as the old sqlite code). Fine for a local single-user PoC; revisit pooling before real multi-user cloud.
- **`web/src/stages/MockStage.jsx` + `StagePlaceholder.jsx` are dead code** — every stage is real. Safe to delete.
- **AI-draft provenance isn't persisted** — win-themes/evidence shown in UI but not saved with the answer.
- **`question_ref` repeats across lots** in the FOR006 master — matrix rows keyed by index, not qref. Don't reintroduce qref as a key.
- **`GraphSharePoint` provider** — not built (no MS Graph here); slots into `library.get_provider()`. **Azure OpenAI provider** — skeleton in `src/llm.py`, not implemented.
- **Team capacity default (25 days, `src/bidplan.py`)** — placeholder, not a real FWF number.

## Open decisions

1. **What next** — Phase C (auth), finish the Phase B seeder tail, browser-review Complete/Learn, or polish. Not decided.
2. **AI-draft provenance persistence** — save the evidence/win-themes with the answer?
3. **Azure OpenAI / GraphSharePoint timing** — build when the respective access is provisioned (Azure migration Phase E).

Settled this session (session 9): **Phase B done** — `db.py` dual-mode via SQLAlchemy Core, verified on a
local SQL Server 2022 container; repurpose the existing 2022 image (not 2025) until `VECTOR` is needed;
Azurite is Blob/Queue/Table only, **not** a SQL emulator (it's scaffolded for later, not used by Phase B).

Settled session 8, unchanged: **Azure/SPA target design** — clone TalentGrow's blueprint (SWA + Functions
Flex + Azure SQL free + Managed Identity everywhere, no Key Vault); Entra ID/MSAL sign-in; `docs/design/azure-target.md` is the plan of record.

Settled session 7, unchanged: journey feature-complete, all 6 stages real; Complete via LocalMirror; Learn built; browser review of stages 1–3/5 done.

Settled earlier, unchanged: Manage (Stage 5) FOR003 + pre-flight gate; flat repo structure; Plan real;
Triage + AI + Settings; six-stage journey shape + visual style approved; library-provider seam; stack =
FastAPI + (now dual-mode) SQLAlchemy/SQLite + React/Vite; shared bid record from `docs/design/data-model.md`.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. Confirm DB state: `python3 src/db.py` → `opportunities: 21`, `qualifications: 3`, `bids: 3`,
   `bid_plans: 3`, `bid_manage: 3`, `bid_responses: 1`, `bid_outcomes: 2` — unless prior testing left
   different rows; check before assuming.
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev` →
   `http://localhost:5173`. Seeders: `seed_plan_demo.py` / `seed_manage_demo.py` / `seed_complete_demo.py`
   / `seed_learn_demo.py` (each takes `--clear`).
4. **Dual-mode DB**: default = local sqlite (`src/bids.db`), no setup. To exercise SQL Server: `docker
   compose up -d --wait db`, then set `DB_URL` (see the SQL Server URL above). `pyodbc` + system
   `msodbcsql18` required for that path only.
5. Complete's library reads the real gitignored export at `knowledge/SharePoint Folder/Bids/`; absent =
   "library not connected" (honest, not a bug). `src/.env` holds the Anthropic key for AI drafting.
6. Azure migration: `docs/design/azure-target.md` is the plan of record; Phase B (DB) is done, Phase C
   (auth) is next.

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`). Optionally `docker compose down`.
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
