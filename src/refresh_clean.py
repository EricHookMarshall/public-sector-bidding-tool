#!/usr/bin/env python3
"""
Refresh + cleanup pass for the Public Sector Bidding PoC.

Keeps bids.db lean and fresh now that two sources feed it (hard rule: store only
data useful for acting on *open* opportunities; no long-term historical archive).

Two phases:

  1. REFRESH — re-run each connector (Find a Tender, Contracts Finder) so current
     open notices are re-upserted, last_seen_at is bumped, and source_runs is
     re-stamped. Connectors are invoked as-is (subprocess), so their CPV scope,
     pagination and CF's own 429 self-throttling all apply unchanged — single
     source of truth, nothing duplicated here.

  2. CLEANUP (flag, don't delete) — write a persisted `lifecycle` flag on every
     row:
       - open    : tenderPeriod deadline still in the future
       - closed  : deadline has passed
       - unknown : no/invalid deadline
       - stale   : the row's source was refreshed this run but the row was NOT
                   seen (last_seen_at predates this run) — i.e. it dropped off the
                   feed (withdrawn / closed-and-removed). This is the one signal
                   the API can't derive live from deadline_date.

We FLAG rather than DELETE (project decision): the brief favours a lean DB, but
the API already derives open/closed live, so a non-destructive flag keeps the UI
able to show/hide closed + stale rows without losing provenance. Nothing is
removed; bids.db stays fully inspectable.

Staleness is only judged for sources that refreshed *successfully* this run — a
failed or rate-limited fetch must never wrongly mark its rows stale.

Run:
  python3 refresh_clean.py [days_back]            # default 120: refresh both, then flag
  python3 refresh_clean.py [days_back] --no-fetch # skip the network refresh; re-flag only
"""
import datetime
import os
import subprocess
import sys

import db

HERE = os.path.dirname(os.path.abspath(__file__))

# (source name as stored in the DB, connector script). Source names MUST match
# the SOURCE_NAME each connector writes, so staleness is scoped correctly.
CONNECTORS = [
    ("Find a Tender", "find_tender_filter.py"),
    ("Contracts Finder", "contracts_finder_filter.py"),
]


def _open_closed(deadline, now):
    """open / closed / unknown from a bid deadline vs `now` (UTC). Thin alias over
    db.derive_lifecycle (the shared source api._derive_open also uses) so the
    persisted flag and the live API agree. `now` is captured once per batch."""
    return db.derive_lifecycle(deadline, now)


def refresh(days):
    """Re-run each connector in turn. Returns the set of source names that
    refreshed successfully (exit 0) — only those are trusted for staleness."""
    refreshed = set()
    for name, script in CONNECTORS:
        print(f"\n=== Refreshing {name}  ({script}, days_back={days}) ===")
        result = subprocess.run([sys.executable, os.path.join(HERE, script), str(days)],
                                cwd=HERE)
        if result.returncode == 0:
            refreshed.add(name)
        else:
            print(f"  ! {name} connector exited {result.returncode}; its rows "
                  f"will NOT be flagged stale this run.")
    return refreshed


def clean(conn, refreshed, run_start):
    """Write the lifecycle flag on every row. `run_start` is the ISO timestamp
    captured before the refresh; rows whose source refreshed but whose
    last_seen_at predates it weren't re-seen → stale."""
    now = datetime.datetime.now(datetime.timezone.utc)
    rows = conn.execute(
        "SELECT id, source, deadline_date, last_seen_at FROM opportunities"
    ).fetchall()

    counts = {"open": 0, "closed": 0, "unknown": 0, "stale": 0}
    for row in rows:
        life = _open_closed(row["deadline_date"], now)
        seen_this_run = (row["last_seen_at"] or "") >= run_start
        if row["source"] in refreshed and not seen_this_run:
            life = "stale"
        counts[life] += 1
        conn.execute(
            "UPDATE opportunities SET lifecycle = ? WHERE id = ?", (life, row["id"])
        )
    conn.commit()
    return counts


def main():
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    no_fetch = "--no-fetch" in sys.argv
    days = int(positional[0]) if positional else 120

    # Capture BEFORE refreshing: connector upserts stamp last_seen_at = now,
    # which is strictly after this. Rows not re-seen keep an older stamp.
    run_start = db.now_iso()

    if no_fetch:
        print("Skipping connector refresh (--no-fetch); re-flagging existing rows only.")
        print("Note: with no refresh, staleness is not judged (no source trusted).")
        refreshed = set()
    else:
        refreshed = refresh(days)

    conn = db.connect()
    db.init_db(conn)
    counts = clean(conn, refreshed, run_start)
    total, by_source = db.counts(conn)
    conn.close()

    print("\n=== Cleanup summary ===")
    print(f"Refreshed sources : {', '.join(sorted(refreshed)) or '(none)'}")
    print(f"Lifecycle flags   : open={counts['open']}  closed={counts['closed']}  "
          f"unknown={counts['unknown']}  stale={counts['stale']}")
    print(f"DB total {total}    : " + ", ".join(f"{s} {n}" for s, n in by_source))
    print(f"\nDB: {db.DB_PATH}")


if __name__ == "__main__":
    main()
