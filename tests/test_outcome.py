"""B07 Outcome maths — win-rate + score-percentage invariants (Learn domain rules).

Asserts the *shape* of the computation (competitive denominator, honest None for
"no data", rounding) rather than hard-coding a table, so the tests stay true if the
vocabulary is re-tuned. Also pins the CL3 guard: an unknown result must not create a
phantom bucket in by_result.
"""
import outcome as L


def _item(result=None, saved=True, score_pct=None):
    """A minimal winrate_summary item (outcome_view shape)."""
    return {"result": result, "saved": saved, "score_pct": score_pct}


# ---- score_pct -------------------------------------------------------------

def test_score_pct_from_fraction_string():
    assert L.score_pct("88/100") == 88


def test_score_pct_bare_in_range_is_percentage():
    assert L.score_pct("92") == 92


def test_score_pct_against_explicit_max():
    assert L.score_pct("45", "50") == 90


def test_score_pct_rounds_to_nearest_integer():
    # 2/3 -> 66.67 -> 67
    assert L.score_pct("2/3") == 67


def test_score_pct_none_when_no_number():
    assert L.score_pct(None) is None
    assert L.score_pct("") is None
    assert L.score_pct("n/a") is None


def test_score_pct_out_of_range_bare_is_none():
    # 250 with no denominator isn't a percentage and has no max — undecidable.
    assert L.score_pct("250") is None


# ---- winrate_summary -------------------------------------------------------

def test_win_rate_uses_competitive_denominator():
    # Withdrawn is excluded from the win-rate denominator on purpose.
    items = [_item("Won"), _item("Not Won"), _item("Withdrawn")]
    s = L.winrate_summary(items)
    assert s["won"] == 1 and s["not_won"] == 1
    assert s["competitive"] == 2
    assert s["win_rate"] == 50  # 1 / (1+1)


def test_win_rate_none_when_nothing_competitive():
    s = L.winrate_summary([_item("Awaiting"), _item("Withdrawn")])
    assert s["competitive"] == 0
    assert s["win_rate"] is None  # honest "—" rather than a misleading 0%


def test_win_rate_rounds():
    # 2 won of 3 competitive -> 66.67 -> 67
    items = [_item("Won"), _item("Won"), _item("Not Won")]
    assert L.winrate_summary(items)["win_rate"] == 67


def test_avg_score_none_when_no_scores():
    s = L.winrate_summary([_item("Won"), _item("Not Won")])
    assert s["avg_score"] is None


def test_avg_score_averages_and_rounds():
    items = [_item("Won", score_pct=90), _item("Not Won", score_pct=81)]
    assert L.winrate_summary(items)["avg_score"] == 86  # 85.5 -> 86


def test_empty_input_is_all_none_and_zero():
    s = L.winrate_summary([])
    assert s["recorded"] == 0
    assert s["win_rate"] is None
    assert s["avg_score"] is None
    assert s["by_result"] == {r: 0 for r in L.RESULTS}


def test_recorded_counts_only_saved():
    items = [_item("Won", saved=True), _item("Awaiting", saved=False)]
    assert L.winrate_summary(items)["recorded"] == 1


def test_unknown_result_folds_into_awaiting_no_phantom_bucket():
    # CL3: a legacy/unknown stored result must not add a key to by_result.
    s = L.winrate_summary([_item("Shortlisted"), _item("Won")])
    assert set(s["by_result"]) == set(L.RESULTS)  # no "Shortlisted" bucket
    assert s["by_result"]["Awaiting"] == 1        # unknown folded in
    assert s["won"] == 1


def test_missing_result_treated_as_awaiting():
    s = L.winrate_summary([_item(None)])
    assert s["by_result"]["Awaiting"] == 1
