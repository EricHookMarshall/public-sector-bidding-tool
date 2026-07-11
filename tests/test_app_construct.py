"""Smoke test: the FastAPI app imports and constructs.

Catches the class of failure a unit test misses — a syntax error, a bad import,
or a route-registration blow-up that would stop `uvicorn` from booting at all.
Runs in local-bypass mode so it needs no token, DB, or network.
"""
import os


def test_api_app_constructs():
    os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")
    import api  # noqa: E402  (import here so the env var is set first)

    from fastapi import FastAPI
    assert isinstance(api.app, FastAPI)
    # A real route surface, not an empty shell.
    paths = {r.path for r in api.app.routes}
    assert any(p.startswith("/api/") for p in paths), paths
