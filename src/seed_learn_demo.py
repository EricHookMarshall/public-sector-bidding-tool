#!/usr/bin/env python3
"""
Seed ILLUSTRATIVE B07 outcomes so the Learn (Stage 6) board has something to show.
Like seed_plan_demo.py / seed_manage_demo.py, this is DEMO data, not real FWF
results: it hangs genuine bid_outcomes rows (via db.py) off the same demo bids the
Plan seed created, so the win-rate readout, the outcome cards and the derived
library suggestions render against a realistic spread for a browser review.
Everything it writes is real schema — the only thing "fake" is that a human didn't
record these outcomes.

Depends on seed_plan_demo.py having run first (it needs the bids to exist). The
cases are chosen to exercise every signal Learn exists to give:
  · RTPI — Won, high score, lessons tagged to PROMOTE content (the win path that
    makes the next bid easier). This is the bid Manage marked submitted.
  · SPM  — Not Won, a competitor named, a lesson tagged to RETIRE weak content
    (the loss path — a lost bid's answers shouldn't seed the next one unchanged).
  · SUMIT — left UNRECORDED on purpose, so the board shows a bid still Awaiting an
    outcome (the loop-closing nudge to record it).
Together they give a 50% win rate (1 won / 2 competitive) tracked bid-by-bid, and
both bids surface "library updates suggested, awaiting your approval" alerts.

Idempotent: keyed on bid_id via db.upsert_bid_outcome, so re-running updates in
place. Run:  python3 seed_learn_demo.py   ·   Reset:  python3 seed_learn_demo.py --clear
"""
import datetime
import sys

import db
import outcome as L


def _day(offset):
    """ISO date `offset` days from today. Outcome dates are relative so they stay
    recent-past instead of drifting ever further behind the hard-coded 2026 dates."""
    return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()


DEMO = [
    {
        "match": "RTPI Cloud Hosted System",
        "outcome": {
            "result": "Won",
            "score_received": "88", "max_score": "100",
            "award_date": _day(-9), "debrief_date": _day(-2),
            "feedback": "Strong technical response and a clear, costed social value offer. "
                        "Evaluators singled out the UK data-residency design.",
            "lessons": [
                {"category": "Technical response",
                 "note": "The hosting/residency answer scored top marks — reuse it as the reference.",
                 "action": "promote"},
                {"category": "Social value",
                 "note": "Costed social value commitments landed well; promote the template.",
                 "action": "promote"},
            ],
            "library_approved": "",   # left unapproved so the board shows the nudge
        },
    },
    {
        "match": "Social Program Management",
        "outcome": {
            "result": "Not Won",
            "score_received": "61", "max_score": "100",
            "winner": "Incumbent Digital Ltd",
            "award_date": _day(-6), "debrief_date": _day(-1),
            "feedback": "Priced above the incumbent; pricing narrative marked as unclear on "
                        "the implementation phasing.",
            "lessons": [
                {"category": "Pricing",
                 "note": "Pricing narrative was flagged unclear — retire it, don't reuse as-is.",
                 "action": "retire"},
                {"category": "Competitor insight",
                 "note": "Incumbent held on strongly on price; note for future qualification.",
                 "action": ""},
            ],
            "library_approved": "",
        },
    },
    # SUMIT is intentionally omitted — it stays Awaiting so the board demonstrates
    # a bid with no outcome recorded yet.
]


def _find_bid(conn, fragment):
    # ORDER BY + fetchone() returns the first match; no LIMIT/TOP/FETCH keeps the
    # query identical on sqlite and SQL Server (dev-local seeder, dual-mode DB).
    row = conn.execute(
        "SELECT b.id AS bid_id FROM bids b JOIN opportunities o ON o.id = b.opportunity_id "
        "WHERE o.title LIKE ? ORDER BY b.id",
        (f"%{fragment}%",),
    ).fetchone()
    return row["bid_id"] if row else None


def clear(conn):
    removed = 0
    for spec in DEMO:
        bid_id = _find_bid(conn, spec["match"])
        if bid_id is None:
            continue
        cur = conn.execute("DELETE FROM bid_outcomes WHERE bid_id = ?", (bid_id,))
        removed += cur.rowcount
    conn.commit()
    print(f"Cleared {removed} demo outcome record(s).")


def seed(conn):
    made = 0
    views = []
    for spec in DEMO:
        bid_id = _find_bid(conn, spec["match"])
        if bid_id is None:
            print(f"  skip — no bid for {spec['match']!r} (run seed_plan_demo.py first)")
            continue
        db.upsert_bid_outcome(conn, bid_id, spec["outcome"])

        view = L.outcome_view(spec["outcome"])
        view["saved"] = True
        views.append(view)
        n = len(view["suggestions"])
        score = view["score_pct"]
        # Fragments extracted so no f-string nests same-type quotes (PEP 701 is
        # 3.12-only; this keeps the seeder importable on ≤3.11).
        score_part = f" · {score}%" if score is not None else ""
        winner_part = f" · lost to {view['winner']}" if view.get("winner") else ""
        print(f"  seeded outcome for bid {bid_id}: {spec['match']} "
              f"[{view['result']}{score_part}{winner_part} "
              f"· {n} library suggestion{'s' if n != 1 else ''}]")
        made += 1
    conn.commit()

    if views:
        wr = L.winrate_summary(views)
        rate = f"{wr['win_rate']}%" if wr["win_rate"] is not None else "—"
        avg = f"{wr['avg_score']}%" if wr["avg_score"] is not None else "—"
        print(f"Seeded {made} demo outcome(s). Win rate {rate} "
              f"({wr['won']} won / {wr['competitive']} competitive), avg score {avg}. "
              f"Open the Learn stage to review.")


if __name__ == "__main__":
    conn = db.connect()
    db.init_db(conn)
    if "--clear" in sys.argv:
        clear(conn)
    else:
        seed(conn)
    conn.close()
