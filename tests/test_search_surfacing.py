"""/api/search must surface a partial (incomplete) source run.

The connector layer already degrades per-partition and returns `incomplete` +
`partition_errors` (see test_sell2wales.py). This guards the *reporting* half:
that the endpoint passes the partial state through as `incomplete` + a
`failed_partitions` count, and — deliberately — does NOT leak the raw
`partition_errors` (which carry upstream detail) into the client response.
"""
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")  # unauthenticated TestClient, as in dev

import api  # noqa: E402  (after env is set)
from fastapi.testclient import TestClient  # noqa: E402


def _fake_source(name, result):
    """A sources.SOURCES entry whose run() ignores its args and returns `result`."""
    return {"name": name, "run": lambda **_kw: result}


def test_incomplete_source_surfaces_flag_and_count(monkeypatch):
    partial = {
        "source": "Flaky Source", "scanned": 3, "kept": 1,
        "inserted": 1, "updated": 0,
        "partition_errors": [{"error": "upstream 500 — internal detail"},
                             {"error": "upstream 500 — internal detail"}],
        "incomplete": True,
    }
    monkeypatch.setattr(api.sources, "SOURCES", {"flaky": _fake_source("Flaky Source", partial)})

    r = TestClient(api.app).post("/api/search", json={"sources": ["flaky"]})
    assert r.status_code == 200, r.text
    run = r.json()["runs"][0]

    assert run["ok"] is True
    assert run["incomplete"] is True
    assert run["failed_partitions"] == 2
    # The raw partition errors (upstream detail) must not reach the client.
    assert "partition_errors" not in run
    assert "internal detail" not in r.text


def test_healthy_source_omits_the_incomplete_flag(monkeypatch):
    healthy = {
        "source": "Good Source", "scanned": 5, "kept": 5,
        "inserted": 5, "updated": 0, "incomplete": False,
    }
    monkeypatch.setattr(api.sources, "SOURCES", {"good": _fake_source("Good Source", healthy)})

    r = TestClient(api.app).post("/api/search", json={"sources": ["good"]})
    assert r.status_code == 200, r.text
    run = r.json()["runs"][0]

    assert run["ok"] is True
    assert "incomplete" not in run          # a clean run stays quiet
    assert "failed_partitions" not in run
