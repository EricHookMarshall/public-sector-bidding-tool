#!/usr/bin/env python3
"""
Seed a few ILLUSTRATIVE bids so the Plan (Stage 3) board has something to show.

This is DEMO data, not real FWF bid/no-bid calls: it drives real stored
opportunities through the real Triage "Go" path (creating genuine qualification +
bid + bid_plan rows via db.py), so the Plan board, capacity bar and alerts render
against realistic numbers for a browser review. Everything it writes is real
schema — the only thing "fake" is that a human didn't make these decisions.

Idempotent: keyed on (source, ocid) opportunities that already exist, and the
qualification/bid/plan upserts are all keyed, so re-running updates in place.

Run:    python3 seed_plan_demo.py
Reset:  python3 seed_plan_demo.py --clear   (removes the seeded bids/quals/plans)

The opportunities themselves are NEVER touched — only the Stage 2/3 rows hung off
them. Picks are by title match so it degrades gracefully if the DB differs.
"""
import datetime
import sys

import db
import qualification as Q


def _day(offset):
    """ISO date `offset` days from today. Demo deadlines are relative so the
    passed/imminent spread stays realistic instead of decaying to all-overdue
    as the old hard-coded 2026 dates would once that month passed."""
    return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()

# Each demo bid: a title fragment to find the opportunity, the FOR001 complexity
# (drives the real cost-to-chase), a RAG sketch, where it sits on the pipeline
# board, its owner, and — for the ones mid-flight — a clarification deadline so
# the founding-failure alert has something to fire on. Dates are chosen relative
# to the notices' real submission deadlines to give a believable urgency spread.
DEMO = [
    {
        "match": "Social Program Management",
        "complexity": "Med-High",
        "rag": {"budget_secured": 3, "commercially_viable": 2, "account_relationship": 2,
                "strength_of_competition": 2},
        "pipeline_stage": "In review", "owner": "EH",
        "clarification_deadline": None,
    },
    {
        "match": "SUMIT Project",
        "complexity": "Low",
        "rag": {"budget_secured": 2, "commercially_viable": 2, "account_relationship": 1},
        "pipeline_stage": "Qualifying", "owner": "",          # deliberately unassigned → alert
        "clarification_deadline": _day(2),                    # imminent → founding-failure alert
    },
    {
        "match": "RTPI Cloud Hosted System",
        "complexity": "Medium",
        "rag": {"budget_secured": 3, "commercially_viable": 3, "account_relationship": 2},
        "pipeline_stage": "Submitted", "owner": "KS",         # off the board → doesn't count vs capacity
        "clarification_deadline": None,
    },
]


def _find_opp(conn, fragment):
    # ORDER BY + fetchone() returns the first match; no LIMIT/TOP/FETCH keeps the
    # query identical on sqlite and SQL Server (dev-local seeder, dual-mode DB).
    row = conn.execute(
        "SELECT * FROM opportunities WHERE title LIKE ? ORDER BY id",
        (f"%{fragment}%",),
    ).fetchone()
    return db._row_dict(row) if row else None


def clear(conn):
    """Remove the seeded Stage 2/3 rows (leaves opportunities untouched)."""
    removed = 0
    for spec in DEMO:
        opp = _find_opp(conn, spec["match"])
        if not opp:
            continue
        bid = db.get_bid_for_opportunity(conn, opp["id"])
        if bid:
            conn.execute("DELETE FROM bid_plans WHERE bid_id = ?", (bid["id"],))
            conn.execute("DELETE FROM bids WHERE id = ?", (bid["id"],))
        conn.execute("DELETE FROM qualifications WHERE opportunity_id = ?", (opp["id"],))
        removed += 1
    conn.commit()
    print(f"Cleared demo Stage 2/3 rows for {removed} opportunity(ies).")


def seed(conn):
    made = 0
    for spec in DEMO:
        opp = _find_opp(conn, spec["match"])
        if not opp:
            print(f"  skip — no opportunity matching {spec['match']!r}")
            continue

        econ = Q.compute_bid_economics(spec["complexity"])
        rating, label = Q.rag_summary(spec["rag"])
        qual = {
            "client_name": opp.get("buyer_name") or opp.get("title"),
            "summary": opp.get("title"),
            "estimated_value": opp.get("value_max"),
            "submission_deadline": opp.get("deadline_date"),
            "clarification_deadline": spec["clarification_deadline"],
            "complexity": spec["complexity"],
            "estimated_bid_effort_days": econ["effort_days"],
            "estimated_bid_cost": econ["cost"],
            "win_qualification_rag": spec["rag"],
            "rag_summary_rating": rating,
            "rag_summary_label": label,
            "decision": "Go",
        }
        qid = db.upsert_qualification(conn, opp["id"], qual)
        bid_id = db.create_bid_from_qualification(
            conn, opp["id"], qid, qual["client_name"], stage="Plan")

        # Give it a pipeline position + owner so the board isn't all in column 1.
        db.upsert_bid_plan(conn, bid_id, {
            "pipeline_stage": spec["pipeline_stage"],
            "owner": spec["owner"],
        })
        made += 1
        print(f"  seeded bid {bid_id}: {spec['match']} "
              f"[{spec['complexity']} · {econ['effort_days']}d · {spec['pipeline_stage']}"
              f"{' · ' + spec['owner'] if spec['owner'] else ' · no owner'}]")
    conn.commit()
    print(f"Seeded {made} demo bid(s). Open the Plan stage to review.")


if __name__ == "__main__":
    conn = db.connect()
    db.init_db(conn)
    if "--clear" in sys.argv:
        clear(conn)
    else:
        seed(conn)
    conn.close()
