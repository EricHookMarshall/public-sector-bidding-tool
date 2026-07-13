#!/usr/bin/env python3
"""G1 follow-on — "which bids did we LOSE, and to whom?"

Award notices name only the WINNER, so a loss is never stated anywhere: it has to be
inferred. The inference is: take a bid FWF actually made, find that procurement's award
notice in the public feed, and read off the supplier. If it isn't us, we lost — and we
learn who beat us and for how much. `cf_bulk` supplies the feed (see that module for why
the OCDS *APIs* can't do this); this module does the matching.

THIS MODULE PROPOSES. IT DOES NOT ASSERT. Nothing here writes to bids.db.

That rule is not squeamishness, it is the lesson of two concrete near-misses:

  1. `D365 Awards.xlsx` in the bid library looks like a record of FWF's wins. It is not —
     every row is an award to a DIFFERENT company (Hitachi, EY, Softcat). An importer
     pointed at it would have written ten false records into our own awards table.
  2. Buyer-name matching alone returns every notice that buyer published in the window.
     Early runs called an unrelated PwC contract ("Home Office - Strategic Cost Review")
     a lost bid, purely because it shares the words "home" and "office" with the folder
     name, and called our WM5G AI bid lost to a rail-fares consultancy because both say
     "west midlands". Geography and buyer names are not evidence.

So every bid gets a RANKED CANDIDATE LIST with the evidence that earned the rank, and a
human confirms. Confidence, strongest first:

  ref     the buyer's own tender reference (PS25317, NCC1547) appears in the notice.
          Near-proof, and the only tier that has actually produced a clean result.
  title   buyer matches AND the notice title shares a DISTINCTIVE word with the bid —
          distinctive meaning after the buyer's own name and aliases are subtracted.
  buyer   buyer matches and nothing else does. A lead. Not a match.

Verdicts:
  WON             an award on a matched notice names FWF (CH number, or a name variant)
  LOST            a matched notice carries an award, and it went to someone else
  LIVE/NO AWARD   the tender notice matched, but no award is published yet
  NO MATCH        the buyer never appears in the window. NOT a loss — for a Scottish or
                  Welsh buyer it almost certainly means the notice lives on PCS or
                  Sell2Wales, which this feed does not carry.

Run:  python3 bid_outcomes.py [--json]
"""
import json
import os
import re
import sys
from collections import defaultdict

import cf_bulk

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "bid_manifest.json")

# FWF's Companies House number is CONFIG, never hardcoded (facts decay; it's org-specific).
# api.py resolves it from app_settings `own_org`, same as own_awards.py. This default is
# only for the CLI.
DEFAULT_CH = "11934102"

STOP = {"the", "of", "and", "for", "services", "service", "ltd", "limited", "plc",
        "council", "university", "authority", "department", "provision", "supply",
        "framework", "contract", "tender", "uk", "national", "group", "cc", "city"}

RANK = {"ref": 0, "title": 1, "buyer": 2}


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).strip()


def toks(s):
    return {t for t in norm(s).split() if t and t not in STOP and len(t) > 2}


def key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def is_us(name, ident, ch_number):
    """Is this supplier FWF? CH number is the unambiguous signal; the name is a backup
    (publishers write both 'Future Work Force' and 'Future Workforce')."""
    if key(ident) and key(ch_number) in key(ident):
        return True
    return bool(re.search(r"future\s*work\s*force|future\s*workforce", name or "", re.I))


def distinctive(bid):
    """The words that identify the bid's SUBJECT, with the buyer's identity removed.

    Subtracting the buyer name AND every alias is the whole point. Leave them in and:
      '25 Home Office PPPT'  keeps {home, office} -> matches any Home Office notice
      '20 West Midlands WM5G' keeps {west, midlands} -> matches WMCA's rail contracts
    Both produced confident, wrong LOST verdicts. If nothing distinctive survives (WM5G
    reduces to the empty set), the bid simply HAS no title signal and falls back to a
    buyer lead — which is the honest answer.
    """
    out = toks(bid["folder"]) - toks(bid["buyer"])
    for alias in bid["aliases"]:
        out -= toks(alias)
    return out


def score(bid, rel):
    """(confidence, reasons) that this notice is the bid's procurement, or (None, _)."""
    hay = key(f"{rel.get('title')} {rel.get('description')} {rel.get('tender_id')}")
    buyer_n = norm(rel.get("buyer"))
    reasons = []

    ref_hit = any(key(r) and key(r) in hay for r in bid.get("refs") or [])
    buyer_hit = any(a in buyer_n for a in bid["aliases"] if a)
    overlap = distinctive(bid) & toks(rel.get("title"))

    if ref_hit:
        reasons.append("tender-ref match")
    if buyer_hit:
        reasons.append("buyer match")
    if overlap:
        reasons.append("title: " + "/".join(sorted(overlap)))

    if ref_hit:
        return "ref", reasons
    if buyer_hit and overlap:
        return "title", reasons
    if buyer_hit:
        return "buyer", reasons
    return None, reasons


def _award_view(rel, award, ch_number):
    """(supplier_names, we_won) — resolving supplier party-ids against parties[], since
    an award often references a party rather than naming the supplier inline."""
    by_id = {p.get("id"): p for p in rel.get("parties") or []}
    names, we_won = [], False
    for sup in award.get("suppliers") or []:
        party = by_id.get(sup.get("id")) or {}
        name = sup.get("name") or party.get("name")
        if name:
            names.append(name)
        if is_us(name, party.get("ident"), ch_number):
            we_won = True
    return names, we_won


def match(bid, releases, ch_number):
    """Every candidate notice for one bid, best-evidence first, plus a verdict."""
    cands = []
    for rel in releases:
        conf, reasons = score(bid, rel)
        if not conf:
            continue
        awards = rel.get("awards") or []
        if not awards:
            cands.append({"conf": conf, "reasons": reasons, "kind": "tender",
                          "buyer": rel.get("buyer"), "title": rel.get("title"),
                          "winners": [], "we_won": False, "amount": None,
                          "currency": None, "date": rel.get("deadline"),
                          "ocid": rel.get("ocid")})
            continue
        for award in awards:
            names, we_won = _award_view(rel, award, ch_number)
            cands.append({"conf": conf, "reasons": reasons, "kind": "award",
                          "buyer": rel.get("buyer"), "title": rel.get("title"),
                          "winners": names, "we_won": we_won,
                          "amount": award.get("amount"), "currency": award.get("currency"),
                          "date": award.get("date"), "ocid": rel.get("ocid")})

    cands.sort(key=lambda c: (RANK[c["conf"]], c["kind"] != "award", not c["we_won"]))
    strong = [c for c in cands if c["conf"] in ("ref", "title")]

    if any(c["we_won"] for c in cands):
        verdict = "WON"
    elif any(c["kind"] == "award" for c in strong):
        verdict = "LOST"
    elif strong:
        verdict = "LIVE / NO AWARD YET"
    elif cands:
        verdict = "LEADS ONLY (buyer seen)"
    else:
        verdict = "NO MATCH"
    return verdict, cands


def run(ch_number=DEFAULT_CH):
    with open(MANIFEST) as fh:
        manifest = json.load(fh)
    releases = cf_bulk.load_cached()
    if not releases:
        raise SystemExit("No cached notices. Run: python3 cf_bulk.py 2025-05-01 2026-07-12")

    out = []
    for bid in manifest["bids"]:
        if bid.get("exclude"):
            # A framework application (G-Cloud) is not a tender — it has no award notice
            # naming FWF, so scoring it would only manufacture noise.
            out.append({"bid": bid, "verdict": "EXCLUDED (framework)", "candidates": []})
            continue
        verdict, cands = match(bid, releases, ch_number)
        out.append({"bid": bid, "verdict": verdict, "candidates": cands})
    return out, len(releases)


def main():
    results, n = run()
    if "--json" in sys.argv:
        print(json.dumps([{"folder": r["bid"]["folder"], "buyer": r["bid"]["buyer"],
                           "verdict": r["verdict"], "candidates": r["candidates"][:8]}
                          for r in results], indent=2))
        return

    print(f"{n:,} notices cached (Contracts Finder / CDP bulk)\n")
    for r in results:
        bid = r["bid"]
        print("=" * 78)
        print(f"{bid['folder']}  ->  {bid['buyer']}")
        print(f"  submitted(folder)={bid['submitted']}  expect={bid.get('expected_source')}"
              f"   VERDICT: {r['verdict']}   ({len(r['candidates'])} candidates)")
        for c in r["candidates"][:3]:
            try:
                amt = f"{float(c['amount']):,.0f}" if c.get("amount") else "?"
            except (TypeError, ValueError):
                amt = str(c.get("amount"))
            tag = "   <<< FWF" if c["we_won"] else ""
            print(f"    [{c['conf']:5}/{c['kind']:6}] {(c['title'] or '')[:52]}")
            print(f"            buyer:  {(c['buyer'] or '')[:46]}")
            print(f"            winner: {', '.join(c['winners']) or '-':46} {amt}"
                  f" {(c['date'] or '')[:10]}{tag}")
            print(f"            why:    {', '.join(c['reasons'])}")
        if len(r["candidates"]) > 3:
            print(f"    ... +{len(r['candidates'])-3} more")

    print("\n" + "=" * 78 + "\nSUMMARY")
    tally = defaultdict(int)
    for r in results:
        tally[r["verdict"]] += 1
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {k:24} {v}")
    print("\nProposals only — nothing written to bids.db. Confirm before recording.")


if __name__ == "__main__":
    main()
