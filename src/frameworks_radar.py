#!/usr/bin/env python3
"""
G2 — Framework opportunity radar: which public-sector agreements FWF should join.

Turns the static framework prose in knowledge/VERIFIED_FACTS.md into a live,
scored view. For each candidate GCA agreement relevant to FWF's IT/software
scope we hold the *curated facts* (dates, membership, fit, source) but compute
the *lifecycle and the recommendation live against today* — so an agreement that
has expired, or a re-entry window that has opened, is reflected the moment it
happens rather than baked into a stale label.

Honesty rules this file lives by (CLAUDE.md — facts decay; precedent: RM6263 was
already expired when a recovery plan still listed it):
  - Every agreement carries a `source` (its GCA page) and the whole doc a
    `VERIFIED` date. Dates known to be projections are marked `projection` so the
    UI can flag them — FWF's G-Cloud re-entry dates are explicitly projections.
  - Lifecycle (upcoming/live/expiring/expired) and the entry-window state are
    DERIVED from the dates against `today`, never stored.
  - FWF's own membership is an internal fact not web-verifiable here; it's marked
    with `confidence` so the UI can say "confirm on the Digital Marketplace".
    (G1's own-awards data can corroborate membership later.)

No DB, no live fetch — api.py serves `radar()` behind GET /api/frameworks/radar.
Which agreement a live bid actually goes through must still be checked against the
agreement's GCA page; this radar is the prioritiser, not the source of truth.
"""
import datetime

# Date the underlying agreement facts were last verified (mirrors VERIFIED_FACTS.md).
VERIFIED = "2026-07-08"

# An agreement expiring within this many days is "expiring" (act-now territory) —
# same 90-day horizon the compliance register uses, so "expiring soon" means one
# thing across the app.
EXPIRING_SOON_DAYS = 90

DISCLAIMER = (
    "Curated from GCA agreement pages and knowledge/VERIFIED_FACTS.md, verified as "
    "at {v}. Lifecycle and recommendations are computed live against today, but "
    "dates marked 'projection' are estimates — confirm against the agreement's GCA "
    "page before acting. Framework membership shown for FWF is an internal fact to "
    "confirm on the Digital Marketplace."
).format(v=VERIFIED)

# The candidate agreements, FWF-scope (IT / software / digital services). `dates`
# values may be tagged as projections via `projection_dates`. `fwf_status` is one
# of member / not_member / unknown; `confidence` qualifies a claimed membership.
AGREEMENTS = [
    {
        "id": "RM1557.15",
        "name": "G-Cloud 15",
        "category": "Framework",
        "fit": "Cloud hosting, software and cloud support — FWF's core catalogue scope.",
        "live_from": "2026-09-01",           # "autumn 2026" go-live (approx)
        "expires": "2030-09-01",             # ~4-year framework
        "entry_window": {"opens": "2028-03-01", "closes": "2028-04-30"},  # projection
        "projection_dates": ["live_from", "expires", "entry_window"],
        "fwf_status": "not_member",
        "confidence": None,
        "notes": "The successor to G-Cloud 14. Open framework with mid-term "
                 "re-opening windows; FWF's specific re-entry dates are projections "
                 "— confirm against the published framework calendar when live.",
        "source": {"label": "GCA — RM1557.15 G-Cloud 15", "url": "https://www.gca.gov.uk/agreements/RM1557.15"},
    },
    {
        "id": "RM1557.14",
        "name": "G-Cloud 14",
        "category": "Framework",
        "fit": "FWF's current cloud route to market — the place today's call-offs run.",
        "live_from": "2024-10-29",
        "expires": "2026-10-28",
        "entry_window": None,                # closed framework generation
        "projection_dates": [],
        "fwf_status": "member",
        "confidence": "internal fact — confirm on the Digital Marketplace listing",
        "notes": "FWF is listed on G-Cloud 14. It expires 28 Oct 2026, so securing a "
                 "G-Cloud 15 place is the continuity action.",
        "source": {"label": "GCA — RM1557.14 G-Cloud 14", "url": "https://www.gca.gov.uk/agreements/RM1557.14"},
    },
    {
        "id": "RM6190",
        "name": "Technology Services 4",
        "category": "Framework",
        "fit": "Broad tech-services scope incl. application development, data and "
               "transformation — strong fit for FWF's delivery work.",
        "live_from": "2025-12-12",
        "expires": "2033-12-12",             # "up to 8 years"
        "entry_window": None,
        "projection_dates": ["expires"],
        "fwf_status": "not_member",
        "confidence": None,
        "notes": "Live since 12 Dec 2025 (replaced RM6100 TS3). The strongest "
                 "confirmed live route during the G-Cloud 14→15 gap.",
        "source": {"label": "GCA — RM6190 Technology Services 4", "url": "https://www.gca.gov.uk/agreements/RM6190"},
    },
    {
        "id": "DOS7",
        "name": "Digital Outcomes and Specialists 7",
        "category": "Framework",
        "fit": "Digital specialists / outcomes — the live successor to RM6263, in FWF scope.",
        "live_from": None,                   # in development; go-live TBC
        "expires": None,
        "entry_window": None,
        "projection_dates": [],
        "fwf_status": "unknown",
        "confidence": None,
        "notes": "Development started 30 Jul 2024; assess DOS7 in place of the "
                 "expired RM6263. Track for its ITT/go-live.",
        "source": {"label": "GCA — Digital Outcomes and Specialists", "url": "https://www.gca.gov.uk/agreements"},
    },
    {
        "id": "RM6263",
        "name": "Digital Specialists and Programmes",
        "category": "Framework",
        "fit": "Digital specialists — but superseded; kept as a documented dead end.",
        "live_from": "2021-03-08",
        "expires": "2026-03-07",             # both 12-month extensions used
        "entry_window": None,
        "projection_dates": [],
        "fwf_status": "not_member",
        "confidence": None,
        "notes": "Expired 7 Mar 2026 (both extensions used). Do NOT pursue — assess "
                 "DOS7 instead. Listed so the radar shows the dead route explicitly.",
        "source": {"label": "GCA — RM6263", "url": "https://www.gca.gov.uk/agreements/RM6263"},
    },
]


def _parse(iso):
    """ISO date (or None/blank) → date, or None if absent/unparseable."""
    if not iso:
        return None
    try:
        return datetime.date.fromisoformat(str(iso)[:10])
    except ValueError:
        return None


def _days_between(target, today):
    """Whole days from today to target date (negative = past), or None."""
    d = _parse(target)
    return (d - today).days if d else None


def _entry_window_state(window, today):
    """open / upcoming / closed / none — the state of a re-entry window today."""
    if not window:
        return "none"
    opens, closes = _parse(window.get("opens")), _parse(window.get("closes"))
    if opens and today < opens:
        return "upcoming"
    if closes and today > closes:
        return "closed"
    if opens or closes:
        return "open"
    return "none"


def assess(agreement, today):
    """Return a copy of `agreement` with live-derived fields: `lifecycle`,
    `days_to_expiry`, `entry_window_state`, `recommendation` (act/pursue/prepare/
    maintain/watch/skip) and human `reasons`. Nothing is stored — all computed."""
    a = dict(agreement)
    days = _days_between(a.get("expires"), today)
    live_in = _days_between(a.get("live_from"), today)
    window_state = _entry_window_state(a.get("entry_window"), today)

    # Lifecycle from the dates.
    if days is not None and days < 0:
        lifecycle = "expired"
    elif live_in is not None and live_in > 0:
        lifecycle = "upcoming"
    elif days is not None and days <= EXPIRING_SOON_DAYS:
        lifecycle = "expiring"
    elif a.get("live_from") or a.get("expires"):
        lifecycle = "live"
    else:
        lifecycle = "unknown"

    member = a.get("fwf_status") == "member"
    reasons = []

    if lifecycle == "expired":
        rec = "skip"
        reasons.append(f"Expired {a.get('expires')} — no longer a route.")
    elif member and lifecycle == "expiring":
        rec = "act"
        reasons.append(f"FWF is a member but it expires in {days}d — secure the successor place now.")
    elif member:
        rec = "maintain"
        reasons.append("FWF is already a member — maintain the listing.")
    elif lifecycle == "upcoming":
        rec = "prepare"
        reasons.append(f"Opens {a.get('live_from')} ({live_in}d) — prepare to apply.")
    elif lifecycle == "unknown":
        rec = "watch"
        reasons.append("Dates not yet published — track for the ITT / go-live.")
    elif window_state == "open":
        rec = "pursue"
        reasons.append("Live and a re-entry window is open — apply now.")
    elif window_state == "upcoming":
        rec = "prepare"
        reasons.append(f"Live; next entry window opens {a['entry_window'].get('opens')}.")
    else:
        rec = "pursue"
        reasons.append("Live and in FWF's scope — pursue admission (check the next entry route).")

    if days is not None and 0 <= days <= EXPIRING_SOON_DAYS and lifecycle != "expired":
        reasons.append(f"Expires in {days}d.")
    if a.get("confidence"):
        reasons.append(a["confidence"])

    a["lifecycle"] = lifecycle
    a["days_to_expiry"] = days
    a["entry_window_state"] = window_state
    a["recommendation"] = rec
    a["reasons"] = reasons
    return a


# Recommendations ranked by urgency, so the board sorts most-actionable first.
_REC_RANK = {"act": 0, "pursue": 1, "prepare": 2, "watch": 3, "maintain": 4, "skip": 5}


def radar(today=None):
    """The full framework radar: every candidate agreement assessed against today,
    most-actionable first, plus a recommendation summary. `today` defaults to the
    real current date (the one place this reads the clock)."""
    today = today or datetime.date.today()
    assessed = [assess(a, today) for a in AGREEMENTS]
    assessed.sort(key=lambda a: (_REC_RANK.get(a["recommendation"], 9), a.get("days_to_expiry") is None,
                                 a.get("days_to_expiry") if a.get("days_to_expiry") is not None else 1 << 30))
    summary = {}
    for a in assessed:
        summary[a["recommendation"]] = summary.get(a["recommendation"], 0) + 1
    return {
        "verified": VERIFIED,
        "disclaimer": DISCLAIMER,
        "as_of": today.isoformat(),
        "expiring_soon_days": EXPIRING_SOON_DAYS,
        "agreements": assessed,
        "summary": summary,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(radar(), indent=2))
