"""G1 follow-on — offline tests for the lost-bid matcher.

These pin the two false positives that a live run actually produced, because both were
CONFIDENT and WRONG, which is the exact failure class this project exists to prevent:

  1. Buyer-name leak — folder '25 Home Office PPPT' shares {home, office} with the
     notice 'Home Office - Strategic Cost Review', so an unrelated PwC award scored as a
     title-grade match and the bid was reported LOST to PwC.
  2. Geography leak — folder '20 West Midlands WM5G' shares {west, midlands} with West
     Midlands Combined Authority's rail-fares award, so our AI bid was reported LOST to
     a transport consultancy. The bid library's own 'Not Won' record is what caught it.

A buyer-name or geography collision is a BUYER LEAD. Never a match.
"""
import os

os.environ.setdefault("LOCAL_AUTH_BYPASS", "1")

import bid_outcomes as BO  # noqa: E402

CH = "11934102"

HOME_OFFICE = {"folder": "25 Home Office PPPT", "buyer": "Home Office",
               "aliases": ["home office"], "submitted": False}
WM5G = {"folder": "20 West Midlands WM5G", "buyer": "WM5G Limited",
        "aliases": ["wm5g", "west midlands combined authority"], "submitted": False}
ACAS = {"folder": "22 UK BS (ACAS)", "buyer": "UK Shared Business Services (for Acas)",
        "aliases": ["uk shared business services", "uksbs", "acas"],
        "refs": ["PS25317"], "submitted": False}


def rel(buyer, title, suppliers=None, ident=None, tender_id=""):
    """A minimal cf_bulk-shaped notice."""
    awards = []
    if suppliers is not None:
        awards = [{"id": "a1", "date": "2026-02-13", "amount": "100000",
                   "currency": "GBP",
                   "suppliers": [{"name": s, "id": s} for s in suppliers]}]
    parties = [{"id": s, "name": s, "scheme": "GB-COH", "ident": ident}
               for s in (suppliers or [])]
    return {"ocid": "ocds-x", "buyer": buyer, "title": title, "description": "",
            "tender_id": tender_id, "awards": awards, "parties": parties}


def test_buyer_name_words_are_not_a_title_match():
    """'Home Office' in the title is the BUYER, not the bid's subject."""
    notice = rel("Home Office", "Home Office - Strategic Cost Review",
                 suppliers=["PRICEWATERHOUSECOOPERS LLP"])
    conf, _ = BO.score(HOME_OFFICE, notice)
    assert conf == "buyer", f"buyer-name collision must not exceed a buyer lead, got {conf}"


def test_geography_words_are_not_a_title_match():
    """'West Midlands' is where the buyer is, not what we bid for."""
    notice = rel("WEST MIDLANDS COMBINED AUTHORITY",
                 "West Midlands Rail Executive - Fares Reform Business Case",
                 suppliers=["WSP UK Limited"])
    conf, _ = BO.score(WM5G, notice)
    assert conf == "buyer", f"geography collision must not exceed a buyer lead, got {conf}"


def test_wm5g_has_no_distinctive_subject_words():
    """Once buyer + aliases are subtracted, WM5G has NO subject words left — so it can
    never earn a title match, and must degrade to a lead rather than invent one."""
    assert BO.distinctive(WM5G) == set()


def test_tender_ref_is_near_proof():
    """The buyer's own reference in the notice is the one signal we trust."""
    notice = rel("UK SBS", "PS25317 - Ai Discovery for Early Conciliation & Helpline",
                 suppliers=["Informed Solutions Ltd."])
    conf, reasons = BO.score(ACAS, notice)
    assert conf == "ref"
    assert "tender-ref match" in reasons


def test_lost_names_the_winner():
    notice = rel("UK SBS", "PS25317 - Ai Discovery for Early Conciliation & Helpline",
                 suppliers=["Informed Solutions Ltd."])
    verdict, cands = BO.match(ACAS, [notice], CH)
    assert verdict == "LOST"
    assert cands[0]["winners"] == ["Informed Solutions Ltd."]
    assert not cands[0]["we_won"]


def test_won_when_the_supplier_is_us_by_ch_number():
    """A win is recognised on the CH number, not a hopeful name match."""
    notice = rel("UK SBS", "PS25317 - Ai Discovery", suppliers=["FUTURE WORK FORCE LIMITED"],
                 ident=CH)
    verdict, cands = BO.match(ACAS, [notice], CH)
    assert verdict == "WON"
    assert cands[0]["we_won"]


def test_unmatched_buyer_is_no_match_not_a_loss():
    """A Scottish/Welsh buyer absent from this feed is a COVERAGE GAP. Never a loss."""
    notice = rel("Scottish Water", "Digital Transformation Services",
                 suppliers=["Someone Else Ltd"])
    verdict, _ = BO.match(HOME_OFFICE, [notice], CH)
    assert verdict == "NO MATCH"
