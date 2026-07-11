"""FOR006 response word-count + over-limit compliance gate (Complete domain rules).

Word counting and the over-limit flag are described as a hard compliance gate — an
over-length answer can be discarded unread — so the boundaries are worth pinning:
empty/None/whitespace inputs, and the exact under/at/over-limit transition.
"""
import response as R


# ---- word_count ------------------------------------------------------------

def test_word_count_empty_and_none_are_zero():
    assert R.word_count(None) == 0
    assert R.word_count("") == 0


def test_word_count_whitespace_only_is_zero():
    assert R.word_count("   \t\n  ") == 0


def test_word_count_collapses_runs_of_whitespace():
    # Leading/trailing/among-words whitespace must not inflate the count.
    assert R.word_count("  one   two\tthree\nfour  ") == 4


def test_word_count_counts_non_string_input():
    # word_count stringifies, so a numeric answer still counts as one token.
    assert R.word_count(12345) == 1


# ---- over_limit boundary (via response_view) -------------------------------

def _view(answer, limit):
    return R.response_view({"supplier_response": answer, "word_count_limit": limit})


def test_under_limit_is_not_over():
    v = _view("one two three", "5 words")
    assert v["actual_words"] == 3
    assert v["over_limit"] is False


def test_exactly_at_limit_is_not_over():
    v = _view("one two three four five", 5)
    assert v["actual_words"] == 5
    assert v["over_limit"] is False


def test_one_over_limit_is_over():
    v = _view("one two three four five six", 5)
    assert v["actual_words"] == 6
    assert v["over_limit"] is True


def test_no_limit_is_never_over():
    v = _view("as many words as we like here", None)
    assert v["word_count_limit"] is None
    assert v["over_limit"] is False


def test_empty_answer_never_over():
    v = _view("", 100)
    assert v["actual_words"] == 0
    assert v["answered"] is False
    assert v["over_limit"] is False
