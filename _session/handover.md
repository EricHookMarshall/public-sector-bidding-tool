# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-12` (session 23) — **Award-refresh diagnosed + G1 manual award capture shipped:**

- **The award-refresh 429s were the VPN's shared exit IP** — not our hammering. With the VPN off (residential
  IP), a 7-day probe walked **930 award notices with zero 429s**. The earlier RATE_LIMITED verdict is resolved.
- **BUT FWF's real NHS Barnsley win is not recoverable from public OCDS.** CH `11934102` verified correct
  (= "FUTURE WORK FORCE LIMITED"), yet no award to FWF appears in Contracts Finder's supplier search or web
  search under either spelling. Likely the notice named FWF without a CH id (so the GB-COH matcher correctly
  won't catch it), was sub-threshold, or FWF was a subcontractor. Full trail in `award_refresh_log.md`.
- **G1 manual award capture (new).** `POST /api/awards/manual` + `DELETE /api/awards/{id}` (Admin),
  `db.delete_award`. Stored under source `Internal record (manual)`, scheme `MANUAL` (never GB-COH), status
  `unverified` — honest provenance, and the OCDS refresh never overwrites it. `AwardsView` "Record a known
  award" form + `unverified` badge + Remove. **The NHS Barnsley record is seeded into bids.db.**
- **`make check` green: 103 backend tests** (was 98; +5 manual-awards, incl. a "survives OCDS refresh" guard),
  doc-consistency, vite build. Live-verified via uvicorn: POST → board=1, empty → 422, persisted to disk.

## Active task

**Next task — continue searching the APIs for the NHS Barnsley award's details.** The contract is real and now
recorded manually (unverified stub), but its public notice hasn't been located. Keep hunting via API search
(FTS/CF OCDS award feeds date-boxed to 3–4yr ago; buyer-name/keyword angles) to find the notice or enough
detail (title, date, value, contract term) to **enrich the seeded manual record**. If it genuinely isn't
published, that's a definitive finding — record it and move on. Coverage caveat: `own_awards._fetch_source`
caps at `max_pages=200` (~5 months of feed volume), so a full-window walk needs date-chunking to be exhaustive.

Also still open (unchanged): **click the 3 new views (G1/G2/G3) in a live browser** (API + build verified only).

## Blockers / prerequisites

- **Sell2Wales upstream is down**, not us — re-check periodically; no code fix possible on our side.
- **Empty *bid* pipeline is expected** (session-13 cleanse). Compliance register separate, seeded (19).
- **Live `GraphSharePoint`/`SharePointStore`** — no MS Graph here; unrelated to this session's work.
- **Azure:** FWF Intern subscription live; no resource group yet — Bicep/IaC (A1) is the real gap.

## Open decisions

1. **What next** — chase the Sell2Wales bulk-download fallback, do F1 remainder (eTendersNI/G-Cloud),
   or start on G1–G3. Not decided.
2. **Cert pin maintenance** — `src/certs/sectigo_dv_r36_intermediate.pem` is shared by PCS + Sell2Wales;
   refresh instructions live in the module docstrings + `src/certs/README.md` if either site changes CA.
3. Carried from session 19 (untouched this session): compliance write-gating, file-content expiry
   extraction — see `progress.md` session-19 entry.

## Auth quick-reference

Unchanged this session. Local dev default `LOCAL_AUTH_BYPASS=1`. Full config: `src/.env.example` +
`web/.env.example`.

## Start-of-session checklist

1. Read [`state.yaml`](state.yaml), [`CLAUDE.md`](../CLAUDE.md), this file, and [`todo.md`](todo.md).
2. Confirm DB: `python3 src/db.py` → `opportunities: 24` (unchanged this session — verification was GET-only).
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev`. Search now
   default-hides closed opps (toggle in the Filters panel) and shows a partial-results warning if a source
   (e.g. Sell2Wales) returns `incomplete`.
4. `git status` for the true commit state (this doc doesn't duplicate it).

## End-of-session checklist

1. Kill services: `pkill -f "uvicorn api:app"; pkill -f vite`.
2. Update [`state.yaml`](state.yaml) first, then **replace** the Status + Active task above (don't append).
3. **Prepend** a dated entry to [`progress.md`](progress.md) (most-recent-first).
4. Update the [`todo.md`](todo.md) active queue; commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
