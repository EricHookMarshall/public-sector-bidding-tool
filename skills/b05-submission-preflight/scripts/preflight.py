#!/usr/bin/env python3
"""B05 — Submission pre-flight & EFS/FVRA gate (v2).

Two-stage: run at 'readiness' (T-5 / midpoint) and 'final' (T-1 / <=4h before).

Fixes the v1 silent-pass holes. These are now BLOCKING:
  - no matrix supplied / no mandatory rows found
  - no answer list supplied where answers are required
  - any document marked UNKNOWN
  - any required document missing an expiry_date where one is expected
  - submission deadline missing date, time, OR timezone
  - EFS gate not cleared
  - no clarification owner / mailbox not confirmed monitored

Documents are conditional, not hard-coded: each has required / present /
expiry_date / acceptable_for_this_bid / source_link.

Usage:
    python preflight.py --config bid.json --stage readiness|final
"""
import argparse
import json
import re
import sys


def deadline_ok(d):
    """Require an ISO datetime with an explicit timezone offset."""
    if not d:
        return False, "deadline missing"
    if not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", d):
        return False, "deadline missing date or time"
    if not re.search(r"(Z|[+-]\d{2}:?\d{2})$", d):
        return False, "deadline missing timezone"
    return True, ""


def efs_cleared(efs):
    if efs is None:
        return False, "EFS position not supplied (UNKNOWN blocks)"
    if not efs.get("route_has_financial_stage", True):
        return True, "no separate financial-standing stage"
    if efs.get("standalone_clears"):
        return True, "standalone accounts clear threshold"
    if efs.get("pcg_in_place") and efs.get("pcg_acceptable_this_stage"):
        return True, "Arobs PCG in place and acceptable at this stage"
    return False, ("EFS gate NOT cleared (PCG absent/unconfirmed; the G-Cloud 15 "
                   "failure mode)")


def run(cfg, stage):
    b = []  # blocking items

    # Matrix / mandatory rows
    rows = cfg.get("mandatory_rows")
    if not rows:
        b.append("No matrix / no mandatory rows supplied (cannot confirm completeness)")
    else:
        for r in rows:
            rags = r.get("rags", {})
            if not rags:
                b.append(f"Row {r.get('ref')}: no RAG statuses supplied")
            else:
                not_green = [k for k, v in rags.items()
                             if str(v).capitalize() != "Green"]
                if not_green:
                    b.append(f"Row {r.get('ref')}: not Green on {', '.join(not_green)}")

    # Answers where required
    answers = cfg.get("answers")
    if cfg.get("answers_required", True) and not answers:
        b.append("Answers required but no answer list supplied")
    for a in answers or []:
        if a.get("within_limit") is False:
            b.append(f"Answer {a.get('ref')}: over limit")
        if a.get("placeholders", 0) > 0:
            b.append(f"Answer {a.get('ref')}: {a['placeholders']} unfilled placeholder(s)")
        if a.get("open_flags", 0) > 0:
            b.append(f"Answer {a.get('ref')}: {a['open_flags']} unresolved checker flag(s)")

    # Documents (conditional)
    for name, d in (cfg.get("documents") or {}).items():
        if not d.get("required", False):
            continue
        if d.get("present") is None:
            b.append(f"Document '{name}': status UNKNOWN")
            continue
        if not d.get("present"):
            b.append(f"Document '{name}': required but not present")
        if d.get("expiry_expected", True) and not d.get("expiry_date"):
            b.append(f"Document '{name}': expiry_date missing")
        if d.get("acceptable_for_this_bid") is False:
            b.append(f"Document '{name}': not acceptable for this bid")

    # EFS gate
    ok, msg = efs_cleared(cfg.get("efs"))
    if not ok:
        b.append(f"EFS/FVRA: {msg}")

    # Deadline
    ok, msg = deadline_ok(cfg.get("deadline"))
    if not ok:
        b.append(f"Deadline: {msg}")

    # Clarification handling
    if not cfg.get("clarification_owner"):
        b.append("No clarification owner assigned")
    if not cfg.get("clarification_mailbox_monitored"):
        b.append("Clarification mailbox not confirmed monitored")

    verdict = "READY" if not b else "NOT READY"
    return verdict, b


def main():
    ap = argparse.ArgumentParser(description="B05 pre-flight v2")
    ap.add_argument("--config", required=True)
    ap.add_argument("--stage", choices=["readiness", "final"], default="final")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    verdict, blocking = run(cfg, args.stage)
    print(f"Bid: {cfg.get('bid','(unnamed)')}   Stage: {args.stage}")
    print(f"VERDICT: {verdict}\n")
    for item in blocking:
        print(f"  - {item}")
    sys.exit(0 if verdict == "READY" else 1)


if __name__ == "__main__":
    main()
