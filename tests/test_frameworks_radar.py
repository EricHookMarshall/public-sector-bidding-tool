"""G2 framework radar — the value is that lifecycle + recommendation are computed
LIVE against today, not stored (the RM6263 "listed after it expired" failure).
These tests pin that logic and the honest-provenance shape (a source per agreement,
projected dates flagged).
"""
import datetime
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")

import frameworks_radar as FR  # noqa: E402
import api  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def test_every_agreement_has_a_source():
    for a in FR.AGREEMENTS:
        assert a["id"] and a["name"]
        assert a["source"]["url"].startswith("https://"), a["id"]


def test_expiry_is_derived_against_today():
    # RM6263 expired 2026-03-07: before that date it's live, after it's expired+skip.
    before = FR.assess(_by_id("RM6263"), datetime.date(2026, 1, 1))
    after = FR.assess(_by_id("RM6263"), datetime.date(2026, 7, 12))
    assert before["lifecycle"] != "expired"
    assert after["lifecycle"] == "expired"
    assert after["recommendation"] == "skip"


def test_member_expiring_escalates_to_act():
    # G-Cloud 14 (member, expires 2026-10-28): well before expiry it's 'maintain';
    # inside the 90-day window it escalates to 'act'.
    early = FR.assess(_by_id("RM1557.14"), datetime.date(2026, 1, 1))
    near = FR.assess(_by_id("RM1557.14"), datetime.date(2026, 9, 1))
    assert early["recommendation"] == "maintain"
    assert near["recommendation"] == "act"


def test_upcoming_framework_is_prepare():
    # G-Cloud 15 live_from 2026-09-01: before that it's upcoming → prepare.
    got = FR.assess(_by_id("RM1557.15"), datetime.date(2026, 7, 12))
    assert got["lifecycle"] == "upcoming"
    assert got["recommendation"] == "prepare"
    assert "live_from" in got["projection_dates"]  # its dates are flagged projections


def test_radar_sorts_most_actionable_first_and_summarises():
    r = FR.radar(datetime.date(2026, 9, 1))
    recs = [a["recommendation"] for a in r["agreements"]]
    ranks = [FR._REC_RANK[x] for x in recs]
    assert ranks == sorted(ranks), "agreements must be ordered by urgency"
    assert sum(r["summary"].values()) == len(FR.AGREEMENTS)


def test_endpoint_serves_radar():
    res = TestClient(api.app).get("/api/frameworks/radar")
    assert res.status_code == 200
    body = res.json()
    assert body["agreements"] and body["verified"] == FR.VERIFIED
    assert "as_of" in body


def _by_id(agreement_id):
    return next(a for a in FR.AGREEMENTS if a["id"] == agreement_id)
