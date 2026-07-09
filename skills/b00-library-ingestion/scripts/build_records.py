#!/usr/bin/env python3
"""B00 — Bid library record builder & validator.

Takes structured records (Claude extracts them from source bids) and validates
them for load into the three SharePoint libraries. Records failing validation
are quarantined (reported, not emitted). Nothing is auto-approved.

Usage:
    python build_records.py --in records.json --outdir ./out

records.json = list of answer records (see references/record_schema.md).
Emits: out/answer_bank.json, out/evidence_register.json, out/quarantine.json,
       out/coverage.json
"""
import argparse
import json
import os

REQUIRED = ["buyer", "question_text", "answer_text", "source_link"]
OUTCOMES = {"won", "lost", "shortlisted", "non_compliant", "withdrawn", "unknown"}
REUSE = {"approved", "needs_update", "do_not_reuse"}
CONF = {"public", "internal", "client_confidential", "commercially_sensitive"}


def validate(rec):
    problems = []
    for f in REQUIRED:
        if not rec.get(f):
            problems.append(f"missing {f}")
    if rec.get("outcome") and rec["outcome"] not in OUTCOMES:
        problems.append(f"bad outcome '{rec['outcome']}'")
    # reuse_status defaults to needs_update; never auto-approve
    rs = rec.get("reuse_status", "needs_update")
    if rs not in REUSE:
        problems.append(f"bad reuse_status '{rs}'")
    if rs == "approved" and not rec.get("approved_by"):
        problems.append("reuse_status=approved but no approved_by (not allowed)")
    conf = rec.get("confidentiality")
    if conf and conf not in CONF:
        problems.append(f"bad confidentiality '{conf}'")
    return problems


def main():
    ap = argparse.ArgumentParser(description="B00 record builder")
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    records = json.load(open(args.infile))

    answers, evidence, quarantine = [], [], []
    for rec in records:
        problems = validate(rec)
        if problems:
            quarantine.append({"record": rec, "problems": problems})
            continue
        rec.setdefault("reuse_status", "needs_update")
        rec.setdefault("confidentiality", "internal")
        answers.append(rec)
        for ev in rec.get("evidence_used", []) or []:
            evidence.append({
                "evidence_type": ev.get("type", "unknown"),
                "owner": ev.get("owner", ""),
                "expiry_date": ev.get("expiry_date"),
                "approved_external": ev.get("approved_external", False),
                "related_claim": ev.get("claim", ""),
                "source_link": ev.get("source_link", rec.get("source_link")),
                "from_bid": rec.get("buyer"),
            })

    coverage = {
        "records_in": len(records),
        "answers_written": len(answers),
        "evidence_written": len(evidence),
        "quarantined": len(quarantine),
        "missing_owner": sum(1 for a in answers if not a.get("content_owner")),
        "missing_outcome": sum(1 for a in answers if not a.get("outcome")
                               or a.get("outcome") == "unknown"),
        "needs_update": sum(1 for a in answers
                            if a.get("reuse_status") == "needs_update"),
        "missing_expiry_timebound": sum(
            1 for a in answers if a.get("timebound") and not a.get("expiry_date")),
    }

    for name, data in [("answer_bank", answers), ("evidence_register", evidence),
                       ("quarantine", quarantine), ("coverage", coverage)]:
        with open(os.path.join(args.outdir, f"{name}.json"), "w") as f:
            json.dump(data, f, indent=2)

    print(json.dumps(coverage, indent=2))
    if quarantine:
        print(f"\n{len(quarantine)} record(s) quarantined — see quarantine.json")


if __name__ == "__main__":
    main()
