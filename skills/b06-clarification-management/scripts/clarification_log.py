#!/usr/bin/env python3
"""B06 — Clarification register (v2).

Adds the fields a real bid needs: deadline date+time+timezone, portal link,
received-via, owner + backup, evidence required, internal due date, escalation
date, expanded status, sent-by, buyer confirmation. Flags due-soon, overdue,
and ESCALATE (past escalation date and still open).

Commands:
    add    --register r.json --ref C1 --received 2026-07-08 \
           --deadline 2026-07-15T17:00:00+01:00 --owner Eric --backup Roxana \
           --internal-due 2026-07-12 --escalation 2026-07-13 \
           --portal https://... --via portal --summary "parent co data" \
           --evidence "Arobs 2024 report"
    status --register r.json --ref C1 --set drafting
    close  --register r.json --ref C1 --sent 2026-07-12T09:00:00+01:00 \
           --sent-by Eric --buyer-confirmed yes
    list   --register r.json
"""
import argparse
import json
import os
from datetime import date, datetime

# Standalone skill vocabulary — deliberately NOT the app's canonical clarification
# model. The authoritative status set lives in src/clarification.py
# (CLARIFICATION_STATUSES = Open/Drafting/Submitted/Answered), which wins per
# CLAUDE.md's source-of-truth order. This helper targets the (not-yet-stood-up)
# SharePoint bid store and keeps its own lifecycle; if the skill chain is ever
# folded into the app, conform this to src/clarification.py rather than the reverse.
STATUSES = ["open", "drafting", "with_reviewer", "sent", "closed"]


def _load(p):
    if not os.path.exists(p):
        return {"items": []}
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _save(p, d):
    # Write to a sibling temp file then os.replace for an atomic swap — a crash
    # mid-write must never truncate the live register (this tool exists to stop
    # exactly that kind of admin data loss).
    tmp = f"{p}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)
    os.replace(tmp, p)


def _d(s):
    """Parse a date or datetime (with/without tz) to a date."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        return datetime.strptime(s, "%Y-%m-%d").date()


def add(a):
    d = _load(a.register)
    if any(i["ref"] == a.ref for i in d["items"]):
        raise SystemExit(f"{a.ref} exists.")
    d["items"].append({
        "ref": a.ref, "received": a.received, "deadline": a.deadline,
        "portal": a.portal, "received_via": a.via, "owner": a.owner,
        "backup_owner": a.backup, "evidence_required": a.evidence,
        "internal_due": a.internal_due, "escalation_date": a.escalation,
        "summary": a.summary, "status": "open", "sent": None,
        "sent_by": None, "buyer_confirmed": None,
    })
    _save(a.register, d)
    print(f"Logged {a.ref} (deadline {a.deadline}, owner {a.owner}, "
          f"backup {a.backup}).")


def set_status(a):
    d = _load(a.register)
    if a.set not in STATUSES:
        raise SystemExit(f"status must be one of {STATUSES}")
    for i in d["items"]:
        if i["ref"] == a.ref:
            i["status"] = a.set
            _save(a.register, d)
            print(f"{a.ref} -> {a.set}")
            return
    raise SystemExit(f"{a.ref} not found.")


def close(a):
    d = _load(a.register)
    for i in d["items"]:
        if i["ref"] == a.ref:
            i.update(status="closed", sent=a.sent, sent_by=a.sent_by,
                     buyer_confirmed=a.buyer_confirmed)
            _save(a.register, d)
            print(f"Closed {a.ref} (sent {a.sent} by {a.sent_by}, "
                  f"buyer confirmed: {a.buyer_confirmed}).")
            return
    raise SystemExit(f"{a.ref} not found.")


def _wd(a, b):
    if not a or not b:
        return None
    from datetime import timedelta
    step = 1 if b >= a else -1
    days, cur = 0, a
    while cur != b:
        cur += timedelta(days=step)
        if cur.weekday() < 5:
            days += step
    return days


def listcmd(a):
    d = _load(a.register)
    today = date.today()
    openi = [i for i in d["items"] if i["status"] != "closed"]
    if not openi:
        print("No open clarifications.")
    for i in sorted(openi, key=lambda x: x.get("deadline") or "9999"):
        dl = _d(i.get("deadline"))
        esc = _d(i.get("escalation_date"))
        wd = _wd(today, dl) if dl else None
        if dl is None:
            flag = "DEADLINE UNKNOWN — chase buyer **"
        elif wd is not None and wd < 0:
            flag = f"OVERDUE by {-wd} working day(s) **"
        elif wd is not None and wd <= 2:
            flag = f"DUE SOON — {wd} working day(s) **"
        else:
            flag = f"{wd} working days left"
        escalate = esc is not None and today >= esc
        print(f"[{i['ref']}] {i.get('summary','')}  ({i['status']})")
        print(f"    owner {i.get('owner')} / backup {i.get('backup_owner')}  "
              f"deadline {i.get('deadline')}  -> {flag}"
              + ("   ***ESCALATE TO MD***" if escalate else ""))
        if i.get("evidence_required"):
            print(f"    evidence required: {i['evidence_required']}")
    closed = [i for i in d["items"] if i["status"] == "closed"]
    if closed:
        print(f"\n({len(closed)} closed)")


def main():
    ap = argparse.ArgumentParser(description="B06 clarification register v2")
    s = ap.add_subparsers(dest="cmd", required=True)

    a = s.add_parser("add")
    for opt in ["register", "ref", "received", "deadline", "owner"]:
        a.add_argument(f"--{opt}", required=True)
    a.add_argument("--backup", default="")
    a.add_argument("--internal-due", dest="internal_due", default="")
    a.add_argument("--escalation", default="")
    a.add_argument("--portal", default="")
    a.add_argument("--via", default="portal")
    a.add_argument("--evidence", default="")
    a.add_argument("--summary", default="")
    a.set_defaults(func=add)

    st = s.add_parser("status")
    st.add_argument("--register", required=True)
    st.add_argument("--ref", required=True)
    st.add_argument("--set", required=True)
    st.set_defaults(func=set_status)

    c = s.add_parser("close")
    c.add_argument("--register", required=True)
    c.add_argument("--ref", required=True)
    c.add_argument("--sent", required=True)
    c.add_argument("--sent-by", dest="sent_by", required=True)
    c.add_argument("--buyer-confirmed", dest="buyer_confirmed", default="no")
    c.set_defaults(func=close)

    l = s.add_parser("list")
    l.add_argument("--register", required=True)
    l.set_defaults(func=listcmd)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
