#!/usr/bin/env python3
"""
FWF's FOR002 Bid Plan rig — the Plan (Stage 3) domain logic.

Like qualification.py for Triage, this is NOT invented: the vocabulary is lifted
from FWF's real `FOR002 BidPlan Timeline` + `Tender Pipeline.xlsx`
(docs/design/data-model.md §3). db.py persists a plan record; this module
supplies the fixed vocabularies and the two cross-bid computations the Plan board
performs:
  - capacity_summary(items, capacity_days) — committed bid-effort vs team capacity.
  - alerts(items, capacity_days, now)      — the deadline/owner/capacity warnings,
    including the missed-clarification alert this whole tool exists to prevent.

A BidPlan has two parts (data-model.md §3):
  (a) pipeline position — where the bid sits on the board (Tender Pipeline.xlsx).
  (b) the FOR002 phase timeline — the fixed, ordered phase list that gives a real
      critical path / calendar.

Kept here (not in db.py) for the same reason as qualification.py: db.py is
persistence; the domain tables live beside it.
"""
import datetime

# (a) Pipeline position — the board's columns. FWF's Tender Pipeline.xlsx uses
# ad-hoc strings ("Pre-Tender", "Open Tender", "Closed"); a bid only reaches Plan
# AFTER a Go, so the pre-qualification states drop away and what's left is the
# operational path a live bid moves through (matches the approved mockup board).
# Text-tolerant per the PoC — this is the suggested enum, not a hard constraint.
PIPELINE_STAGES = ["Qualifying", "Kick-off", "Drafting", "In review", "Submitted", "Closed"]

# A bid is "committed work" (counts against capacity) until it's off the board.
PIPELINE_DONE = {"Submitted", "Closed"}

# (b) FOR002 phase timeline — the fixed, ordered phase list, copied from the
# FOR002 BidPlan Timeline sheet (data-model.md §3b). These phases + their
# dependencies are what give a real critical path.
FOR002_PHASES = [
    "Opportunity Release", "Opp/Doc Review", "Bid/No-Bid Decision", "Kick-Off",
    "Stakeholders", "Win themes", "Section ownership", "Identify CQs",
    "Solution Design", "Draft 1", "Red Review", "Draft 2", "Gold Review",
    "Submission", "Post-submission",
]

# FOR002 owner roles (the sheet's owner column vocabulary).
OWNER_ROLES = ["Bid Manager", "Sales Lead", "Solution Lead", "Writers",
               "Review Team", "Senior Stakeholders"]

# Per-phase progress states (drives the timeline board).
PHASE_STATUSES = ["Not started", "In progress", "Done", "Blocked"]

# Team bid-writing capacity over the planning horizon, in person-days. FWF runs a
# small bid team; this is the default the capacity bar measures commitment
# against (the UI can override it). Deliberately a round default, not a false
# precision — the point is to surface over-commitment, not to forecast exactly.
# A couple of concurrent Med/High bids (16.5–24d each on the FOR001 rig) will
# tip a team this size over, which is exactly the trade-off Planning surfaces.
DEFAULT_TEAM_CAPACITY_DAYS = 25

# A deadline this many days out (or nearer) is "imminent" and raises an alert.
IMMINENT_DAYS = 7


def default_phases():
    """The FOR002 timeline seeded blank — one row per fixed phase, ready for the
    planner to assign owners and dates. Never persisted until the user saves."""
    return [
        {"phase": p, "owner": "", "start_date": "", "completion_date": "",
         "status": "Not started", "comments": ""}
        for p in FOR002_PHASES
    ]


def _parse_date(value):
    """Lenient date parse for the mixed formats FWF's forms carry. Accepts an ISO
    date/datetime; returns a date, or None if unparseable/blank."""
    if not value:
        return None
    s = str(value).strip()
    try:
        return datetime.datetime.fromisoformat(s).date()
    except ValueError:
        # Fall back to a plain date prefix (e.g. "2026-08-14T..." already handled;
        # this catches "2026-08-14 ..." style).
        try:
            return datetime.date.fromisoformat(s[:10])
        except ValueError:
            return None


def days_until(value, now=None):
    """Whole days from `now` until a deadline (negative = already passed), or None
    if the date is missing/unparseable. `now` defaults to today (UTC)."""
    d = _parse_date(value)
    if d is None:
        return None
    today = (now or datetime.datetime.now(datetime.timezone.utc)).date()
    return (d - today).days


def capacity_summary(items, capacity_days=DEFAULT_TEAM_CAPACITY_DAYS):
    """Committed bid-writing effort vs team capacity.

    `items` are board rows (see api.py); only bids still in flight (pipeline stage
    not in PIPELINE_DONE) count as committed work. Returns the numbers the
    capacity bar renders, including whether the team is over-committed — the
    "something has to give" signal Planning exists to give.
    """
    committed = sum(
        (it.get("effort_days") or 0)
        for it in items if it.get("pipeline_stage") not in PIPELINE_DONE
    )
    over = committed > capacity_days
    return {
        "committed_days": committed,
        "capacity_days": capacity_days,
        "remaining_days": capacity_days - committed,
        "over": over,
        # Bar fill: clamp to 100% (over-commitment is shown by the `over` flag +
        # the negative remaining, not by a bar wider than its track).
        "pct": min(100, round((committed / capacity_days) * 100)) if capacity_days else 0,
    }


def alerts(items, capacity_days=DEFAULT_TEAM_CAPACITY_DAYS, now=None):
    """The Plan board's warnings, computed from real bid data. Ordered
    most-urgent first. Each: {level: crit|warn, text, bid_id?}.

    The clarification-deadline alerts are the reason this tool exists — a missed
    clarification is the admin failure that killed the G-Cloud 15 bid.
    """
    out = []
    for it in items:
        if it.get("pipeline_stage") in PIPELINE_DONE:
            continue  # off the board — no live deadline to chase
        title = it.get("title") or f"Bid {it.get('bid_id')}"
        bid_id = it.get("bid_id")

        # Clarification deadline — the founding-failure signal.
        cd = it.get("days_to_clarification")
        if cd is not None:
            if cd < 0:
                out.append({"level": "crit", "bid_id": bid_id,
                            "text": f"{title}: clarification deadline PASSED {abs(cd)}d ago"})
            elif cd <= IMMINENT_DAYS:
                out.append({"level": "crit", "bid_id": bid_id,
                            "text": f"{title}: clarification deadline in {cd}d"})

        # Submission deadline — missed, or imminent with nobody on it.
        sd = it.get("days_to_submission")
        if sd is not None:
            if sd < 0:
                out.append({"level": "crit", "bid_id": bid_id,
                            "text": f"{title}: submission deadline PASSED {abs(sd)}d ago"})
            elif sd <= IMMINENT_DAYS and not it.get("owner"):
                out.append({"level": "crit", "bid_id": bid_id,
                            "text": f"{title}: closes in {sd}d and has no owner assigned"})
            elif sd <= IMMINENT_DAYS:
                out.append({"level": "warn", "bid_id": bid_id,
                            "text": f"{title}: closes in {sd}d"})
            elif not it.get("owner"):
                out.append({"level": "warn", "bid_id": bid_id,
                            "text": f"{title}: no owner assigned"})

    cap = capacity_summary(items, capacity_days)
    if cap["over"]:
        out.insert(0, {"level": "crit",
                       "text": f"Team over-committed by {cap['committed_days'] - cap['capacity_days']:g} "
                               f"days ({cap['committed_days']:g} committed vs {cap['capacity_days']:g} capacity) "
                               f"— something has to give"})

    # Crit before warn, otherwise input order (which is bid order).
    out.sort(key=lambda a: 0 if a["level"] == "crit" else 1)
    return out


def reference():
    """The full FOR002 vocabulary for the UI to render the Plan board + timeline."""
    return {
        "pipeline_stages": PIPELINE_STAGES,
        "pipeline_done": sorted(PIPELINE_DONE),
        "phases": FOR002_PHASES,
        "owner_roles": OWNER_ROLES,
        "phase_statuses": PHASE_STATUSES,
        "default_capacity_days": DEFAULT_TEAM_CAPACITY_DAYS,
        "imminent_days": IMMINENT_DAYS,
    }


if __name__ == "__main__":
    print("FOR002 pipeline stages:", " → ".join(PIPELINE_STAGES))
    print(f"FOR002 phases ({len(FOR002_PHASES)}):")
    for p in FOR002_PHASES:
        print(f"  · {p}")
