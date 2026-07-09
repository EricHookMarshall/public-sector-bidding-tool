#!/usr/bin/env python3
"""B07 — Outcome debrief & library update engine.

Takes a bid outcome plus per-answer results and produces:
  - a debrief record
  - a set of library actions: promote / retire / refresh answers & evidence

This closes the loop: won answers get promoted toward 'approved'; criticised or
losing answers get flagged do_not_reuse; time-bound evidence gets an expiry
refresh action. Actions are RECOMMENDATIONS applied by a human in SharePoint.

Usage:
    python debrief.py --in outcome.json

outcome.json:
{
  "bid_id": "FWF-2026-001",
  "buyer": "Example Council",
  "outcome": "won",                 # won|lost|shortlisted|non_compliant|withdrawn
  "overall_score": "82%",
  "feedback": "strong technical, weak social value",
  "answers": [
    {"ref": "3.2.1", "record_id": "ANS-101", "answer_score": "high",
     "feedback": "clear", "timebound": false},
    {"ref": "3.4.2", "record_id": "ANS-140", "answer_score": "low",
     "feedback": "generic, no evidence", "timebound": false},
    {"ref": "4.1.1", "record_id": "ANS-160", "answer_score": "high",
     "timebound": true, "evidence_expiry": "2026-09-01"}
  ]
}
"""
import argparse
import json


def library_actions(outcome, answers):
    actions = []
    for a in answers:
        rid = a.get("record_id") or a.get("ref")
        score = (a.get("answer_score") or "").lower()
        fb = (a.get("feedback") or "").lower()

        criticised = any(w in fb for w in
                         ["generic", "weak", "no evidence", "unclear", "poor"])

        if outcome == "won" and score == "high" and not criticised:
            actions.append({"record": rid, "action": "promote",
                            "to": "approved",
                            "why": "won bid, high-scoring, not criticised"})
        elif criticised or score == "low" or outcome in ("lost", "non_compliant"):
            actions.append({"record": rid, "action": "flag_do_not_reuse",
                            "why": f"score={score or 'n/a'}; feedback criticised"
                                   if criticised else
                                   f"score={score or 'n/a'}; outcome={outcome}"})
        else:
            actions.append({"record": rid, "action": "review",
                            "why": "no strong signal — human review"})

        if a.get("timebound") and a.get("evidence_expiry"):
            actions.append({"record": rid, "action": "refresh_before",
                            "date": a["evidence_expiry"],
                            "why": "time-bound evidence expiry"})
    return actions


def main():
    ap = argparse.ArgumentParser(description="B07 debrief & library update")
    ap.add_argument("--in", dest="infile", required=True)
    args = ap.parse_args()
    o = json.load(open(args.infile))
    actions = library_actions(o.get("outcome", "unknown"), o.get("answers", []))

    debrief = {
        "bid_id": o.get("bid_id"),
        "buyer": o.get("buyer"),
        "outcome": o.get("outcome"),
        "overall_score": o.get("overall_score"),
        "feedback": o.get("feedback"),
        "library_actions": actions,
        "summary": {
            "promote": sum(1 for x in actions if x["action"] == "promote"),
            "flag_do_not_reuse": sum(1 for x in actions
                                     if x["action"] == "flag_do_not_reuse"),
            "review": sum(1 for x in actions if x["action"] == "review"),
            "refresh_before": sum(1 for x in actions
                                  if x["action"] == "refresh_before"),
        },
    }
    print(json.dumps(debrief, indent=2))


if __name__ == "__main__":
    main()
