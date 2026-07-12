#!/usr/bin/env python3
"""
"How to supply" reference (G3) — curated, in-app help on the UK public-sector
routes to market, aimed at the novice bidder the tool is built for.

This is **reference content, not a connector**: distilled summaries + source
links for the ways a supplier reaches public buyers (Frameworks, Dynamic
Markets, the legacy DPS, Catalogues, and finding notices under the Procurement
Act 2023). It intentionally holds no live data and touches no DB — api.py serves
`reference()` verbatim behind `GET /api/supply/reference`.

**Facts decay (CLAUDE.md).** Framework codes, statuses and dates move. Every
section carries a `source` link and the whole doc carries `VERIFIED` — the date
the underlying facts were last checked against a live source (see
knowledge/VERIFIED_FACTS.md). Treat it as a signpost to re-verify, never as a
substitute for the live GCA/Find-a-Tender pages. The route *concepts* (what a
framework is, DPS→Dynamic Markets under PA23) are stable; the specific agreement
examples are illustrative and must be re-checked before relying on them in a bid.

Which agreements FWF should actually *pursue* is G2's job (a live radar/scoring
view), deliberately kept out of here so this stays purely educational.
"""

# The date the framework/legislation facts below were last verified against live
# sources — mirrors knowledge/VERIFIED_FACTS.md (as at 2026-07-08). Surfaced in
# the UI so a reader can see how fresh the reference is and re-verify if stale.
VERIFIED = "2026-07-08"

# One honest caveat shown at the top of the view: curated summaries, re-verify
# before relying on any specific code/date/status in a live bid.
DISCLAIMER = (
    "Curated reference, distilled from the sources linked in each section and "
    "verified as at {verified}. Framework codes, dates and statuses change — "
    "always re-check the linked source before relying on a specific agreement in "
    "a live bid."
).format(verified=VERIFIED)

# The routes to market. Each: a novice-readable summary, the key things that
# actually matter when supplying that way, and a source link. `example` is an
# illustrative current agreement (re-verify — see VERIFIED note), omitted where a
# route has no single representative agreement.
ROUTES = [
    {
        "id": "frameworks",
        "title": "Frameworks",
        "summary": (
            "A framework is a pre-vetted list of suppliers that public buyers can "
            "buy from without running a full tender each time. You compete once to "
            "get *onto* the framework; buyers then either award you work directly "
            "or run a mini-competition (a 'call-off') among the suppliers on it."
        ),
        "key_points": [
            "You can usually only join during the framework's application window — "
            "miss it and you wait for the next one (or a mid-term re-opening).",
            "Getting on a framework is not a contract or guaranteed work — it makes "
            "you *eligible* to be awarded call-offs.",
            "Each framework has a scope (lots) and selection criteria (financial "
            "standing, evidence, certifications) you must meet to be admitted.",
            "Most central-government tech buying runs through GCA frameworks.",
        ],
        "example": "G-Cloud 15 (RM1557.15) and Technology Services 4 (RM6190).",
        "source": {"label": "GCA — how to supply", "url": "https://www.gca.gov.uk/how-to-supply"},
    },
    {
        "id": "dynamic-markets",
        "title": "Dynamic Markets",
        "summary": (
            "Dynamic Markets are the Procurement Act 2023 replacement for Dynamic "
            "Purchasing Systems. Like a framework they are a list of qualified "
            "suppliers, but they stay open — you can apply to join at any time, and "
            "new suppliers can be admitted throughout the market's life."
        ),
        "key_points": [
            "Always-open: no single application window, unlike most frameworks.",
            "Introduced by the Procurement Act 2023 (in force 24 February 2025).",
            "Buyers run a competition among the qualified members for each contract.",
            "Good for suppliers who miss a framework window — you can still get in.",
        ],
        "source": {
            "label": "gov.uk — Procurement Act 2023 guidance",
            "url": "https://www.gov.uk/government/collections/transforming-public-procurement",
        },
    },
    {
        "id": "dps",
        "title": "Dynamic Purchasing Systems (DPS)",
        "summary": (
            "A DPS is the older (PCR 2015) always-open supplier list. Under the "
            "Procurement Act 2023, new ones are set up as Dynamic Markets instead — "
            "but DPS arrangements created before the Act continue until they expire, "
            "so you may still meet one."
        ),
        "key_points": [
            "Legacy mechanism — being superseded by Dynamic Markets under PA23.",
            "Existing DPS keep running under their original (PCR 2015) rules.",
            "Function is the same idea as a Dynamic Market: qualify, then compete.",
        ],
        "source": {
            "label": "gov.uk — Transforming public procurement",
            "url": "https://www.gov.uk/government/collections/transforming-public-procurement",
        },
    },
    {
        "id": "catalogues",
        "title": "Catalogues",
        "summary": (
            "Some routes let buyers browse and buy listed services directly from an "
            "online catalogue, rather than running a competition. You publish your "
            "services and prices; buyers search, compare and award. G-Cloud's "
            "Digital Marketplace is the best-known example."
        ),
        "key_points": [
            "You list services + day rates / prices against defined lots.",
            "Buyers award by searching and shortlisting against their requirement.",
            "Keep listings accurate — an out-of-date price or capability loses work.",
        ],
        "example": "The G-Cloud Digital Marketplace (cloud hosting, software, support).",
        "source": {
            "label": "GCA — agreements (frameworks & catalogues)",
            "url": "https://www.gca.gov.uk/agreements",
        },
    },
    {
        "id": "finding-notices",
        "title": "Finding opportunities & notices",
        "summary": (
            "Under the Procurement Act 2023, tender and contract notices publish to "
            "a central digital platform. Find a Tender is the main place to see UK "
            "public-sector opportunities; the devolved nations also run their own "
            "portals (Public Contracts Scotland, Sell2Wales, eTendersNI)."
        ),
        "key_points": [
            "Register as a supplier and set up alerts so opportunities come to you.",
            "This tool already searches Find a Tender, Contracts Finder, Public "
            "Contracts Scotland and Sell2Wales for you — see the Search stage.",
            "Notices tell you the deadline, scope and how to respond — read the whole "
            "notice before deciding to bid.",
        ],
        "source": {"label": "Find a Tender", "url": "https://www.find-tender.service.gov.uk/"},
    },
]

# A short, ordered "getting started" path for someone who has never bid — the
# novice on-ramp. Deliberately generic and route-agnostic.
GETTING_STARTED = [
    "Get your basics in order: company registration, accounts, insurances and any "
    "certifications buyers ask for (e.g. Cyber Essentials, ISO 27001) — these live "
    "in the Compliance & Renewals register.",
    "Register on Find a Tender (and the devolved portals if you sell there) and set "
    "up alerts for your service area.",
    "Identify the frameworks and dynamic markets that match what you sell, and note "
    "their application windows.",
    "Watch for opportunities in the Search stage, triage them (bid / no-bid), and "
    "plan the ones worth pursuing.",
    "Build a library of reusable answers and evidence so each bid gets faster — the "
    "Complete stage drafts from it.",
]

# Where to go to learn more / do the actual registrations. Help resources, per G3.
HELP_LINKS = [
    {"label": "GCA — how to supply to government", "url": "https://www.gca.gov.uk/how-to-supply"},
    {"label": "GCA — live agreements (frameworks, DPS, dynamic markets)", "url": "https://www.gca.gov.uk/agreements"},
    {"label": "Find a Tender — search & register", "url": "https://www.find-tender.service.gov.uk/"},
    {"label": "Contracts Finder", "url": "https://www.contractsfinder.service.gov.uk/"},
    {"label": "gov.uk — Procurement Act 2023 (Transforming Public Procurement)", "url": "https://www.gov.uk/government/collections/transforming-public-procurement"},
]


def reference():
    """The full 'how to supply' reference payload, served verbatim by the API.

    Static/curated — no DB, no live fetch (see module docstring). `verified` lets
    the UI show how fresh the underlying facts are, honouring the facts-decay rule."""
    return {
        "verified": VERIFIED,
        "disclaimer": DISCLAIMER,
        "routes": ROUTES,
        "getting_started": GETTING_STARTED,
        "help_links": HELP_LINKS,
    }


if __name__ == "__main__":  # quick manual inspection
    import json

    print(json.dumps(reference(), indent=2))
