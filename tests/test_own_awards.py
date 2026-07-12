"""G1 own-awards connector — offline tests for the supplier-match logic.

The whole point of matching on the Companies House number (not the name) is to
never record an award that isn't ours. These tests pin that: our number matches,
a near-miss number doesn't, a buyer sharing the number doesn't, and a broken
source degrades instead of poisoning the run.
"""
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")

import own_awards as OA  # noqa: E402

OUR_CH = "11934102"

# One OCDS award release where FWF (our CH) is the winning supplier, alongside an
# award to a different company we must NOT pick up.
RELEASE_OURS = {
    "ocid": "ocds-abc-001",
    "id": "notice-001",
    "buyer": {"name": "Example Council"},
    "tender": {
        "title": "Digital transformation services",
        "items": [{"classification": {"scheme": "CPV", "id": "72000000", "description": "IT services"}}],
        "contractPeriod": {"startDate": "2026-04-01", "endDate": "2028-03-31"},
    },
    "parties": [
        {"id": "org-fwf", "name": "Future Workforce UK Ltd", "roles": ["supplier"],
         "identifier": {"scheme": "GB-COH", "id": "11934102"}},
        {"id": "org-other", "name": "Some Other Ltd", "roles": ["supplier"],
         "identifier": {"scheme": "GB-COH", "id": "09999999"}},
        {"id": "org-buyer", "name": "Example Council", "roles": ["buyer"],
         "identifier": {"scheme": "GB-COH", "id": "11934102"}},  # buyer shares our number — must be ignored
    ],
    "awards": [
        {"id": "award-1", "status": "active", "date": "2026-03-15",
         "value": {"amount": 250000, "currency": "GBP"}, "suppliers": [{"id": "org-fwf"}]},
        {"id": "award-2", "status": "active", "date": "2026-03-15",
         "value": {"amount": 90000, "currency": "GBP"}, "suppliers": [{"id": "org-other"}]},
    ],
}


def test_normalise_and_equality():
    assert OA.normalise_ch(" 11934102 ") == "11934102"
    assert OA._ch_equal("11934102", "11934102")
    assert OA._ch_equal("01234567", "1234567")     # leading-zero padding tolerated
    assert not OA._ch_equal("11934102", "11934103")
    assert not OA._ch_equal("", "11934102")


def test_matched_party_excludes_buyer_and_others():
    matched = OA.matched_supplier_party_ids(RELEASE_OURS, OUR_CH)
    assert set(matched) == {"org-fwf"}          # only the supplier party with our number
    assert "org-buyer" not in matched            # buyer sharing the number is excluded
    assert "org-other" not in matched


def test_awards_in_picks_only_ours():
    got = list(OA._awards_in(RELEASE_OURS, OUR_CH))
    assert len(got) == 1
    award, name = got[0]
    assert award["id"] == "award-1"
    assert name == "Future Workforce UK Ltd"


def test_wrong_number_matches_nothing():
    assert OA.matched_supplier_party_ids(RELEASE_OURS, "22222222") == {}
    assert list(OA._awards_in(RELEASE_OURS, "22222222")) == []


def test_to_award_record_shape():
    src = OA.SOURCES[0]
    rec = OA.to_award_record(src, RELEASE_OURS, RELEASE_OURS["awards"][0],
                             "Future Workforce UK Ltd", OUR_CH, src["notice_url"])
    assert rec["source"] == "Find a Tender (awards)"
    assert rec["award_id"] == "award-1"
    assert rec["supplier_id"] == "11934102"
    assert rec["supplier_scheme"] == "GB-COH"
    assert rec["value_amount"] == 250000
    assert rec["contract_end"] == "2028-03-31"
    assert "72000000" in rec["cpv_codes"]
    assert rec["url"].endswith("notice-001")


def test_inline_supplier_identifier_without_parties():
    # A release with no parties[] block, supplier identifier inline on the award.
    rel = {
        "ocid": "ocds-x", "id": "n-x", "buyer": {"name": "B"},
        "tender": {"title": "T"},
        "awards": [{"id": "aw", "status": "active", "suppliers": [
            {"name": "Future Workforce UK Ltd", "identifier": {"scheme": "GB-COH", "id": "11934102"}}]}],
    }
    got = list(OA._awards_in(rel, OUR_CH))
    assert len(got) == 1 and got[0][0]["id"] == "aw"


def test_run_requires_a_number():
    import pytest
    with pytest.raises(ValueError):
        OA.run("", use_db=False)


def test_run_degrades_on_source_error():
    # One good source, one that raises: we keep the good hits and record the error.
    def good_fetch(url):
        return {"releases": [RELEASE_OURS], "links": {}}

    def broken_fetch(url):
        raise RuntimeError("upstream 500")

    sources = [
        {"name": "Good", "endpoint": "http://good", "fetch": good_fetch,
         "param": "updatedFrom", "notice_url": lambda rel: "http://n"},
        {"name": "Broken", "endpoint": "http://broken", "fetch": broken_fetch,
         "param": "updatedFrom", "notice_url": lambda rel: "http://n"},
    ]
    res = OA.run(OUR_CH, use_db=False, sources=sources)
    assert res["kept"] == 1                      # the good source's one match survives
    assert res["incomplete"] is True
    assert res["source_errors"][0]["source"] == "Broken"
