#!/usr/bin/env python3
"""B03 — Reuse ranking engine.

Applies the explicit reuse-score formula to candidate records retrieved from
the SharePoint Approved Answer Bank / Evidence Register, and applies the
do-not-reuse exclusions before ranking.

    Reuse score =
       35% relevance to question
     + 20% same buyer/sector/framework
     + 15% outcome quality (won > shortlisted > unknown > lost)
     + 15% freshness
     + 10% evidence availability
     +  5% approved reuse status

All feature inputs are 0-1 (Claude supplies them; relevance/semantic similarity
in particular is judged or supplied by the retrieval layer). Excluded candidates
are dropped with a reason, never silently ranked low.

Usage:
    python rank.py --in candidates.json
"""
import argparse
import json

WEIGHTS = {
    "relevance": 0.35,
    "context_match": 0.20,     # same buyer/sector/framework
    "outcome_quality": 0.15,
    "freshness": 0.15,
    "evidence_availability": 0.10,
    "approved_status": 0.05,
}

OUTCOME_QUALITY = {"won": 1.0, "shortlisted": 0.6, "unknown": 0.3, "lost": 0.1,
                   "non_compliant": 0.0, "withdrawn": 0.2}


def excluded(c):
    """Return an exclusion reason, or None if the candidate is usable."""
    if c.get("reuse_status") == "do_not_reuse":
        return "flagged do_not_reuse"
    if c.get("lost_bid_criticised"):
        return "lost-bid content criticised in feedback"
    if c.get("superseded_framework"):
        return "superseded framework language"
    if c.get("names_former_staff"):
        return "names former employee"
    if c.get("expired_claim"):
        return "expired insurance/certification claim"
    if c.get("confidentiality") in ("client_confidential", "commercially_sensitive") \
            and not c.get("cleared_for_reuse"):
        return "client-confidential / commercially sensitive, not cleared"
    if c.get("stale_regime"):
        return "PCR2015/MEAT or CCS wording where PA23/MAT/GCA now applies"
    return None


def score_candidate(c):
    oq = OUTCOME_QUALITY.get((c.get("outcome") or "unknown").lower(), 0.3)
    feats = {
        "relevance": float(c.get("relevance", 0)),
        "context_match": float(c.get("context_match", 0)),
        "outcome_quality": oq,
        "freshness": float(c.get("freshness", 0)),
        "evidence_availability": float(c.get("evidence_availability", 0)),
        "approved_status": 1.0 if c.get("reuse_status") == "approved" else 0.0,
    }
    total = round(sum(feats[k] * w for k, w in WEIGHTS.items()), 4)
    return total, feats


def rank(candidates):
    kept, dropped = [], []
    for c in candidates:
        reason = excluded(c)
        if reason:
            dropped.append({"id": c.get("id"), "reason": reason})
            continue
        total, feats = score_candidate(c)
        kept.append({"id": c.get("id"), "reuse_score": total,
                     "features": feats, "reuse_status": c.get("reuse_status"),
                     "source_link": c.get("source_link")})
    kept.sort(key=lambda x: x["reuse_score"], reverse=True)
    return kept, dropped


def main():
    ap = argparse.ArgumentParser(description="B03 reuse ranking")
    ap.add_argument("--in", dest="infile", required=True)
    args = ap.parse_args()
    candidates = json.load(open(args.infile))
    kept, dropped = rank(candidates)
    print(json.dumps({"ranked": kept, "excluded": dropped}, indent=2))
    print(f"\n{len(kept)} usable, {len(dropped)} excluded")


if __name__ == "__main__":
    main()
