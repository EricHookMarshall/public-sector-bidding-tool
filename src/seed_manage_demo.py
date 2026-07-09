#!/usr/bin/env python3
"""
Seed ILLUSTRATIVE FOR003 registers so the Manage (Stage 5) board has something
to show. Like seed_plan_demo.py, this is DEMO data, not real FWF clarifications:
it hangs genuine bid_manage rows (via db.py) off the same three demo bids the
Plan seed created, so the register, the deadline alerts and the pre-flight gate
render against a realistic spread for a browser review. Everything it writes is
real schema — the only thing "fake" is that a human didn't log these.

Depends on seed_plan_demo.py having run first (it needs the bids to exist). The
three cases are chosen to exercise every signal Manage exists to give:
  · SUMIT — a clarification whose deadline has PASSED with no owner (the exact
    founding failure: a missed clarification, unassigned).
  · SPM   — a clarification imminent but owned + backed up, and a gate blocked by
    an EXPIRED Cyber Essentials cert (the expired-credential enforcement).
  · RTPI  — clarifications answered, gate clear, already submitted (the done state).

Idempotent: keyed on bid_id via db.upsert_bid_manage, so re-running updates in
place. Run:  python3 seed_manage_demo.py   ·   Reset:  python3 seed_manage_demo.py --clear
"""
import sys

import clarification as M
import db


def _preflight(overrides):
    """A full pre-flight checklist with the given {key: (status, expiry_date)}
    overrides applied; everything else left blank (pending)."""
    checks = M.default_preflight()
    for c in checks:
        if c["key"] in overrides:
            status, expiry = overrides[c["key"]]
            c["status"] = status
            if expiry is not None:
                c["expiry_date"] = expiry
    return checks


# All-pass gate (a legitimately submittable bid): every mandatory item passed,
# credentials in date. The auto clarifications item is derived, so its stored
# status is irrelevant — the demo answers RTPI's clarification instead.
_ALL_PASS = {it["key"]: ("pass", "2027-01-01" if it.get("expiry") else None)
             for it in M.PREFLIGHT_ITEMS}

DEMO = [
    {
        "match": "SUMIT Project",
        "clarifications": [{
            **M.default_clarification(),
            "question_number": "CQ01",
            "question": "Confirm whether the Arobs parent company guarantee is acceptable in lieu of 3 years' filed accounts",
            "channel": "via portal", "owner": "", "backup_owner": "",
            "buyer_deadline": "2026-07-06", "deadline_note": "12:00 BST",
            "status": "Open",
        }],
        "preflight": _preflight({"pcg": ("pass", None)}),
        "submitted": "",
    },
    {
        "match": "Social Program Management",
        "clarifications": [{
            **M.default_clarification(),
            "question_number": "CQ01",
            "question": "Confirm exact wording required for the parent company guarantee (Schedule 5)",
            "channel": "via portal", "owner": "EH", "backup_owner": "KS",
            "buyer_deadline": "2026-07-14", "deadline_note": "17:00 BST",
            "status": "Drafting",
        }],
        # Nearly ready — but Cyber Essentials expired last month, so the gate
        # holds (plus the open clarification the auto item catches).
        "preflight": _preflight({
            "responses_complete": ("pass", None), "social_value": ("pass", None),
            "carbon_plan": ("na", None), "modern_slavery": ("pass", None),
            "uk_gdpr": ("pass", None), "pcg": ("pass", None),
            "deadline_captured": ("pass", None),
            "cyber_essentials": ("pass", "2026-06-15"),   # expired → enforced fail
        }),
        "submitted": "",
    },
    {
        "match": "RTPI Cloud Hosted System",
        "clarifications": [{
            **M.default_clarification(),
            "question_number": "CQ01",
            "question": "Confirm the hosting region requirement (UK-only data residency)",
            "channel": "via email", "owner": "KS", "backup_owner": "EH",
            "buyer_deadline": "2026-06-20", "deadline_note": "17:00 BST",
            "date_submitted": "2026-06-12", "response_date": "2026-06-18",
            "buyer_response": "UK-only data residency confirmed; no offshore processing permitted.",
            "status": "Answered",
        }],
        "preflight": _preflight(_ALL_PASS),
        "submitted": "yes",
    },
]


def _find_bid(conn, fragment):
    row = conn.execute(
        "SELECT b.id AS bid_id FROM bids b JOIN opportunities o ON o.id = b.opportunity_id "
        "WHERE o.title LIKE ? ORDER BY b.id LIMIT 1",
        (f"%{fragment}%",),
    ).fetchone()
    return row["bid_id"] if row else None


def clear(conn):
    removed = 0
    for spec in DEMO:
        bid_id = _find_bid(conn, spec["match"])
        if bid_id is None:
            continue
        cur = conn.execute("DELETE FROM bid_manage WHERE bid_id = ?", (bid_id,))
        removed += cur.rowcount
    conn.commit()
    print(f"Cleared {removed} demo manage record(s).")


def seed(conn):
    made = 0
    for spec in DEMO:
        bid_id = _find_bid(conn, spec["match"])
        if bid_id is None:
            print(f"  skip — no bid for {spec['match']!r} (run seed_plan_demo.py first)")
            continue
        fields = {
            "clarifications": spec["clarifications"],
            "preflight": spec["preflight"],
            "submitted": spec["submitted"],
        }
        if spec["submitted"] == "yes":
            fields["submitted_at"] = db.now_iso()
        db.upsert_bid_manage(conn, bid_id, fields)

        # Report the gate state so the run shows what the board will render.
        resolved = M.resolve_preflight(spec["preflight"], spec["clarifications"])
        gate = M.preflight_summary(resolved)
        clar = spec["clarifications"][0]
        state = "SUBMITTED" if spec["submitted"] == "yes" else (
            "gate clear" if gate["ready"] else f"gate blocked ×{gate['blocking_count']}")
        print(f"  seeded manage for bid {bid_id}: {spec['match']} "
              f"[clar {clar['status']} · due {clar['buyer_deadline'] or '—'}"
              f"{' · no owner' if not clar['owner'] else ' · ' + clar['owner']} · {state}]")
        made += 1
    conn.commit()
    print(f"Seeded {made} demo manage record(s). Open the Manage stage to review.")


if __name__ == "__main__":
    conn = db.connect()
    db.init_db(conn)
    if "--clear" in sys.argv:
        clear(conn)
    else:
        seed(conn)
    conn.close()
