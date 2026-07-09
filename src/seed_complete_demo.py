#!/usr/bin/env python3
"""
Seed an ILLUSTRATIVE FOR006 response matrix so the Complete (Stage 4) board +
workspace have something to show. Like the other seed_*_demo.py scripts, this is
DEMO data, not a real FWF submission: it seeds the matrix for one demo bid from the
real FOR006 master question set (via the library provider) and applies a spread of
statuses + one short placeholder answer, so the compliance matrix, the completion
bar and the word-count check render for a browser review. The reusable library it
draws from is read LIVE from the real export (library.py / LocalMirror) — nothing
about the library is seeded or faked.

Depends on seed_plan_demo.py having run first (it needs the bids to exist). Uses the
RTPI demo bid (the one Manage marked submitted / Learn recorded Won) so the journey
reads coherently across stages.

Idempotent: keyed on bid_id via db.upsert_bid_responses, so re-running updates in
place. Run:  python3 seed_complete_demo.py   ·   Reset:  python3 seed_complete_demo.py --clear
"""
import os
import sys

import db
import library as LIB
import response as R

MATCH = "RTPI Cloud Hosted System"

# A short, obviously-placeholder answer for the first question — enough to show the
# word-count check working, not a real submission. Kept well under any limit.
_DEMO_ANSWER = (
    "FWF will deliver the hosted service from UK Azure regions with UK-only data "
    "residency, ISO 27001-aligned security controls, and role-based access. "
    "[DEMO PLACEHOLDER — replace with the real drafted answer.]"
)

# question_ref → (status, answer) overrides applied over the master template.
OVERRIDES = {
    0: ("Approved", _DEMO_ANSWER),   # first question — answered + approved
    1: ("Drafted", "Draft in progress. [DEMO PLACEHOLDER]"),
    2: ("In review", "Under internal review. [DEMO PLACEHOLDER]"),
    # the rest stay "To do", unanswered
}


def _find_bid(conn, fragment):
    row = conn.execute(
        "SELECT b.id AS bid_id FROM bids b JOIN opportunities o ON o.id = b.opportunity_id "
        "WHERE o.title LIKE ? ORDER BY b.id LIMIT 1",
        (f"%{fragment}%",),
    ).fetchone()
    return row["bid_id"] if row else None


def clear(conn):
    bid_id = _find_bid(conn, MATCH)
    if bid_id is None:
        print("  nothing to clear — no demo bid found")
        return
    cur = conn.execute("DELETE FROM bid_responses WHERE bid_id = ?", (bid_id,))
    conn.commit()
    print(f"Cleared {cur.rowcount} demo response matrix(es).")


def seed(conn):
    bid_id = _find_bid(conn, MATCH)
    if bid_id is None:
        print(f"  skip — no bid for {MATCH!r} (run seed_plan_demo.py first)")
        return

    template = LIB.master_template()
    items = []
    for i, q in enumerate(template):
        item = {**R.default_response_item(), **q}
        if i in OVERRIDES:
            status, answer = OVERRIDES[i]
            item["status"] = status
            item["supplier_response"] = answer
        item["actual_words"] = R.word_count(item.get("supplier_response"))
        items.append(item)

    db.upsert_bid_responses(conn, bid_id, {"items": items})

    views = [R.response_view(it) for it in items]
    s = R.matrix_summary(views)
    src = "real FOR006 master" if os.path.exists(LIB.master_path()) else "fallback questions"
    print(f"  seeded FOR006 matrix for bid {bid_id}: {MATCH} "
          f"[{s['total']} questions from {src} · {s['approved']} approved · "
          f"{s['answered']} answered · {s['over_word_limit']} over word limit]")
    conn.commit()
    print("Seeded 1 demo response matrix. Open the Complete stage to review.")


if __name__ == "__main__":
    conn = db.connect()
    db.init_db(conn)
    if "--clear" in sys.argv:
        clear(conn)
    else:
        seed(conn)
    conn.close()
