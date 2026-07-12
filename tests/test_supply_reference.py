"""The "how to supply" reference (G3) is curated, static content — no DB, no
live fetch. These tests guard its *shape* so the UI can rely on it and so the
facts-decay discipline (a verified date + a source link on every route) holds.
"""
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")  # unauthenticated TestClient, as in dev

import supply_reference as SUPPLY  # noqa: E402
import api  # noqa: E402  (after env is set)
from fastapi.testclient import TestClient  # noqa: E402


def test_reference_has_expected_top_level_shape():
    ref = SUPPLY.reference()
    assert set(ref) >= {"verified", "disclaimer", "routes", "getting_started", "help_links"}
    assert ref["verified"], "a verified date is required (facts-decay discipline)"
    assert ref["routes"] and ref["getting_started"] and ref["help_links"]


def test_every_route_carries_a_source_link():
    # A curated fact with no source can't be re-verified — the discipline requires one.
    for r in SUPPLY.reference()["routes"]:
        assert r["id"] and r["title"] and r["summary"]
        assert r["key_points"], f"{r['id']} has no key points"
        src = r["source"]
        assert src["label"] and src["url"].startswith("https://"), f"{r['id']} source"


def test_covers_the_g3_routes_to_market():
    ids = {r["id"] for r in SUPPLY.reference()["routes"]}
    # G3 scope: Frameworks, Dynamic Markets, DPS, Catalogues (+ finding notices).
    assert {"frameworks", "dynamic-markets", "dps", "catalogues"} <= ids


def test_endpoint_serves_the_reference():
    client = TestClient(api.app)
    res = client.get("/api/supply/reference")
    assert res.status_code == 200
    body = res.json()
    assert body["verified"] == SUPPLY.VERIFIED
    assert len(body["routes"]) == len(SUPPLY.ROUTES)
