# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work — Status, the single
> Active task, blockers, open decisions. **Replace it, don't append.** Keep it under ~80 lines;
> if it grows, the overflow belongs in [`progress.md`](progress.md) (cold dated log, on demand).
> Machine-readable version: [`state.yaml`](state.yaml). Authority order lives in [`CLAUDE.md`](../CLAUDE.md).

## Status

`2026-07-12` (session 19) — **Shipped the C-series "Compliance & Renewals" view — the highest
founding-purpose payoff.** The tool now has an **org-level, app-OWNED compliance-asset register**: every
credential / policy / framework and its renewal status in one screen, lifting the "expired cert at bid time"
failure (the reason this project exists) out of per-bid burial. Key design call the user reframed mid-scope:
this is the *system of record*, **not** a read of the bid library — assets are **uploaded** (bytes → a
gitignored store) or registered as references, are **updatable**, and expiry is **derived** to drive alerts.

Built (all live-verified against the real `bids.db` + a running server):
- **`src/db.py`** — new `compliance_assets` table + CRUD helpers (`insert/get/list/update/delete` +
  idempotent `seed_compliance_assets`). Expiry STATUS is never stored — derived live (facts decay).
- **`src/compliance_store.py`** (new) — the file-store seam, mirroring `library.py`: **`LocalFileStore`**
  now (gitignored `src/compliance_store/`), **`SharePointStore`** later behind the same interface. Stored
  paths are generated (uuid+ext), never the client filename → **path traversal blocked** (verified).
- **`src/compliance.py`** (new) — expiry derivation (reuses `library.py` date maths), board sort
  (urgency-first), summary counts, and seed-from-library.
- **`src/api.py`** — `GET /api/compliance/board|reference`, `POST /assets` (multipart upload),
  `PUT /assets/{id}`, `DELETE /assets/{id}`, `GET /assets/{id}/file` (attachment-only), `POST
  /import-from-library`; startup one-time seed; **CORS gained DELETE**.
- **Frontend** — new top-level **`ComplianceView.jsx`** (`#compliance` route, open to all — TopBar "🛡
  Compliance" button), `api.js` helpers, KPI banner + urgency-sorted register + upload/edit/delete.
- **`python-multipart`** added to `requirements.txt`; `src/compliance_store/` added to `.gitignore`.

Verified: **`make check` green — 63 backend tests (+10 new) + doc-consistency + vite build clean.** Live on
real `bids.db`: startup **seeded 19 assets from the real bid library, incl. the EXPIRED ISO (2025-10-31)**;
upload → **expiry auto-mined from notes** → attachment download → PUT update → `422` on bad type/date →
delete removes the file → `404`. **DB now carries a `compliance_assets` table (19 rows).**

⚠️ **Not committed.** All changes are on disk only (7 modified + 4 new files). Commit when you're ready —
I did not, since you didn't ask. ⚠️ **Not yet clicked in a live browser** this session (API + build verified;
the UI is build-clean but I couldn't drive a browser here — worth a manual look).

## Active task

**No task in flight.** C-series C3 MVP is shipped. Natural follow-ons (in `state.yaml → deferred`):
1. **Commit** this session's work (your call).
2. **C-series phase 2** — extract expiry from uploaded **PDF/docx bytes** (today it's mined from the
   name/notes text only); **C4** framework/contract membership tracker (category exists, no data source yet);
   file-replace in the edit form.
3. **Structural refactors** — R1 (api.py is now ~1.9k lines — split routers, compliance is a clean seam to
   carve first), R3 connector dedupe.
4. **S5 key rotation** — your action (rotate the Anthropic key in `src/.env`).

## Blockers / prerequisites

- **Empty *bid* pipeline is expected** (session-13 cleanse) — Plan/Manage/Complete/Learn read 0 bids until an
  opp is triaged to Go. The new **compliance register is separate** and now seeded (19).
- **Live `GraphSharePoint` / `SharePointStore`** — no MS Graph here; Complete uses `LocalMirror`, Compliance
  uses `LocalFileStore`. Both drop the live provider in behind the seam later. Don't fake either.
- **Azure correction:** the **FWF Intern subscription IS live** (verified `az account list` 2026-07-12) but
  **no resource group for this app exists yet**. The old `needs_subscription` note is stale; Azure Phase D's
  real gap is now Bicep/IaC (A1) + creating the RG, not access.

## Open decisions

1. **What next** — commit + C4/phase-2 compliance, vs R1 router split (compliance makes a clean first carve),
   vs Azure IaC now that the sub is confirmed. Not decided.
2. **Compliance write-gating** — asset create/update/delete are open to any authenticated user (like bid
   saves), not Admin-only. Revisit if compliance should be ops-restricted.
3. **File-content expiry extraction** — parse dates out of the PDF/docx itself (needs a parser dep), vs the
   current text-field mining. Deferred.

## Auth quick-reference

Local dev default is `LOCAL_AUTH_BYPASS=1` (API unauthenticated, synthetic Admin) + `VITE_AAD_*` unset →
runs like sessions 1–9. To exercise role-gating add `LOCAL_AUTH_ROLE=User`. Full config: `src/.env.example`
(API) + `web/.env.example` (SPA). New env knobs: `COMPLIANCE_STORE` (default `local_file`),
`COMPLIANCE_STORE_ROOT` (override the store dir, used by tests).

## Start-of-session checklist

1. Read [`state.yaml`](state.yaml), [`CLAUDE.md`](../CLAUDE.md), this file, and [`todo.md`](todo.md).
2. Confirm DB: `python3 src/db.py` → `opportunities: 24`, empty *bid* pipeline; the compliance register holds
   19 seeded assets (separate from the bid pipeline).
3. Spin up: `uvicorn api:app --app-dir src --reload --port 8000` + `cd web && npm run dev` → <http://localhost:5173>.
   The **"🛡 Compliance"** button (top bar) opens the new `#compliance` view.
4. Complete's library reads the gitignored export; Compliance's files live in gitignored `src/compliance_store/`.

## End-of-session checklist

1. Kill services: `pkill -f "uvicorn api:app"; pkill -f vite`.
2. Update [`state.yaml`](state.yaml) first, then **replace** the Status + Active task above (don't append).
3. **Prepend** a dated entry to [`progress.md`](progress.md) (most-recent-first).
4. Update the [`todo.md`](todo.md) active queue; commit only if the user asks.

Run `/end-session` to do steps 1–4 guided.
