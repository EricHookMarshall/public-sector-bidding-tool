# TODO

> Active and in-flight work only. Completed items are cold history — see `_session/progress.md`
> (most-recent-first), which holds the full dated retrospective for each pass.

## Active queue

**Full PoC is COMPLETE — all success criteria met, all user-requested UI features built.**
No blocking work remains.

## Surfaced / open

- [ ] **`.gitignore`** — `bids.db` and `web/node_modules/` should be gitignored. The repo exists; easy first commit.
- [ ] **Cross-source dedupe** — `(source, ocid)` dedupes within a source. Cross-source matching (same notice on FTS and CF) is not yet handled. Low priority given value-band split.

## Parked / optional polish

- [ ] **CPV label badge on cards** — `cpv_catalog.py` now has descriptions; could show a labelled chip on the result card (e.g. `72000000 — IT services…`) instead of the raw code.
- [ ] **Third API source** — `sources.py` registry makes it a one-connector-plus-one-line add. Candidates: TED (EU above-threshold), Scotland eTender, Crown Commercial Service.
- [ ] **Lifecycle badge on cards** — `stale`/`closed` lifecycle flag is surfaced in the filter + detail view but not on the card itself.
- [ ] **CPV scope widen** — currently IT/software only. Widen `TARGET_CPV` + `cpv_catalog.py` for other sectors.
- [ ] **Make connectors faster** — CF takes 10–30s due to rate limiting. A background job / progress stream would improve UX for live searches.

## Done

Completed items are cold history — see `_session/progress.md` (most-recent-first).

- [x] **Bootstrap: brief → CLAUDE.md → session scaffold** (2026-06-29).
- [x] **Pulled in + adapted `end-session` and `resume-prompt` skills** (2026-06-29).
- [x] **SQLite schema + persistence** — `db.py` built; `find_tender_filter.py` refactored to upsert into `bids.db`. Full ~18-field schema; `(source, ocid)` upsert key (2026-06-29).
- [x] **Settled second source** — Contracts Finder (OCDS, lower-value UK) (2026-06-29).
- [x] **Contracts Finder connector** — `contracts_finder_filter.py`; 2 open IT notices upserted; DB 14 rows across 2 sources. **Success criteria met (>1 source)** (2026-06-29).
- [x] **FastAPI JSON API (`api.py`)** — `/api/meta`, `/api/opportunities`, `/api/opportunities/{id}` (2026-06-29).
- [x] **React/Vite frontend (`web/`)** — filter sidebar, opportunity cards, detail modal (2026-06-29).
- [x] **Refresh / cleanup script** — `refresh_clean.py`: re-runs connectors + writes persisted `lifecycle` flag (open/closed/unknown/stale). **Success criteria fully met** (2026-06-29).
- [x] **Connector refactor** — `run(cpv_codes, stage, open_only, date range)` in both connectors; CLI unchanged (2026-06-29).
- [x] **Source registry** — `sources.py`; registry-driven source toggles (2026-06-29).
- [x] **Region glossary** — `regions.py`; 63-code NUTS/ITL → plain English, prefix fallback (2026-06-29).
- [x] **CPV catalogue** — `cpv_catalog.py`; 63 IT/digital codes with descriptions; dropdown in UI (2026-06-29).
- [x] **`POST /api/search`** — live fan-out to selected connectors with CPV/stage/date params (2026-06-29).
- [x] **`GET /api/export`** — CSV download mirroring current filters, 22 fields (2026-06-29).
- [x] **UI: live search panel** — source checkboxes, stage, open-only toggle, date window, CPV chip editor + catalogue dropdown (2026-06-29).
- [x] **UI: description on cards, region labels, export button** (2026-06-29).
- [x] **Bug fix: `cpv_catalog` crash** — was read as `opts.cpv_catalog`; corrected to `meta?.cpv_catalog` (2026-06-29).
