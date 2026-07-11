"""CPV relevance-scope invariant (the DB-population contract in CLAUDE.md).

Connectors strip trailing zeros so a *group* code matches all of its sub-codes,
and the most specific prefix must win. If this breaks, the DB either fills with
irrelevant notices or silently drops relevant ones.
"""
from find_tender_filter import build_prefixes, matches


def test_trailing_zeros_stripped_so_group_matches_subcodes():
    prefixes = build_prefixes(["72000000"])          # "IT services" group
    assert prefixes == ["72"]
    assert matches("72212000", prefixes) == "72"     # a sub-code matches the group
    assert matches("48000000", prefixes) is None     # unrelated group does not


def test_longest_prefix_wins():
    # Most specific prefix must be tried first (longest-first ordering).
    prefixes = build_prefixes(["72000000", "72212224"])
    assert prefixes == ["72212224", "72"]            # longest first
    assert matches("72212224000", prefixes) == "72212224"


def test_no_match_returns_none():
    assert matches("30000000", build_prefixes(["72000000"])) is None


def test_dedupes_equivalent_codes():
    # "72000000" and "72" strip to the same prefix — no duplicate.
    assert build_prefixes(["72000000", "72"]) == ["72"]
