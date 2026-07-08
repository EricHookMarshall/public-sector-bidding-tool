# Handover — hot state

> **Read first when resuming.** A one-page snapshot of *current* work. Keep it to a page —
> **replace it, don't append.** Cold history (the dated log, past decisions) lives in
> [`progress.md`](progress.md); reach it on demand, it does not auto-load.

## Status

`2026-07-08` — **Phase 0 complete: consolidated into one connected git repo, facts verified,
project scaffold in place.** The three loose folders are now `discovery/` (working PoC),
`skills/` (B00–B07 bid chain), `knowledge/` (context + reference). Pushed to
`github.com/EricHookMarshall/public-sector-bidding-tool` (`main`). This session also added the
top-level `CLAUDE.md`, this `_session/` triad, and the `/resume-prompt` + `/end-session` skills.

## Active task

**Phase 1 — wire search → triage.** Define one shared record so a discovery opportunity can be
promoted into a bid/no-bid decision (discovery ↔ skills B01 qualification). Approach is
**breadth-first** (thin end-to-end) per the user's steer. Not started.

## Surfaced / parked threads

- **FWF strategy docs still carry .docx export artefacts** (`knowledge/01–03`): stray `*title*`
  lines, `Page  of` footers, pipe-table headers. Readable but messy — light cleanup pass optional.
- **Planning layer (Phase 2)** exists nowhere yet — the highest-value novel piece ("which bids, when, capacity").
- **Third+ discovery source** — `discovery/sources.py` registry makes it a one-connector add (Scotland / Wales / TED).

## Open decisions

1. **Product form** — grow the discovery UI into the whole journey, OR keep discovery separate and
   run the bid workspace via skills + SharePoint? Shapes all downstream architecture.
2. **SharePoint timing** — Phase 3 (AI pre-fill) is blocked on real MS Graph credentials; this
   environment only has a Google Drive connector. Until then pre-fill can only be prototyped on samples.

Settled: breadth-first sequencing; one connected repo with clean structure; facts verified
(`knowledge/VERIFIED_FACTS.md`), incl. correction that RM6263 is expired → assess DOS7; RM6190 TS4 is a live candidate.

## Start-of-session checklist

1. Read [CLAUDE.md](../CLAUDE.md), this file, and [todo.md](todo.md).
2. Confirm repo state: `git -C .. status` (clean?) and `git -C .. log --oneline -3`.
3. (Optional) Spin up discovery to sanity-check the search stage — see `discovery/CLAUDE.md`.

## End-of-session checklist

1. Kill any running services (`pkill -f "uvicorn api:app"; pkill -f vite`).
2. **Replace** the Status + Active task above with the new current state — don't append.
3. **Prepend** a dated entry to [progress.md](progress.md) (most-recent-first).
4. Update the [todo.md](todo.md) active queue.
5. Commit only if the user asks. If committing on `main`, that's fine for this repo's solo bootstrap phase.

Run `/end-session` to do steps 1–4 guided.
