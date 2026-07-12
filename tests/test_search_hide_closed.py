"""F6 — Search default-hides closed opportunities unless they're in flight.

The default list view should drop opps whose derived bid_status is 'closed',
EXCEPT ones the user is actively chasing (picked into Triage, or already worked)
— mirroring the Triage pull-gate carve-out — and an explicit bid_status filter
must always override the hide. Exercised through api._query_opportunities against
a temp DB so the derivation + carve-out run for real.
"""
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")

import api  # noqa: E402
import db  # noqa: E402

OPEN = "2099-01-01T00:00:00"      # deadline in the future -> bid_status "open"
CLOSED = "2000-01-01T00:00:00"    # deadline in the past   -> bid_status "closed"


def _opp(conn, ocid, deadline):
    """Insert one opportunity and return its id."""
    db.upsert_opportunity(conn, {
        "source": "test", "ocid": ocid, "title": f"opp {ocid}",
        "deadline_date": deadline,
    })
    return conn.execute("SELECT id FROM opportunities WHERE ocid = ?", (ocid,)).fetchone()["id"]


def _query(conn, **overrides):
    params = dict(
        q=None, source=None, status=None, bid_status=None, lifecycle=None,
        country=None, region=None, currency=None, notice_type=None,
        min_value=None, max_value=None, sort="deadline_date", order="asc",
    )
    params.update(overrides)
    return api._query_opportunities(conn, **params)


def _conn(tmp_path):
    conn = db.connect(db_path=str(tmp_path / "bids.db"))
    db.init_db(conn)
    return conn


def test_default_hides_closed_but_keeps_open(tmp_path):
    conn = _conn(tmp_path)
    open_id = _opp(conn, "open-1", OPEN)
    _opp(conn, "closed-1", CLOSED)

    ids = {r["id"] for r in _query(conn, hide_closed=True)}
    assert open_id in ids
    assert len(ids) == 1, "the closed opp must be hidden by default"


def test_closed_but_selected_stays_visible(tmp_path):
    conn = _conn(tmp_path)
    closed_id = _opp(conn, "closed-inflight", CLOSED)
    db.set_triage_selected(conn, closed_id, True)   # pulled into Triage == in flight

    ids = {r["id"] for r in _query(conn, hide_closed=True)}
    assert closed_id in ids, "a closed opp in the pipeline must never vanish"


def test_hide_closed_off_shows_everything(tmp_path):
    conn = _conn(tmp_path)
    _opp(conn, "open-1", OPEN)
    _opp(conn, "closed-1", CLOSED)

    ids = {r["id"] for r in _query(conn, hide_closed=False)}
    assert len(ids) == 2


def test_explicit_bid_status_overrides_hide(tmp_path):
    conn = _conn(tmp_path)
    _opp(conn, "open-1", OPEN)
    closed_id = _opp(conn, "closed-1", CLOSED)

    # Asking for closed explicitly must return the closed opp even with the
    # default hide flag still set — the explicit filter wins.
    rows = _query(conn, bid_status="closed", hide_closed=True)
    assert {r["id"] for r in rows} == {closed_id}
