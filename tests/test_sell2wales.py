"""Sell2Wales connector — mapping + the resilience contract.

Sell2Wales's upstream list API is unreliable (returns HTTP 500 on every query as
at 2026-07). The connector's job is to degrade per-partition, not to fail the
whole source: a poisoned (month × noticeType) partition must be recorded and
skipped, never raise. These tests pin that, plus the field mapping — all offline
via the `fetch_partition._fetch` seam (no network).
"""
import io
import urllib.error

import sell2wales as s2w


SAMPLE = {
    "id": "rls-1-WAL100200",
    "ocid": "ocds-kuma6s-0000600100",
    "date": "2026-07-10T00:00:00Z",
    "tag": ["tender"],
    "buyer": {"name": "Cardiff Council"},
    "parties": [{"name": "Cardiff Council", "roles": ["buyer"],
                 "address": {"region": "UKL22"}}],
    "tender": {
        "title": "ICT Managed Service",
        "status": "active",
        "value": {"amount": 250000.0, "currency": "GBP"},
        "tenderPeriod": {"endDate": "2099-01-01T00:00:00Z"},   # far future = open
        "classification": {"id": "72222300", "scheme": "CPV"},
        "documents": [{"documentType": "contractNotice",
                       "url": "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=WAL100200"}],
    },
}


def test_to_record_maps_core_fields_and_welsh_url():
    rec = s2w.to_record(SAMPLE, ["72222300"])
    assert rec["source"] == "Sell2Wales"
    assert rec["buyer_name"] == "Cardiff Council"
    assert rec["region"] == "UKL22"
    assert rec["value_max"] == 250000.0
    assert rec["url"].startswith("https://www.sell2wales.gov.wales/")


def test_stage_maps_to_ojeu_plus_welsh_website_types():
    assert s2w.STAGE_NOTICE_TYPES["tender"] == [2, 51]
    assert s2w.STAGE_NOTICE_TYPES["award"] == [3, 53]
    import find_tender_filter as ft
    assert set(ft.STAGES) <= set(s2w.STAGE_NOTICE_TYPES)


def test_poisoned_partition_is_recorded_not_raised(monkeypatch):
    # Every partition 500s (the live failure mode). run() must NOT raise: it
    # records each partition and returns 0 kept + incomplete=True.
    monkeypatch.setattr(s2w, "MAX_PARTITION_TRIES", 1)   # skip retry backoff in the test

    def boom(url):
        raise urllib.error.HTTPError(
            url, 500, "Internal Server Error", None,
            io.BytesIO(b"<html><title>Error converting data type nvarchar to float.</title></html>"))

    monkeypatch.setattr(s2w.fetch_partition, "_fetch", boom)
    res = s2w.run(published_from="2026-07-01", published_to="2026-07-31", use_db=False)

    assert res["kept"] == 0
    assert res["incomplete"] is True
    assert res["partition_errors"], "the failed partition must be recorded"
    pe = res["partition_errors"][0]
    assert pe["httpStatus"] == 500
    assert "nvarchar" in pe["error"]           # the real SQL fault, surfaced
    assert pe["retryable"] is True
    assert pe["fallback"] == "official-monthly-download"


def test_healthy_partition_ingests_and_dedupes(monkeypatch):
    monkeypatch.setattr(s2w, "PAGE_DELAY", 0)   # no politeness sleep in the test
    # Both notice-type partitions return the same release → deduped to one record.
    monkeypatch.setattr(s2w.fetch_partition, "_fetch", lambda url: {"releases": [SAMPLE]})
    res = s2w.run(published_from="2026-07-01", published_to="2026-07-31", use_db=False)

    assert res["kept"] == 1
    assert res["incomplete"] is False
    assert res["records"][0]["source"] == "Sell2Wales"


def test_partial_outage_keeps_good_partitions(monkeypatch):
    # One notice type works, the other 500s → we keep the good one AND flag incomplete.
    monkeypatch.setattr(s2w, "MAX_PARTITION_TRIES", 1)
    monkeypatch.setattr(s2w, "PAGE_DELAY", 0)

    def flaky(url):
        if "noticeType=51" in url:
            raise urllib.error.HTTPError(url, 500, "err", None, io.BytesIO(b"<title>boom</title>"))
        return {"releases": [SAMPLE]}

    monkeypatch.setattr(s2w.fetch_partition, "_fetch", flaky)
    res = s2w.run(published_from="2026-07-01", published_to="2026-07-31", use_db=False)

    assert res["kept"] == 1                 # the healthy partition still ingested
    assert res["incomplete"] is True        # but the outage is not hidden
    assert len(res["partition_errors"]) == 1
