"""FOR001 qualification economics + RAG rating (Triage domain rules).

Asserts invariants rather than hard-coding the effort table, so the tests stay
true if the day-counts are re-tuned — what must hold is the *shape* of the maths.
"""
import qualification as Q


def test_unknown_complexity_yields_zeros_not_error():
    r = Q.compute_bid_economics("nonsense")
    assert r["effort_days"] == 0
    assert r["cost"] == 0
    assert r["breakdown"] == []


def test_economics_are_internally_consistent():
    r = Q.compute_bid_economics("Medium")
    assert r["breakdown"], "a known complexity must produce a breakdown"
    assert len(r["breakdown"]) == len(Q.BID_EFFORT_DAYS)
    # Totals must equal the sum of the per-role lines.
    assert r["cost"] == sum(b["cost"] for b in r["breakdown"])
    assert r["effort_days"] == sum(b["days"] for b in r["breakdown"])
    for b in r["breakdown"]:
        assert b["cost"] == b["days"] * b["rate"]


def test_higher_complexity_costs_at_least_as_much():
    low = Q.compute_bid_economics("Low")["effort_days"]
    high = Q.compute_bid_economics("High")["effort_days"]
    assert high >= low


def test_custom_day_rates_flow_through():
    role = next(iter(Q.BID_EFFORT_DAYS))
    base = Q.compute_bid_economics("Medium")["cost"]
    dearer = Q.compute_bid_economics("Medium", rates={role: Q.DAY_RATE * 4})["cost"]
    assert dearer > base


def test_rag_summary_risk_facing_labels():
    keys = list(Q.RAG_CRITERIA_KEYS)
    assert Q.rag_summary({keys[0]: 3, keys[1]: 3}) == (3, "Low")   # high score = low risk
    assert Q.rag_summary({keys[0]: 1}) == (1, "High")              # low score = high risk
    assert Q.rag_summary({}) == (None, None)                       # nothing scored


def test_rag_summary_ignores_out_of_range_and_unknown_keys():
    keys = list(Q.RAG_CRITERIA_KEYS)
    # 7 is out of the 1..3 range and "bogus" isn't a real criterion → both ignored,
    # leaving only the valid 2 → (2, "Med").
    assert Q.rag_summary({keys[0]: 2, keys[1]: 7, "bogus": 3}) == (2, "Med")
