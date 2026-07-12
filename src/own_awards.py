#!/usr/bin/env python3
"""
G1 — FWF's OWN awarded contracts, pulled from the public OCDS *award* packages
(Find a Tender + Contracts Finder) and matched to FWF by its Companies House
number (identifier scheme GB-COH).

This is the mirror image of the opportunity connectors: instead of "notices I
could bid on" it answers "contracts WE have already won", which the app needs to
show FWF's public track record and (feeding G2) reason about frameworks.

Why match on the Companies House number, not the name: a fuzzy name match
("Future Workforce…") would produce false records, and a false record is the
exact failure class this whole tool exists to prevent (knowledge/VERIFIED_FACTS
— a missed clarification killed a real bid; accuracy is the point). The CH number
is the one identifier OCDS carries that is unambiguous, so an award only counts
as ours when a supplier party on it carries GB-COH == our number.

The number itself is **configuration, never hardcoded** (facts decay / it's
org-specific): callers pass it in — api.py resolves it from the app_settings
`own_org` record, the CLI from argv. An empty number matches nothing (and run()
refuses to fetch), so the connector is inert until FWF's number is set.

Run:  python3 own_awards.py <companies_house_number> [days_back] [--no-db]
"""
import datetime
import logging
import re
import sys
import time

import contracts_finder_filter as cf
import db
import find_tender_filter as ft

log = logging.getLogger("own_awards")

# Seconds to pace successive page fetches. An award scan walks the WHOLE award
# feed (unlike the opportunity connectors, which stop at the CPV-matched slice),
# so it's page-heavy — pace it to stay under both APIs' rate limits.
PAGE_DELAY = 1.0

# Both sources go through cf.fetch_polite — the shared 429-backoff wrapper around
# ft.fetch (defined in contracts_finder_filter, but source-agnostic). The first
# award run 429'd because the FTS path used the bare ft.fetch with no backoff;
# routing FTS through the polite wrapper too makes the heavy scan resilient.
_polite_fetch = cf.fetch_polite

# OCDS org-identifier schemes that denote a UK Companies House registration.
# Publishers are inconsistent (GB-COH is the register's official scheme code, but
# some emit a "companies house" free-text variant), so we match tolerantly on the
# scheme *and* strictly on the number.
_COH_SCHEME_RE = re.compile(r"(GB-?COH|COMPANIES\s*HOUSE)", re.IGNORECASE)

# The two OCDS award endpoints. Each entry: fetch fn + how to page + a notice-URL
# builder, mirroring the per-source shape the opportunity connectors already use.
SOURCES = [
    {
        "name": "Find a Tender (awards)",
        "endpoint": ft.API,
        "fetch": _polite_fetch,
        "param": "updatedFrom",
        "notice_url": lambda rel: f"https://www.find-tender.service.gov.uk/Notice/{rel.get('id')}",
    },
    {
        "name": "Contracts Finder (awards)",
        "endpoint": cf.API,
        "fetch": _polite_fetch,
        "param": "publishedFrom",
        "notice_url": cf.notice_url,
    },
]


def normalise_ch(value):
    """Canonical form of a Companies House number for comparison: upper-cased,
    non-alphanumerics stripped. Returns "" for falsy input. (Prefix letters like
    SC/NI are kept; only formatting/whitespace is removed.)"""
    if not value:
        return ""
    return re.sub(r"[^0-9A-Za-z]", "", str(value)).upper()


def _ch_equal(a, b):
    """Do two CH numbers refer to the same registration? Exact after
    normalisation, or equal once leading zeros are dropped from purely-numeric
    forms (some publishers pad '01234567', others don't)."""
    a, b = normalise_ch(a), normalise_ch(b)
    if not a or not b:
        return False
    if a == b:
        return True
    if a.isdigit() and b.isdigit():
        return a.lstrip("0") == b.lstrip("0")
    return False


def _party_identifiers(party):
    """Every (scheme, id) an OCDS party carries — its primary identifier plus any
    additionalIdentifiers. Skips blanks."""
    out = []
    ident = party.get("identifier") or {}
    if ident.get("id"):
        out.append((ident.get("scheme") or "", str(ident["id"])))
    for extra in party.get("additionalIdentifiers") or []:
        if extra.get("id"):
            out.append((extra.get("scheme") or "", str(extra["id"])))
    return out


def _is_our_coh(scheme, ident_id, ch_number):
    """True when (scheme, id) is a Companies House identifier equal to our number."""
    return bool(_COH_SCHEME_RE.search(scheme or "")) and _ch_equal(ident_id, ch_number)


def matched_supplier_party_ids(release, ch_number):
    """The org-ids (release.parties[].id) of supplier parties on this release whose
    Companies House identifier is ours. Returns {party_id: party_name}. A party
    must actually be a supplier (role 'supplier' / 'tenderer') — we don't count a
    buyer or funder that happens to share the number."""
    matched = {}
    for party in release.get("parties") or []:
        roles = {str(r).lower() for r in (party.get("roles") or [])}
        if roles and not (roles & {"supplier", "tenderer"}):
            continue
        for scheme, ident_id in _party_identifiers(party):
            if _is_our_coh(scheme, ident_id, ch_number):
                matched[party.get("id")] = party.get("name") or ""
                break
    return matched


def _contract_period(award, tender):
    """(startDate, endDate) for the contract, preferring the award's own period,
    falling back to the tender's."""
    per = (award.get("contractPeriod") or tender.get("contractPeriod") or {})
    return per.get("startDate"), per.get("endDate")


def to_award_record(source, release, award, party_name, ch_number, notice_url):
    """Map one matched OCDS award into db.AWARD_FIELDS shape."""
    tender = release.get("tender") or {}
    value = award.get("value") or {}
    start, end = _contract_period(award, tender)
    # The supplier as named on THIS award (fall back to the matched party's name).
    supplier_name = party_name
    for sup in award.get("suppliers") or []:
        if sup.get("name"):
            supplier_name = sup["name"]
            break
    cpvs = sorted({cid for cid, _ in ft.cpvs_in(release)})
    return {
        "source": source["name"],
        "source_endpoint": source["endpoint"],
        "ocid": release.get("ocid") or release.get("id"),
        "award_id": award.get("id") or f"{release.get('ocid') or release.get('id')}-award",
        "title": tender.get("title") or "(no title)",
        "buyer_name": (release.get("buyer") or {}).get("name"),
        "supplier_name": supplier_name,
        "supplier_scheme": "GB-COH",
        "supplier_id": normalise_ch(ch_number),
        "cpv_codes": ", ".join(cpvs),
        "value_amount": value.get("amount"),
        "currency": value.get("currency"),
        "award_date": award.get("date"),
        "contract_start": start,
        "contract_end": end,
        "status": award.get("status"),
        "url": notice_url(release),
        "raw_json": {"award": award, "ocid": release.get("ocid") or release.get("id")},
    }


def _awards_in(release, ch_number):
    """Every award on a release that is ours (supplier party matched by CH number).
    Yields (award_dict, supplier_party_name)."""
    matched = matched_supplier_party_ids(release, ch_number)
    for award in release.get("awards") or []:
        # An award names its suppliers either by party-id reference or inline; try
        # both so we catch releases that don't use the parties[] block.
        for sup in award.get("suppliers") or []:
            if sup.get("id") in matched:
                yield award, matched[sup["id"]]
                break
            if any(_is_our_coh(s, i, ch_number)
                   for s, i in _party_identifiers(sup)):
                yield award, sup.get("name") or ""
                break


def _fetch_source(source, frm, ch_number, max_pages=200):
    """Pull one OCDS award source and return (records, scanned, pages). Raises on a
    fetch/parse failure — the caller decides whether that poisons the whole run."""
    import urllib.parse

    query = {"stages": "award", "limit": 100, source["param"]: frm}
    url = f"{source['endpoint']}?{urllib.parse.urlencode(query)}"
    records, scanned, pages = [], 0, 0
    while url and pages < max_pages:
        pages += 1
        pkg = source["fetch"](url)
        for rel in pkg.get("releases", []):
            scanned += 1
            for award, party_name in _awards_in(rel, ch_number):
                records.append(
                    to_award_record(source, rel, award, party_name, ch_number, source["notice_url"])
                )
        nxt = (pkg.get("links") or {}).get("next")
        url = nxt if nxt and nxt != url else None
        if url:
            time.sleep(PAGE_DELAY)   # pace the walk over the full award feed
    return records, scanned, pages


def run(companies_house_number, days=365, use_db=True, sources=None):
    """Fetch → match-by-CH-number → (optionally) upsert FWF's own awards.

    `companies_house_number` is required and must be non-empty — an empty number
    would match nothing, so we refuse rather than silently return zero. Each source
    is fetched independently: one source erroring degrades (records a `source_error`)
    rather than poisoning the whole run, mirroring the resilient search connectors.

    Returns: {configured, ch_number, scanned, kept, inserted, updated, records,
              source_errors, incomplete}.
    """
    ch = normalise_ch(companies_house_number)
    if not ch:
        raise ValueError("own_awards.run requires a Companies House number")

    now = datetime.datetime.now(datetime.timezone.utc)
    frm = (now - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")

    records, scanned, source_errors = [], 0, []
    for source in (sources or SOURCES):
        try:
            recs, sc, _pages = _fetch_source(source, frm, ch)
            records.extend(recs)
            scanned += sc
        except Exception as exc:  # a broken source shouldn't lose the others' hits
            log.warning("own_awards source %s failed: %s", source["name"], exc)
            source_errors.append({"source": source["name"], "error": str(exc)})

    # De-dupe across sources on (source, award_id) is handled by the DB key; within
    # this run, sort newest-first for display.
    records.sort(key=lambda r: r.get("award_date") or "", reverse=True)

    inserted = updated = 0
    if use_db:
        conn = db.connect()
        db.init_db(conn)
        for rec in records:
            if db.upsert_award(conn, rec) == "inserted":
                inserted += 1
            else:
                updated += 1
        conn.commit()
        for source in (sources or SOURCES):
            db.record_source_run(conn, source["name"], source["endpoint"], scanned, len(records))
        conn.close()

    return {
        "configured": True,
        "ch_number": ch,
        "scanned": scanned,
        "kept": len(records),
        "inserted": inserted,
        "updated": updated,
        "records": records,
        "source_errors": source_errors,
        "incomplete": bool(source_errors),
    }


def main():
    args = [a for a in sys.argv[1:] if a != "--no-db"]
    use_db = "--no-db" not in sys.argv
    if not args:
        print("usage: python3 own_awards.py <companies_house_number> [days_back] [--no-db]")
        raise SystemExit(2)
    ch = args[0]
    days = int(args[1]) if len(args) > 1 else 365
    res = run(ch, days=days, use_db=use_db)

    print(f"Matched CH {res['ch_number']} across {res['scanned']} award notices "
          f"(last {days} days).")
    if res["source_errors"]:
        for e in res["source_errors"]:
            print(f"  ! {e['source']} unavailable: {e['error']}")
    print(f"Found {res['kept']} award(s) for us:\n")
    for r in res["records"]:
        val = f"{r['currency'] or ''} {r['value_amount'] or '?'}".strip()
        print(f"• {r['title']}")
        print(f"  Buyer:  {r['buyer_name'] or '?'}   Awarded: {r['award_date'] or '?'}   Value: {val}")
        print(f"  {r['url']}\n")
    if use_db:
        print(f"DB: {res['inserted']} inserted, {res['updated']} updated → {db.DB_PATH}")
    else:
        print("DB write skipped (--no-db).")


if __name__ == "__main__":
    main()
