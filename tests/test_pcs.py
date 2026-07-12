"""Public Contracts Scotland connector — offline mapping + pagination invariants.

PCS differs from the OCDS connectors it sits beside: month-granular paging, a
notice-type split per stage, and a bespoke buyer/region/URL mapping. These tests
pin that logic against a captured release shape (no network).
"""
import datetime

import public_contracts_scotland as pcs


# A trimmed real PCS release (fields the mapper touches). CPV lives at
# tender.classification + items[].additionalClassifications — the shape ft.cpvs_in
# already understands.
SAMPLE = {
    "id": "rls-1-JUL559948",
    "ocid": "ocds-r6ebe6-0000823882",
    "date": "2026-07-10T00:00:00Z",
    "tag": ["tender"],
    "buyer": {"name": "Aberdeen City Council"},
    "parties": [{
        "name": "Aberdeen City Council",
        "roles": ["buyer"],
        "address": {"region": "UKM50", "locality": "Aberdeen"},
    }],
    "tender": {
        "title": "Operation and Maintenance Services",
        "description": "O&M services for the facility.",
        "status": "active",
        "value": {"amount": 477616363.0, "currency": "GBP"},
        "tenderPeriod": {"endDate": "2026-08-11T14:00:00Z"},
        "classification": {"id": "72500000", "scheme": "CPV"},
        "items": [{
            "id": "1",
            "additionalClassifications": [
                {"id": "72222300", "scheme": "CPV"},
                {"id": "45220000", "scheme": "CPV"},
            ],
        }],
        "documents": [{
            "documentType": "contractNotice",
            "url": "https://www.publiccontractsscotland.gov.uk/search/show/search_view.aspx?ID=JUL559948",
        }],
    },
    "links": [{"rel": "canonical",
               "href": "https://api.publiccontractsscotland.gov.uk/v1/Notice?id=ocds-r6ebe6-0000823882"}],
}


def test_to_record_maps_core_fields():
    rec = pcs.to_record(SAMPLE, ["72222300"])
    assert rec["source"] == "Public Contracts Scotland"
    assert rec["ocid"] == "ocds-r6ebe6-0000823882"
    assert rec["title"] == "Operation and Maintenance Services"
    assert rec["buyer_name"] == "Aberdeen City Council"
    assert rec["value_max"] == 477616363.0
    assert rec["currency"] == "GBP"
    assert rec["deadline_date"] == "2026-08-11T14:00:00Z"
    assert rec["status"] == "active"


def test_to_record_region_from_buyer_party():
    # PCS carries delivery region on the buyer party, not the tender block.
    assert pcs.to_record(SAMPLE, ["72222300"])["region"] == "UKM50"


def test_notice_url_prefers_human_document_link():
    url = pcs.notice_url(SAMPLE)
    assert url.startswith("https://www.publiccontractsscotland.gov.uk/")
    assert "search_view.aspx" in url


def test_buyer_name_falls_back_to_party_role():
    rel = {**SAMPLE, "buyer": {}}          # no rel.buyer.name
    assert pcs._buyer_name(rel) == "Aberdeen City Council"


def test_stage_maps_to_ojeu_plus_site_notice_types():
    # Each stage spans the OJEU form + its sub-threshold Site Notice counterpart.
    assert pcs.STAGE_NOTICE_TYPES["tender"] == [2, 102]
    assert pcs.STAGE_NOTICE_TYPES["award"] == [3, 103]
    # Every stage the UI can request must have a notice-type mapping.
    import find_tender_filter as ft
    assert set(ft.STAGES) <= set(pcs.STAGE_NOTICE_TYPES)


def test_months_in_range_is_inclusive_and_ordered():
    d = datetime.datetime
    tz = datetime.timezone.utc
    # A window spanning a year boundary enumerates every month, mm-yyyy, inclusive.
    got = pcs.months_in_range(d(2025, 11, 20, tzinfo=tz), d(2026, 2, 3, tzinfo=tz))
    assert got == ["11-2025", "12-2025", "01-2026", "02-2026"]
    # Same month at both ends yields exactly one page unit.
    assert pcs.months_in_range(d(2026, 7, 1, tzinfo=tz), d(2026, 7, 28, tzinfo=tz)) == ["07-2026"]
