#!/usr/bin/env python3
"""
FWF's FOR001 Bid Qualification rig — the Triage (Stage 2) domain logic.

This is NOT invented: every constant here is lifted from FWF's real
`FOR001 Bid Qualification Questionnaire.xlsx` (mirrored under
`knowledge/SharePoint Folder/Bids/01 Bid Forms/`, gitignored). The `Reference`
sheet holds FWF's actual "cost to chase" scoring rig; the `Qualification` sheet
holds the fixed delivery-team role set and the Win-Qualification RAG criteria.

db.py persists a qualification record; this module supplies the fixed
vocabularies and the two computations the form performs:
  - compute_bid_economics(complexity) — complexity → bid-writing effort & cost.
  - rag_summary(scores)               — the RAG criteria → an overall rating.

Keeping this here (not in db.py) mirrors cpv_catalog.py / regions.py: db.py is
persistence, the domain tables live beside it. See docs/design/data-model.md §2.
"""

# £/day. FOR001 Reference sheet prices every bid-writing role at a flat £500/day.
DAY_RATE = 500

# The complexity axis, low → high (FOR001 Reference sheet column headers).
COMPLEXITY_LEVELS = ["Low", "Low-Med", "Medium", "Med-High", "High"]

# Bid-writing effort in person-days, per role per complexity — copied cell-for-cell
# from FOR001's Reference sheet. This is FWF's real "cost to chase" model: pick a
# complexity, sum the column, multiply by DAY_RATE. Column totals (for reference):
#   Low 9d/£4,500 · Low-Med 13.5d/£6,750 · Medium 16.5d/£8,250 ·
#   Med-High 19.5d/£9,750 · High 24d/£12,000.
# Planning (Stage 3) reads the resulting cost to weigh a bid against team capacity.
BID_EFFORT_DAYS = {
    "Bid Manager":          {"Low": 2,   "Low-Med": 3,   "Medium": 4,   "Med-High": 5,   "High": 6},
    "Technical Author":     {"Low": 1,   "Low-Med": 2,   "Medium": 2.5, "Med-High": 3,   "High": 4},
    "Delivery Author":      {"Low": 1,   "Low-Med": 1.5, "Medium": 2,   "Med-High": 2.5, "High": 3},
    "Presentation & Demo":  {"Low": 4,   "Low-Med": 5,   "Medium": 6,   "Med-High": 7,   "High": 8},
    "Contract Negotiation": {"Low": 1,   "Low-Med": 2,   "Medium": 2,   "Med-High": 2,   "High": 3},
}

# FOR001 pricing models and the bid/no-bid decision values (Reference sheet enums).
PRICING_MODELS = ["Fixed", "T&M", "Risk Reward"]
DECISIONS = ["Go", "No go"]

# FOR001 "Delivery Team Required" fixed role set. The form seeds a per-role count
# + comments; a promoted qualification carries this as its resourcing sketch.
DELIVERY_ROLES = [
    "Project Manager", "Solution Architect", "Business Analyst",
    "Developer", "Power BI Developer", "UX Designer",
]

# FOR001 "Win Qualification" block — each criterion scored 1 / 2 / 3.
# FWF scores these as a confidence/green rating: 3 = strong (low risk),
# 1 = weak (high risk). `hint` records the poles the form spells out where it
# does (the account-relationship criterion is the only one FWF annotates).
RAG_CRITERIA = [
    {"key": "bid_team_forecast",         "label": "Bid team forecast completed?"},
    {"key": "time_and_staff_to_respond", "label": "Time & staff to respond adequately?"},
    {"key": "staff_to_deliver",          "label": "Staff to deliver?"},
    {"key": "account_relationship",      "label": "Account relationship?",
     "hint": "1 = new account / no relationship · 2 = new account, some relationship · 3 = existing account with relationship"},
    {"key": "social_value_alignment",    "label": "Social value alignment?"},
    {"key": "strength_of_competition",   "label": "Strength of competition?"},
    {"key": "commercially_viable",       "label": "Commercially viable?"},
    {"key": "budget_secured",            "label": "Budget available or secured?"},
    {"key": "price_sensitive",           "label": "Price sensitive / non-standard?"},
    {"key": "ts_and_cs_available",       "label": "Ts & Cs availability?"},
]
RAG_CRITERIA_KEYS = {c["key"] for c in RAG_CRITERIA}


# The bid-writing roles that carry a day rate, in FOR001 order. £500 flat is the
# FOR001 default; a team can override each role in Settings (persisted in bids.db,
# see db.get_setting("day_rates")) so the "cost to chase" reflects real rates.
DAY_RATE_ROLES = list(BID_EFFORT_DAYS)
DEFAULT_DAY_RATES = {role: DAY_RATE for role in DAY_RATE_ROLES}


def resolve_day_rates(stored):
    """Merge a stored partial {role: £/day} over the FOR001 defaults, keeping only
    known roles with a positive number. A blank/None/garbage store → all defaults,
    so a missing or half-filled setting never breaks the economics."""
    rates = dict(DEFAULT_DAY_RATES)
    if isinstance(stored, dict):
        for role in DAY_RATE_ROLES:
            v = stored.get(role)
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if v > 0:
                rates[role] = v
    return rates


def compute_bid_economics(complexity, rates=None):
    """Complexity → the FOR001 bid-writing effort/cost breakdown.

    Returns a dict: {complexity, day_rate, effort_days, cost, breakdown[]}, where
    breakdown is one {role, days, rate, cost} per FOR001 role. `rates` is an
    optional {role: £/day} map (from Settings) — each role defaults to £500 when
    absent, so calling with no rates reproduces the original flat-rate model.
    `day_rate` echoes the FOR001 default for reference; the real cost sums each
    role's own rate. An unrecognised/blank complexity yields zeros, never an error.
    """
    rates = resolve_day_rates(rates) if rates is not None else DEFAULT_DAY_RATES
    if complexity not in COMPLEXITY_LEVELS:
        return {"complexity": complexity, "day_rate": DAY_RATE,
                "effort_days": 0, "cost": 0, "breakdown": []}
    breakdown, total_days, total_cost = [], 0.0, 0.0
    for role, by_complexity in BID_EFFORT_DAYS.items():
        days = by_complexity[complexity]
        rate = rates[role]
        cost = days * rate
        total_days += days
        total_cost += cost
        breakdown.append({"role": role, "days": days, "rate": rate, "cost": cost})
    return {"complexity": complexity, "day_rate": DAY_RATE,
            "effort_days": total_days, "cost": total_cost, "breakdown": breakdown}


def rag_summary(scores):
    """The Win-Qualification RAG criteria → (rating, label).

    `scores` is {criterion_key: 1|2|3} (unscored criteria simply omitted). Rating
    is the rounded average across scored criteria — mirroring the observed FOR001
    sample (mean 2.8 → 3). Label is risk-facing, per FWF's usage: a high score is
    low risk (3→"Low", 2→"Med", 1→"High"). No scores → (None, None).
    """
    vals = [v for k, v in (scores or {}).items()
            if k in RAG_CRITERIA_KEYS and isinstance(v, (int, float)) and 1 <= v <= 3]
    if not vals:
        return None, None
    rating = round(sum(vals) / len(vals))
    return rating, {3: "Low", 2: "Med", 1: "High"}[rating]


def reference(rates=None):
    """The full FOR001 vocabulary for the UI to render the Triage form/labels.
    `rates` (optional {role: £/day} from Settings) feeds the economics curve so the
    Triage estimate reflects the team's configured day rates, not just the default."""
    return {
        "complexity_levels": COMPLEXITY_LEVELS,
        "day_rate": DAY_RATE,
        "bid_effort_days": BID_EFFORT_DAYS,
        "pricing_models": PRICING_MODELS,
        "decisions": DECISIONS,
        "delivery_roles": DELIVERY_ROLES,
        "rag_criteria": RAG_CRITERIA,
        # Precomputed economics per complexity so the UI can show the whole curve
        # (and update the headline stat instantly) without a round-trip per pick.
        "economics_by_complexity": {c: compute_bid_economics(c, rates) for c in COMPLEXITY_LEVELS},
    }


if __name__ == "__main__":
    # Sanity check against the FOR001 Reference sheet's published column totals.
    print("FOR001 bid economics (complexity → effort/cost):")
    for c in COMPLEXITY_LEVELS:
        e = compute_bid_economics(c)
        print(f"  {c:<9} {e['effort_days']:>5} days  £{e['cost']:,.0f}")
