#!/usr/bin/env python3
"""G2 companion — FWF's OWN position on each framework / DPS, from the real bid library.

The radar (`frameworks_radar.py`) answers "which agreements SHOULD FWF be on?" from
curated GCA facts. It cannot see what FWF is *actually doing*: its `fwf_status` is a
hand-written claim carrying the caveat "internal fact — confirm on the Digital
Marketplace". This module supplies the missing half — the evidence — by reading FWF's
own framework folders in the exported bid store.

It matters because the two disagree. The radar has G-Cloud 15 as `not_member` and
recommends "prepare". The library shows **108 files and a drafted response**: FWF is
already well into it. It also shows four agreements the radar has never heard of
(Bluelight, DDaT-NSW, KCC, plus three DPSs) and two empty scaffolds (MOD AI & Edge,
RM6396) that look like intent, not work. A prioritiser that can't see any of that will
keep telling you to start things you've half-finished.

WHAT THIS DOES NOT CLAIM. A folder proves *work*, never *membership*. Nothing here
concludes FWF is ON a framework — that is not derivable from a directory listing, and
inventing it is exactly the false-record failure this project exists to prevent (cf.
`D365 Awards.xlsx`, a file of other companies' awards that reads like a record of ours).
So the ladder tops out at `response_drafted`, and membership stays the radar's caveated
claim until someone confirms it on the Digital Marketplace.

Provider seam, same as `library.py`: LocalMirror now (the gitignored export),
GraphSharePoint later behind the same interface. Absent export -> `available: False`,
never fabricated data.
"""
import os
import re
from datetime import date

# The export lives outside src/ (gitignored, client-confidential). Resolved relative to
# this file so it travels with the code, same convention as bids.db / .env.
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(_REPO, "knowledge", "SharePoint Folder", "Bids",
                    "04 Portal Registrations")

# A response lives here once it's being written. Presence of a file in one of these is
# the strongest signal the export can honestly give.
RESPONSE_DIRS = ("02 Submission Master", "06 Bid Files", "Bid Pack")

# CCS agreements carry an RM code; it's how we tie a folder to a radar agreement.
# 'AI DPS RM62000' is a typo for RM6200 in the real folder name — normalise, don't
# "fix" the source (we don't own it).
_RM_RE = re.compile(r"RM\s?(\d{4,5}(?:\.\d{1,2})?)", re.IGNORECASE)
_RM_TYPOS = {"62000": "6200"}


def rm_code(name):
    """The RM code in a folder name, or None. 'G Cloud 15' has none in the name but IS
    RM1557.15 — the caller maps those by hand rather than guessing here."""
    m = _RM_RE.search(name or "")
    if not m:
        return None
    code = m.group(1)
    return "RM" + _RM_TYPOS.get(code, code)


# Folder-name -> radar agreement id, for the ones whose RM code isn't in the name.
KNOWN_IDS = {"G Cloud 15": "RM1557.15"}


def _scan(path):
    """(file_count, first_touched, last_touched) under a folder, ignoring OS cruft."""
    times, count = [], 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            if f == ".DS_Store":
                continue
            count += 1
            try:
                times.append(os.path.getmtime(os.path.join(root, f)))
            except OSError:
                pass
    if not times:
        return 0, None, None
    return (count,
            date.fromtimestamp(min(times)).isoformat(),
            date.fromtimestamp(max(times)).isoformat())


def _response_files(path):
    """Files sitting in a response/submission folder — the evidence of actual drafting."""
    out = []
    for sub in RESPONSE_DIRS:
        p = os.path.join(path, sub)
        if not os.path.isdir(p):
            continue
        for root, _dirs, files in os.walk(p):
            for f in files:
                if f != ".DS_Store":
                    out.append(f)
    return out


def _status(file_count, responses):
    """The evidence ladder. It deliberately STOPS SHORT of 'submitted' and 'member':
    neither is knowable from a folder, and a confident wrong answer is worse than none.

      planned          the folder exists and is empty — intent, not work
      preparing        framework docs gathered, nothing drafted yet
      response_drafted a response/submission file exists
    """
    if file_count == 0:
        return "planned"
    if responses:
        return "response_drafted"
    return "preparing"


def positions(root=ROOT):
    """FWF's position on every framework/DPS folder in the export.

    Returns {available, root_present, positions[], as_at}. When the export isn't there
    (CI, a fresh clone) this reports available=False rather than inventing anything.
    """
    if not os.path.isdir(root):
        return {"available": False, "reason": "bid-library export not present locally",
                "positions": [], "as_at": date.today().isoformat()}

    out = []
    for kind, folder in (("Framework", "Frameworks"), ("DPS", "DPS")):
        base = os.path.join(root, folder)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if not os.path.isdir(path):
                continue
            count, first, last = _scan(path)
            responses = _response_files(path)
            out.append({
                "name": name,
                "kind": kind,
                "agreement_id": KNOWN_IDS.get(name) or rm_code(name),
                "status": _status(count, responses),
                "file_count": count,
                "response_files": len(responses),
                "first_activity": first,
                "last_activity": last,
                # Provenance, always: this is derived from a directory, not a portal.
                "evidence": "bid-library export (folder contents)",
            })
    out.sort(key=lambda p: (p["status"] != "response_drafted", -p["file_count"]))
    return {"available": True, "positions": out, "as_at": date.today().isoformat(),
            "caveat": ("Derived from FWF's bid-library folders: a folder proves WORK, "
                       "not MEMBERSHIP. 'response_drafted' means a response file exists, "
                       "not that it was submitted or won. Confirm membership on the "
                       "Digital Marketplace / the agreement's GCA page.")}


def annotate(agreements, root=ROOT):
    """Attach FWF's real position to the radar's curated agreements, and flag DISAGREEMENT.

    The point of the pairing: the radar says "prepare for G-Cloud 15" while the library
    shows a drafted G-Cloud 15 response. Surfacing that as `contradicts_radar` is the
    whole value — a prioritiser that tells you to start what you've half-finished is
    worse than useless.
    """
    pos = positions(root)
    by_id = {p["agreement_id"]: p for p in pos["positions"] if p["agreement_id"]}
    unmatched = [p for p in pos["positions"] if p["agreement_id"] not in
                 {a.get("id") for a in agreements}]

    for ag in agreements:
        p = by_id.get(ag.get("id"))
        ag["our_position"] = p
        # We're working on it, but the curated fact says we're not on it and the radar is
        # still telling us to get ready. That's a contradiction worth a human's eye.
        ag["contradicts_radar"] = bool(
            p and p["status"] == "response_drafted" and ag.get("fwf_status") == "not_member"
        )
    return {"available": pos["available"], "agreements": agreements,
            "not_on_radar": unmatched, "caveat": pos.get("caveat"),
            "as_at": pos["as_at"]}


def main():
    res = positions()
    if not res["available"]:
        print(f"unavailable: {res['reason']}")
        return
    print(f"FWF framework / DPS positions (as at {res['as_at']})\n")
    for p in res["positions"]:
        aid = p["agreement_id"] or "—"
        span = f"{p['first_activity']} -> {p['last_activity']}" if p["first_activity"] else "no activity"
        print(f"  [{p['status']:16}] {p['kind']:9} {aid:10} {p['name'][:44]:44}")
        print(f"      {p['file_count']:3} files ({p['response_files']} response)   {span}")
    print(f"\n{res['caveat']}")


if __name__ == "__main__":
    main()
