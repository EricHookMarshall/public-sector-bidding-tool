"""FOR003 pre-flight gate (Manage / Stage 5) — the submission blocker.

Two overrides are the whole point of the gate and must not be bypassable by a
ticked box: an *expired* credential auto-fails, and any *open* clarification
auto-fails the clarifications item. A blank mandatory item blocks too, on
purpose — submission is gated on positive confirmation, not absence of a flag.
"""
import datetime

import clarification as C

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)


def _all_pass_checks():
    """Every mandatory item stored as an explicit pass — a clean gate."""
    return [{"key": k, "status": "pass"} for k in C.PREFLIGHT_KEYS]


def test_clean_gate_is_ready():
    resolved = C.resolve_preflight(_all_pass_checks(), clarifications=[], now=NOW)
    summary = C.preflight_summary(resolved)
    assert summary["ready"] is True
    assert summary["blocking_count"] == 0


def test_open_clarification_auto_fails_and_blocks():
    resolved = C.resolve_preflight(
        _all_pass_checks(),
        clarifications=[{"status": "Open"}],
        now=NOW,
    )
    clar = next(r for r in resolved if r["key"] == "clarifications_resolved")
    assert clar["status"] == "fail"           # overridden regardless of stored value
    assert C.preflight_summary(resolved)["ready"] is False


def test_expired_credential_auto_fails_even_if_marked_pass():
    checks = _all_pass_checks()
    for c in checks:
        if c["key"] == "cyber_essentials":
            c["expiry_date"] = "2025-10-31"   # long past NOW, but stored as "pass"
    resolved = C.resolve_preflight(checks, clarifications=[], now=NOW)
    cyber = next(r for r in resolved if r["key"] == "cyber_essentials")
    assert cyber["status"] == "fail"
    assert "expired" in cyber["reason"]
    assert C.preflight_summary(resolved)["ready"] is False


def test_blank_mandatory_item_blocks():
    # Drop one mandatory confirmation entirely → it must still block.
    checks = [c for c in _all_pass_checks() if c["key"] != "pcg"]
    resolved = C.resolve_preflight(checks, clarifications=[], now=NOW)
    summary = C.preflight_summary(resolved)
    assert summary["ready"] is False
    assert any(b["key"] == "pcg" for b in summary["blocking"])
