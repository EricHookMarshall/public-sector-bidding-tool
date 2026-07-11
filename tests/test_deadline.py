"""Deadline correctness — the founding-purpose rule.

This tool exists because a missed deadline killed a real bid. The single most
consequential calculation is therefore "is this opportunity still open?" — and
it must be correct *across timezones*, because a lexicographic string compare on
an offset-stamped ISO date can call an already-closed tender "open".

Covers `contracts_finder_filter.is_open` (the correct, offset-aware version) and
`bidplan.days_until` (drives every "urgent"/"overdue" badge and the expiry gate).
"""
import datetime

import contracts_finder_filter as cf
from bidplan import days_until

UTC = datetime.timezone.utc
NOON_UTC = datetime.datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)


def test_future_deadline_is_open():
    assert cf.is_open("2026-07-10T18:00:00+00:00", NOON_UTC) is True


def test_past_deadline_is_closed():
    assert cf.is_open("2026-07-10T06:00:00+00:00", NOON_UTC) is False


def test_offset_stamped_deadline_already_past_utc_is_closed():
    # 13:00+05:00 == 08:00 UTC, i.e. already past NOON_UTC → CLOSED.
    # A naive lexicographic compare ("2026-07-10T13:..." >= "2026-07-10T12:...")
    # would wrongly call this OPEN — the exact defect the parsed compare fixes.
    assert cf.is_open("2026-07-10T13:00:00+05:00", NOON_UTC) is False


def test_offset_stamped_deadline_still_future_utc_is_open():
    # 10:00-05:00 == 15:00 UTC, still ahead of NOON_UTC → OPEN.
    assert cf.is_open("2026-07-10T10:00:00-05:00", NOON_UTC) is True


def test_missing_deadline_is_closed():
    assert cf.is_open(None, NOON_UTC) is False
    assert cf.is_open("", NOON_UTC) is False


def test_days_until_signs():
    assert days_until("2026-07-20", NOON_UTC) == 10       # future → positive
    assert days_until("2026-07-05", NOON_UTC) == -5       # past → negative
    assert days_until("2026-07-10", NOON_UTC) == 0        # today → zero


def test_days_until_unparseable_is_none():
    assert days_until(None, NOON_UTC) is None
    assert days_until("not-a-date", NOON_UTC) is None
