# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-12` (session 20) — **Started F1 (more search sources) at the user's request, plus three new
requirements the user asked to have checked/recorded.** Two connectors shipped this session:

- **Public Contracts Scotland** (`src/public_contracts_scotland.py`) — the 3rd search connector, live-verified:
  a `--no-db` run returned real, relevant Scottish IT opportunities. TLS note below.
- **Sell2Wales** (`src/sell2wales.py`) — the 4th, built as a **resilient per-partition adapter** after
  discovering its upstream `/Notices` list API is currently **broken server-side** (HTTP 500 "nvarchar to
  float" SQL fault on every query, including Sell2Wales's own documented example — confirmed their bug, not
  ours, by cross-testing against PCS on the same platform). The connector partitions by month×noticeType,
  retries once with backoff, records a structured error per poisoned partition, and **never aborts the whole
  source** — live it currently records 4 partition failures and ingests 0, but will resume ingesting the
  moment Sell2Wales fixes their endpoint, with zero code change needed.
- **TLS, both connectors:** PCS and Sell2Wales (same Proactis platform, same CA) omit their intermediate
  cert, so no default trust store can verify them. Rather than disabling verification, the **public Sectigo
  intermediate is pinned** (`src/certs/sectigo_dv_r36_intermediate.pem` — not a secret, safe to commit; valid
  to 2036). Proven: a default context REJECTS the connection, the pinned context ACCEPTS with
  `verify_mode=CERT_REQUIRED` — full verification, no `verify=False` anywhere.
- **`make check` green: 74 backend tests** (63 baseline + 6 PCS + 5 Sell2Wales), doc-consistency, vite build.
  `bids.db` untouched (24 opps) — both connectors proved with `--no-db`, not by mutating the tracked baseline.

Also this session: checked 4 user-proposed requirements against the codebase (none existed) and recorded
them as scoped backlog items — **F6** (Search: hide closed opps by default unless triaged) and **G1–G3**
(GCA/frameworks intelligence: pull FWF's own awards via Find a Tender OCDS award packages, a framework-radar
view, an in-app how-to-supply reference). Full detail in `todo.md`.

⚠️ **Not committed.** All of this session's work is on disk only (5 modified + 6 new files, listed below).

## Active task

**No task in flight — F1's first two sources are done; next step is the user's call.** Natural follow-ons
(full detail in `todo.md` → F-series):

1. **Commit this session's work** (your call — nothing staged yet).
2. **Surface `partition_errors`/`incomplete`** in the search run-summary — `sell2wales.run()` already returns
   them; `api.py`'s `/api/search` currently drops them on the floor, so a live Wales outage is invisible to
   the user today. Small, high-value.
3. **Sell2Wales bulk-download fallback** — their official monthly JSON/XML/CSV, but it's behind an
   aspx-postback form (`__VIEWSTATE` present), not a clean GET. Bigger lift.
4. **F1 remainder** — eTendersNI (different platform, Jaggaer), G-Cloud as a source.
5. Or pick up **F6** / **G1–G3** instead (new user reqs, not yet built).

## Blockers / prerequisites

- **Sell2Wales upstream is down**, not us — re-check periodically; no code fix possible on our side.
- **Empty *bid* pipeline is expected** (session-13 cleanse). Compliance register separate, seeded (19).
- **Live `GraphSharePoint`/`SharePointStore`** — no MS Graph here; unrelated to this session's work.
- **Azure:** FWF Intern subscription live; no resource group yet — Bicep/IaC (A1) is the real gap.

## Open decisions

1. **What next** — commit F1, surface partition errors, chase the bulk-download fallback, or start on
   F6/G1–G3. Not decided.
2. **Cert pin maintenance** — `src/certs/sectigo_dv_r36_intermediate.pem` is shared by PCS + Sell2Wales;
   refresh instructions live in the module docstrings + `src/certs/README.md` if either site changes CA.
3. Carried from session 19 (untouched this session): compliance write-gating, file-content expiry
   extraction — see `progress.md` session-19 entry.

## Auth quick-reference

Unchanged this session. Local dev default `LOCAL_AUTH_BYPASS=1`. Full config: `src/.env.example` +
`web/.env.example`.

## Start-of-session checklist

1. Read [`state.yaml`](state.yaml), [`CLAUDE.md`](../CLAUDE.md), this file, and [`todo.md`](todo.md).
2. Confirm DB: `python3 src/db.py` → `opportunities: 24` (unchanged — PCS/Sell2Wales proved with `--no-db`).
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev`. The Search
   panel's source checkboxes now include Public Contracts Scotland + Sell2Wales automatically (registry-driven).
4. `git status` will show 5 modified + 6 new files from this session, uncommitted.

## End-of-session checklist

1. Kill services: `pkill -f "uvicorn api:app"; pkill -f vite`.
2. Update [`state.yaml`](state.yaml) first, then **replace** the Status + Active task above (don't append).
3. **Prepend** a dated entry to [`progress.md`](progress.md) (most-recent-first).
4. Update the [`todo.md`](todo.md) active queue; commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
