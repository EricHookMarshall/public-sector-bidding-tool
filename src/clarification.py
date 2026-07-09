#!/usr/bin/env python3
"""
FWF's FOR003 CQLOG rig — the Manage (Stage 5) domain logic.

Like qualification.py (Triage) and bidplan.py (Plan), this is NOT invented: the
clarification register is FWF's real `FOR003 CQLOG` (clarification log) and the
pre-flight gate is the Governance tracker's "Compliance Matrix / Bid Submission
Checklist" (docs/design/data-model.md §5 and §5b). db.py persists a per-bid
manage record; this module supplies the fixed vocabularies and the cross-bid
computations the Manage board performs:
  - alerts(items, now)              — the clarification-deadline / owner warnings.
  - resolve_preflight(checks, ...)  — the pre-flight gate, with the auto-derived
    and expiry-driven items resolved to an effective pass/fail.
  - preflight_summary(...)          — the gate readout (ready to submit or blocked).

This is the stage the whole tool exists for: a missed clarification is the admin
failure that killed the G-Cloud 15 bid. The register captures every buyer
clarification with an owner, a *backup*, and a real deadline (date + time + tz),
and the gate blocks submission when a mandatory item is missing or a document has
expired — the "facts decay" principle from knowledge/VERIFIED_FACTS.md made into
a gate.

Kept here (not in db.py) for the same reason as qualification.py / bidplan.py:
db.py is persistence; the domain vocabulary lives beside it.
"""
import datetime

# bidplan owns the lenient date maths (days-to-deadline); Manage races the same
# kind of deadline, so it reuses that one utility rather than re-deriving it.
from bidplan import days_until

# FOR003 clarification lifecycle. A clarification is raised (Open), written up
# (Drafting), sent to the buyer (Submitted), then the buyer replies (Answered).
# The deadline that matters is the buyer's window to RECEIVE questions — so a
# clarification still racing that window is one that hasn't been Submitted yet.
CLARIFICATION_STATUSES = ["Open", "Drafting", "Submitted", "Answered"]

# Still racing the buyer's clarification deadline (not yet sent).
PENDING_SUBMISSION = {"Open", "Drafting"}
# Fully resolved for the pre-flight gate (buyer has replied).
RESOLVED_STATUSES = {"Answered"}

# A deadline this many days out (or nearer) is "imminent" and raises an alert.
# Matches bidplan.IMMINENT_DAYS so Plan and Manage speak the same urgency.
IMMINENT_DAYS = 7

# Pre-flight gate template (docs/design/data-model.md §5b). One row per required
# check. `auto` items are derived by the tool (not ticked by hand); `expiry`
# items carry a date and auto-fail once past it (the expired-cert failure this
# tool exists to catch). `mandatory` items block submission unless passed or
# explicitly marked N/A; a non-mandatory item is advisory. The list is the
# suggested set, text-tolerant per the PoC — a real bid can mark items N/A.
PREFLIGHT_ITEMS = [
    {"key": "clarifications_resolved", "label": "All buyer clarifications resolved",
     "category": "Clarifications", "auto": True, "mandatory": True},
    {"key": "responses_complete", "label": "All tender questions answered & within word count",
     "category": "Response", "mandatory": True},
    {"key": "social_value", "label": "Social Value / PPN 06/20 content present",
     "category": "Mandatory content", "mandatory": True},
    {"key": "carbon_plan", "label": "Carbon Reduction Plan in date (required if >£5m)",
     "category": "Mandatory content", "expiry": True, "mandatory": True},
    {"key": "cyber_essentials", "label": "Cyber Essentials certificate in date",
     "category": "Credentials", "expiry": True, "mandatory": True},
    {"key": "modern_slavery", "label": "Modern Slavery statement present",
     "category": "Mandatory content", "mandatory": True},
    {"key": "uk_gdpr", "label": "UK GDPR / data-protection compliance",
     "category": "Mandatory content", "mandatory": True},
    {"key": "pcg", "label": "Arobs parent company guarantee attached",
     "category": "Commercial", "mandatory": True},
    {"key": "deadline_captured", "label": "Submission deadline captured with time + timezone",
     "category": "Governance", "mandatory": True},
]
PREFLIGHT_KEYS = {c["key"] for c in PREFLIGHT_ITEMS}

# Per-check status values. "" (blank) = not yet confirmed → still blocks the gate.
PREFLIGHT_STATUSES = ["pass", "fail", "na"]


def default_clarification():
    """A blank FOR003 register row — the fields the planner fills for one buyer
    clarification. `deadline_note` carries the time + timezone alongside the
    date-only `buyer_deadline`, so the detail that was lost on G-Cloud 15 (the
    exact cut-off) is captured, not rounded away."""
    return {
        "question_number": "", "question": "", "channel": "",
        "owner": "", "backup_owner": "",
        "buyer_deadline": "", "deadline_note": "",
        "date_submitted": "", "response_date": "", "buyer_response": "",
        "status": "Open", "notes": "",
    }


def default_preflight():
    """The pre-flight checklist seeded blank — one row per PREFLIGHT_ITEMS entry,
    every check pending (blank status). Never persisted until the user saves."""
    return [
        {"key": it["key"], "status": "", "note": "", "expiry_date": ""}
        for it in PREFLIGHT_ITEMS
    ]


def clarification_view(c, now=None):
    """One register row enriched with the derived fields the UI reads: the
    days-to-deadline count and whether it's still racing the buyer's window."""
    pending = (c.get("status") or "Open") in PENDING_SUBMISSION
    return {
        **c,
        "days_to_deadline": days_until(c.get("buyer_deadline"), now),
        "pending": pending,
        "resolved": (c.get("status") or "") in RESOLVED_STATUSES,
    }


def resolve_preflight(checks, clarifications, now=None):
    """Resolve the stored pre-flight checks into their EFFECTIVE state.

    Two kinds of item aren't taken at face value:
      - `auto` items are computed by the tool. `clarifications_resolved` passes
        only when every clarification is Answered (or there are none) — a raw,
        honest read of the register, not a box someone ticked.
      - `expiry` items auto-fail once their `expiry_date` is past, whatever the
        stored status says — the expired-certificate failure, enforced.

    Returns one dict per PREFLIGHT_ITEMS entry (template order), each carrying the
    template metadata + effective `status` and a `reason` where the tool overrode
    the stored value.
    """
    by_key = {c.get("key"): c for c in (checks or []) if c.get("key")}
    unresolved = [c for c in (clarifications or [])
                  if (c.get("status") or "Open") not in RESOLVED_STATUSES]

    out = []
    for item in PREFLIGHT_ITEMS:
        stored = by_key.get(item["key"], {})
        status = stored.get("status") or ""
        reason = ""

        if item.get("auto") and item["key"] == "clarifications_resolved":
            if unresolved:
                status, reason = "fail", f"{len(unresolved)} clarification(s) still open"
            else:
                status, reason = "pass", "no open clarifications"

        elif item.get("expiry") and stored.get("expiry_date"):
            d = days_until(stored["expiry_date"], now)
            if d is not None and d < 0:
                status, reason = "fail", f"expired {abs(d)}d ago"
            elif d is not None and d <= IMMINENT_DAYS:
                # Not yet a hard fail, but flag it — a cert expiring mid-bid is
                # the same failure a week early.
                reason = f"expires in {d}d"

        out.append({**item, "status": status,
                    "expiry_date": stored.get("expiry_date", ""),
                    "note": stored.get("note", ""), "reason": reason})
    return out


def preflight_summary(resolved):
    """The gate readout from resolved pre-flight checks (see resolve_preflight).

    `blocking` lists every mandatory item that isn't passed or N/A — a blank
    (unconfirmed) mandatory item blocks too, on purpose: submission is gated on
    positive confirmation, not on the absence of a red flag. `ready` is true only
    when nothing blocks.
    """
    passed = sum(1 for c in resolved if c["status"] == "pass")
    na = sum(1 for c in resolved if c["status"] == "na")
    blocking = [c for c in resolved
                if c.get("mandatory") and c["status"] not in ("pass", "na")]
    return {
        "total": len(resolved),
        "passed": passed,
        "na": na,
        "blocking": [{"key": c["key"], "label": c["label"],
                      "reason": c.get("reason") or ("failed" if c["status"] == "fail" else "not confirmed")}
                     for c in blocking],
        "blocking_count": len(blocking),
        "ready": len(blocking) == 0,
    }


def alerts(items, now=None):
    """The Manage board's warnings, computed from the real registers. Ordered
    most-urgent first. Each: {level: crit|warn, text, bid_id?}.

    The clarification-deadline alerts are the founding-failure signal — a missed
    clarification is the admin failure that killed the G-Cloud 15 bid.
    """
    out = []
    for it in items:
        title = it.get("title") or f"Bid {it.get('bid_id')}"
        bid_id = it.get("bid_id")
        if it.get("submitted"):
            continue  # already submitted — the register is history now

        for c in it.get("clarifications", []):
            if not c.get("pending"):
                continue  # already sent / answered — no window left to miss
            d = c.get("days_to_deadline")
            label = c.get("question_number") or (c.get("question") or "clarification")[:40]
            if d is None:
                if not c.get("owner"):
                    out.append({"level": "warn", "bid_id": bid_id,
                                "text": f"{title}: clarification “{label}” has no deadline and no owner"})
                continue
            if d < 0:
                out.append({"level": "crit", "bid_id": bid_id,
                            "text": f"{title}: clarification “{label}” deadline PASSED {abs(d)}d ago"})
            elif d <= IMMINENT_DAYS and not c.get("owner"):
                out.append({"level": "crit", "bid_id": bid_id,
                            "text": f"{title}: clarification “{label}” due in {d}d with no owner"})
            elif d <= IMMINENT_DAYS:
                out.append({"level": "warn", "bid_id": bid_id,
                            "text": f"{title}: clarification “{label}” due in {d}d"})

        # A live bid whose submission is near but whose pre-flight gate is still
        # blocked — the "you're about to submit something incomplete" warning.
        sd = it.get("days_to_submission")
        pf = it.get("preflight")
        if sd is not None and 0 <= sd <= IMMINENT_DAYS and pf and not pf.get("ready"):
            out.append({"level": "crit", "bid_id": bid_id,
                        "text": f"{title}: closes in {sd}d but pre-flight is blocked "
                                f"({pf['blocking_count']} item(s) outstanding)"})

    out.sort(key=lambda a: 0 if a["level"] == "crit" else 1)
    return out


def reference():
    """The full FOR003 / pre-flight vocabulary for the UI to render Manage."""
    return {
        "clarification_statuses": CLARIFICATION_STATUSES,
        "pending_submission": sorted(PENDING_SUBMISSION),
        "resolved_statuses": sorted(RESOLVED_STATUSES),
        "preflight_items": PREFLIGHT_ITEMS,
        "preflight_statuses": PREFLIGHT_STATUSES,
        "imminent_days": IMMINENT_DAYS,
    }


if __name__ == "__main__":
    print("FOR003 clarification statuses:", " → ".join(CLARIFICATION_STATUSES))
    print(f"Pre-flight checklist ({len(PREFLIGHT_ITEMS)} items):")
    for it in PREFLIGHT_ITEMS:
        flags = []
        if it.get("auto"):
            flags.append("auto")
        if it.get("expiry"):
            flags.append("expiry")
        if not it.get("mandatory"):
            flags.append("advisory")
        tag = f"  [{', '.join(flags)}]" if flags else ""
        print(f"  · {it['label']}{tag}")
