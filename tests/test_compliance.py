"""Compliance & Renewals (C-series) — the expiry derivation, store, and register.

Three layers, all offline (no network, no real bid library):
  - compliance.py: expiry status is DERIVED live against a fixed `now` (so the
    test can't rot as the real date moves) — the founding "expired cert" logic.
  - compliance_store.py: the file-store seam round-trips bytes and REFUSES a
    path-traversal stored_path (a hostile filename must not escape the root).
  - db.py: the compliance_assets CRUD + idempotent seed round-trip on a temp DB.
"""
import datetime

import compliance as CMP
import compliance_store as CS
import db

# A fixed "today" so expired/expiring/ok assertions are stable forever.
NOW = datetime.datetime(2026, 7, 12, tzinfo=datetime.timezone.utc)


# --- compliance.py: derived expiry ------------------------------------------

def test_expiry_status_expired_expiring_ok_none():
    expired = CMP.derive_expiry({"name": "ISO", "expiry_date": "2025-10-31"}, now=NOW)
    assert expired["expiry_status"] == "expired" and expired["days_to_expiry"] < 0

    soon = CMP.derive_expiry({"name": "Cyber", "expiry_date": "2026-08-01"}, now=NOW)
    assert soon["expiry_status"] == "expiring_soon" and 0 <= soon["days_to_expiry"] <= CMP.EXPIRING_SOON_DAYS

    ok = CMP.derive_expiry({"name": "Insurance", "expiry_date": "2099-01-01"}, now=NOW)
    assert ok["expiry_status"] == "ok"

    none = CMP.derive_expiry({"name": "Policy", "expiry_date": ""}, now=NOW)
    assert none["expiry_status"] == "none" and none["days_to_expiry"] is None


def test_expiry_mined_from_notes_when_no_date_field():
    # A renewal date typed only into the notes still drives an alert.
    a = CMP.derive_expiry({"name": "EL Insurance", "expiry_date": "",
                           "notes": "Policy valid until 31 Oct 2025"}, now=NOW)
    assert a["effective_expiry"] == "2025-10-31"
    assert a["expiry_status"] == "expired"


def test_board_sorts_expired_first_then_soonest():
    rows = CMP.board([
        {"name": "ok", "expiry_date": "2099-01-01"},
        {"name": "expired", "expiry_date": "2025-10-31"},
        {"name": "undated", "expiry_date": ""},
        {"name": "soon", "expiry_date": "2026-08-01"},
    ], now=NOW)
    assert [r["name"] for r in rows] == ["expired", "soon", "ok", "undated"]


def test_summary_counts_by_status():
    rows = CMP.board([
        {"name": "a", "expiry_date": "2025-10-31"},
        {"name": "b", "expiry_date": "2099-01-01"},
        {"name": "c", "expiry_date": ""},
    ], now=NOW)
    s = CMP.summary(rows)
    assert s == {"total": 3, "expired": 1, "expiring_soon": 0, "ok": 1, "none": 1}


def test_seed_only_evidence_categories_carry_expiry():
    items = [
        {"category": "Company Credentials", "item": "ISO 27001", "expiry_date": "2025-10-31"},
        {"category": "Capabilities", "item": "not a credential"},   # dropped
        {"category": "Governance", "item": ""},                      # blank name dropped
        {"category": "Commercial", "item": "Insurance"},
    ]
    seeds = CMP.seed_assets_from_library(items)
    names = {s["name"] for s in seeds}
    assert names == {"ISO 27001", "Insurance"}
    iso = next(s for s in seeds if s["name"] == "ISO 27001")
    assert iso["expiry_date"] == "2025-10-31" and iso["source"] == "seed:library"


# --- compliance_store.py: the file-store seam -------------------------------

def test_safe_ext_allows_docs_rejects_others():
    assert CS.safe_ext("cert.PDF") == ".pdf"
    assert CS.safe_ext("scan.jpg") == ".jpg"
    assert CS.safe_ext("evil.exe") == ""
    assert CS.safe_ext("noext") == ""


def test_store_roundtrip_and_delete(tmp_path):
    store = CS.LocalFileStore(root=str(tmp_path))
    stored = store.save(b"cert-bytes", "iso.pdf")
    assert stored.endswith(".pdf") and store.exists(stored)
    assert store.open(stored) == b"cert-bytes"
    assert store.delete(stored) is True
    assert not store.exists(stored)
    assert store.delete(stored) is False  # already gone


def test_store_rejects_unsupported_and_traversal(tmp_path):
    store = CS.LocalFileStore(root=str(tmp_path))
    import pytest
    with pytest.raises(ValueError):
        store.save(b"x", "malware.exe")
    with pytest.raises(ValueError):
        store.open("../../etc/passwd")
    assert store.exists("../../etc/passwd") is False  # confinement, not a crash


# --- db.py: compliance_assets CRUD + seed -----------------------------------

def _conn(tmp_path):
    conn = db.connect(db_path=str(tmp_path / "bids.db"))
    db.init_db(conn)
    return conn


def test_compliance_crud_roundtrip(tmp_path):
    conn = _conn(tmp_path)
    aid = db.insert_compliance_asset(conn, {
        "name": "ISO 27001", "category": "Company Credentials",
        "expiry_date": "2025-10-31", "source": "reference",
        "not_a_column": "should be ignored",  # allow-list guard
    })
    got = db.get_compliance_asset(conn, aid)
    assert got["name"] == "ISO 27001" and got["expiry_date"] == "2025-10-31"
    assert "not_a_column" not in got

    assert db.update_compliance_asset(conn, aid, {"expiry_date": "2026-11-30"}) == 1
    assert db.get_compliance_asset(conn, aid)["expiry_date"] == "2026-11-30"

    assert db.delete_compliance_asset(conn, aid) == ""      # had no stored file
    assert db.get_compliance_asset(conn, aid) is None
    assert db.delete_compliance_asset(conn, 999) is None    # missing id


def test_seed_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    seeds = [{"name": "ISO", "category": "Company Credentials", "source": "seed:library"},
             {"name": "Insurance", "category": "Commercial", "source": "seed:library"}]
    assert db.seed_compliance_assets(conn, seeds) == 2
    # Second call is a no-op — the register is no longer empty.
    assert db.seed_compliance_assets(conn, seeds) == 0
    assert len(db.list_compliance_assets(conn)) == 2
