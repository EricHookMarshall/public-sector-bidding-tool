#!/usr/bin/env python3
"""B01 — Bid Qualification scoring engine (v2).

Two layers plus bid economics:
  Layer 1: hard gates  PASS | FAIL | CONDITIONAL | UNKNOWN
     FAIL                         -> NO-BID (knockout)
     UNKNOWN on ELIGIBILITY gate  -> BLOCK  (cannot recommend on a guess)
     UNKNOWN on other gate        -> REVIEW (insufficient information)
     (missing gate == UNKNOWN — nothing passes silently)
  Layer 2: weighted 1-5 score across seven dimensions
  Economics: bid effort vs contract value vs win probability

Usage:
    python score.py --json '{"gates":{...},"scores":{...},"economics":{...}}'
"""
import argparse
import json
import sys

# Gates that affect ELIGIBILITY — UNKNOWN here BLOCKS.
GATES = {
    "G1": ("Route to market", True),
    "G2": ("Financial standing (EFS/FVRA)", True),
    "G3": ("Capability fit", False),
    "G4": ("Deliverability (Arobs resource)", False),
    "G5": ("Bid capacity & deadline", False),
    "G6": ("Eligibility & mandatory requirements", True),
    "G7": ("Evidence availability", False),
    "G8": ("Contract risk", False),
}

WEIGHTS = {
    "win_probability": 0.22,
    "strategic_fit": 0.15,
    "commercial_value": 0.15,
    "pricing_competitiveness": 0.14,
    "buyer_fit": 0.12,
    "deliverability_risk": 0.12,
    "effort_ratio": 0.10,
}

VALID_GATE = {"PASS", "FAIL", "CONDITIONAL", "UNKNOWN"}


def _band(score, conditional):
    if score >= 3.7:
        return "CONDITIONAL BID" if conditional else "BID"
    if score >= 3.0:
        return "REVIEW"
    return "NO-BID"


def economics(e):
    """Return a bid-economics summary. Non-blocking, advisory."""
    if not e:
        return None
    days = e.get("effort_days")
    rate = e.get("day_rate")
    value = e.get("contract_value")
    win = e.get("win_probability_pct")
    out = {}
    if days is not None and rate is not None:
        out["bid_cost"] = round(days * rate, 2)
    if value is not None and win is not None:
        out["expected_value"] = round(value * win / 100.0, 2)
    if "bid_cost" in out and "expected_value" in out and out["expected_value"]:
        out["cost_to_expected_value_pct"] = round(
            100 * out["bid_cost"] / out["expected_value"], 1)
        out["flag"] = ("HIGH — bid cost is large vs expected value; question the bid"
                       if out["cost_to_expected_value_pct"] > 15 else "acceptable")
    return out


def qualify(gates, scores, econ=None, weights=None):
    weights = weights or WEIGHTS
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("Weights must sum to 1.0 (100%).")

    # Normalise gates: any missing gate is UNKNOWN (never a silent pass)
    resolved = {}
    for g in GATES:
        v = (gates.get(g) or "UNKNOWN").upper()
        if v not in VALID_GATE:
            raise ValueError(f"Gate {g} has invalid value '{v}'.")
        resolved[g] = v

    failed = [g for g, v in resolved.items() if v == "FAIL"]
    if failed:
        return {"recommendation": "NO-BID",
                "reason": "Hard gate failure: " + ", ".join(
                    f"{g} {GATES[g][0]}" for g in failed),
                "gate_state": resolved, "scored": False,
                "economics": economics(econ)}

    unknown_eligibility = [g for g, v in resolved.items()
                           if v == "UNKNOWN" and GATES[g][1]]
    if unknown_eligibility:
        return {"recommendation": "BLOCK",
                "reason": "Eligibility gate(s) UNKNOWN — resolve before any "
                          "recommendation: " + ", ".join(
                              f"{g} {GATES[g][0]}" for g in unknown_eligibility),
                "gate_state": resolved, "scored": False,
                "economics": economics(econ)}

    unknown_other = [g for g, v in resolved.items()
                     if v == "UNKNOWN" and not GATES[g][1]]
    conditional = [g for g, v in resolved.items() if v == "CONDITIONAL"]

    # Score
    for d in weights:
        v = scores.get(d)
        if v is None or not (1 <= v <= 5):
            raise ValueError(f"Score for '{d}' must be 1-5 (got {v!r}).")
    contributions = {d: round(scores[d] * w, 3) for d, w in weights.items()}
    total = round(sum(contributions.values()), 2)

    if unknown_other:
        rec = "REVIEW — insufficient information"
    else:
        rec = _band(total, bool(conditional))

    return {"recommendation": rec, "weighted_score": total,
            "contributions": contributions,
            "gates_conditional": conditional,
            "gates_unknown_nonblocking": unknown_other,
            "gate_state": resolved, "scored": True,
            "economics": economics(econ)}


def main():
    ap = argparse.ArgumentParser(description="B01 qualification scorer v2")
    ap.add_argument("--json", help="{'gates':{}, 'scores':{}, 'economics':{}}")
    args = ap.parse_args()
    if not args.json:
        ap.print_help(); sys.exit(0)
    p = json.loads(args.json)
    print(json.dumps(qualify(p.get("gates", {}), p.get("scores", {}),
                             p.get("economics"), p.get("weights")), indent=2))


if __name__ == "__main__":
    main()
