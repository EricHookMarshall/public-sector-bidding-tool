"""Manual award capture (G1 follow-on).

Some genuinely-won contracts can't be recovered from public OCDS — the notice
named the supplier by name only (no Companies House id for the CH-matcher), the
award was below the publication threshold, or FWF was a subcontractor. The app
lets an Admin record such an award by hand. These tests pin the two guarantees:

  1. a hand-entered award is stored honestly — a DISTINCT source and a 'MANUAL'
     supplier_scheme, never dressed up as a verified GB-COH public match; and
  2. the OCDS refresh path leaves manual records alone (different source key), so
     a real win recorded once is never clobbered by a subsequent public pull.

Isolation: the API tests override get_conn to a temp bids.db so nothing touches
the real one; the db-level test uses its own temp connection.
"""
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")  # unauthenticated TestClient, as in dev

import api  # noqa: E402  (after env is set)
import db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _client(tmp_path):
    """A TestClient whose get_conn yields a connection to an isolated temp DB."""
    path = str(tmp_path / "bids.db")
    conn = db.connect(db_path=path)
    db.init_db(conn)
    conn.close()

    def _override():
        c = db.connect(db_path=path)
        try:
            yield c
        finally:
            c.close()

    api.app.dependency_overrides[api.get_conn] = _override
    return TestClient(api.app), path


def _teardown():
    api.app.dependency_overrides.pop(api.get_conn, None)


# --- db layer --------------------------------------------------------------

def test_upsert_and_delete_award_roundtrip(tmp_path):
    conn = db.connect(db_path=str(tmp_path / "bids.db"))
    db.init_db(conn)
    assert db.list_awards(conn) == []

    db.upsert_award(conn, {
        "source": "Internal record (manual)",
        "award_id": "manual-abc123",
        "title": "Workforce support",
        "buyer_name": "NHS Barnsley",
        "supplier_scheme": "MANUAL",
        "status": "unverified",
    })
    rows = db.list_awards(conn)
    assert len(rows) == 1
    pk = rows[0]["id"]
    assert rows[0]["buyer_name"] == "NHS Barnsley"

    # delete returns the deleted row's source; a second delete finds nothing.
    assert db.delete_award(conn, pk) == "Internal record (manual)"
    assert db.list_awards(conn) == []
    assert db.delete_award(conn, pk) is None
    conn.close()


# --- api layer -------------------------------------------------------------

def test_manual_award_stored_honestly(tmp_path):
    client, _ = _client(tmp_path)
    try:
        r = client.post("/api/awards/manual", json={
            "title": "Workforce transformation support",
            "buyer_name": "NHS Barnsley",
            "value_amount": 45000,
            "note": "original notice not locatable; from internal records",
        })
        assert r.status_code == 200, r.text
        board = r.json()["board"]
        assert board["summary"]["total"] == 1
        award = board["awards"][0]
        # Honest provenance: distinct source, MANUAL scheme (never GB-COH), unverified.
        assert award["source"] == api.MANUAL_AWARD_SOURCE
        assert award["supplier_scheme"] == "MANUAL"
        assert award["supplier_scheme"] != "GB-COH"
        assert award["status"] == "unverified"
        assert award["award_id"].startswith("manual-")
        assert float(award["value_amount"]) == 45000  # stored TEXT, so compare numerically
        assert award["currency"] == "GBP"  # defaulted because a value was given
    finally:
        _teardown()


def test_manual_award_rejects_empty(tmp_path):
    client, _ = _client(tmp_path)
    try:
        r = client.post("/api/awards/manual", json={"note": "nothing useful"})
        assert r.status_code == 422, r.text
    finally:
        _teardown()


def test_manual_award_survives_ocds_refresh(tmp_path, monkeypatch):
    """A manual record must not be clobbered by an OCDS refresh (different source
    key), and the refresh must not invent anything when the sources return none."""
    client, path = _client(tmp_path)
    try:
        # Configure a CH number so refresh is allowed, then record a manual award.
        client.put("/api/settings/own-org", json={"companies_house_number": "11934102"})
        client.post("/api/awards/manual", json={"buyer_name": "NHS Barnsley"})

        # Stub the OCDS pull to return zero awards (as the real feeds do for FWF).
        monkeypatch.setattr(api.OWN, "run", lambda *a, **k: {
            "scanned": 5, "kept": 0, "inserted": 0, "updated": 0,
            "records": [], "source_errors": [], "incomplete": False,
        })
        r = client.post("/api/awards/refresh?days=30")
        assert r.status_code == 200, r.text

        board = client.get("/api/awards/board").json()
        assert board["summary"]["total"] == 1  # the manual award is still there
        assert board["awards"][0]["source"] == api.MANUAL_AWARD_SOURCE
    finally:
        _teardown()


def test_delete_missing_award_404(tmp_path):
    client, _ = _client(tmp_path)
    try:
        assert client.delete("/api/awards/99999").status_code == 404
    finally:
        _teardown()
