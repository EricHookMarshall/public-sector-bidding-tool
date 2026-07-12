#!/usr/bin/env python3
"""
Public Contracts Scotland (PCS) — Scottish public sector notices matching our CPV
codes. Source #3 for the PoC, and the first devolved-nation feed.

PCS publishes an OCDS release feed on the shared Proactis/"klickstream" platform,
so CPV extraction, prefix matching and the open-for-bids check are reused verbatim
from find_tender_filter (`ft.*`) — one source of truth for scope. What differs
from Find a Tender / Contracts Finder, and why this needs its own connector:

  - Pagination is MONTH-GRANULAR, not a cursor. The list endpoint takes
    `dateFrom` as `mm-yyyy` and returns that whole month in one response (no
    `links.next`). So we iterate month-by-month across the window and trim the
    edges by publication date client-side.
  - Notices are split by `noticeType`. A single procurement "stage" therefore
    spans two types: the OJEU form and the sub-threshold "Site Notice" form
    (STAGE_NOTICE_TYPES). The sub-threshold notices are the point of adding PCS —
    Find a Tender already carries the above-threshold OJEU notices UK-wide.
  - The buyer sits in `rel.buyer` (as elsewhere) but the delivery region lives on
    the buyer party address, and the human notice page is a `tender.documents`
    link — so `to_record` is bespoke.
  - PCS's TLS chain is incomplete (the server omits its intermediate cert), so no
    default trust store can build the chain. We pin the public Sectigo intermediate
    it should have sent (certs/sectigo_pcs_intermediate.pem) and keep FULL
    verification — see `_ctx` below. No verify=False anywhere.

Run:  python3 public_contracts_scotland.py [days_back] [--no-db]
      Default 120 days. Persists open matching notices into bids.db; --no-db prints only.
"""
import datetime
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request

import db
import find_tender_filter as ft  # reuse cpvs_in, matches, build_prefixes, is_open, STAGES, TARGET_CPV

SOURCE_NAME = "Public Contracts Scotland"
API = "https://api.publiccontractsscotland.gov.uk/v1/Notices"

# A procurement stage maps to the OJEU notice type + its sub-threshold "Site
# Notice" counterpart, so one search covers both. Keys mirror ft.STAGES.
STAGE_NOTICE_TYPES = {
    "tender":   [2, 102],   # OJEU F2 Contract Notice + Site Contract Notice
    "planning": [1, 101],   # OJEU F1 Prior Information + Site PIN
    "award":    [3, 103],   # OJEU F3 Award Notice + Site Award Notice
}

STAGE = "tender"
OPEN_ONLY = True
PAGE_DELAY = 1.0            # seconds between calls — be a good citizen

# Re-export so `pcs.is_open` resolves like the other connectors.
is_open = ft.is_open

# TLS: PCS's server omits its intermediate cert, so the default trust store can't
# build leaf → intermediate → root. We pin the PUBLIC Sectigo intermediate it
# should have sent (a ~2 KB CA cert, safe to commit — not a secret) and add it to
# the system roots, which restores FULL chain verification. No verify=False.
# Refresh if PCS ever reissues under a different CA — the intermediate's URL is in
# the leaf cert's AIA extension:
#   openssl s_client -connect api.publiccontractsscotland.gov.uk:443 -servername \
#     api.publiccontractsscotland.gov.uk </dev/null 2>/dev/null | \
#     openssl x509 -noout -ext authorityInfoAccess   # -> "CA Issuers - URI"
_PINNED_CA = os.path.join(os.path.dirname(__file__), "certs",
                          "sectigo_dv_r36_intermediate.pem")   # shared with sell2wales (same CA)
_ctx = ssl.create_default_context()   # system roots (incl. the Sectigo root) …
_ctx.load_verify_locations(cafile=_PINNED_CA)   # … + the omitted intermediate


def fetch(url):
    """GET + JSON-decode against the fully-verified TLS context (see _ctx)."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60, context=_ctx) as r:
        try:
            return json.load(r)
        except json.JSONDecodeError as e:
            # A 200 with an HTML/error body (maintenance/WAF) would otherwise
            # surface as a raw decode traceback; re-raise cleanly so the
            # per-source handler reports it uniformly.
            raise RuntimeError("upstream returned a non-JSON body") from e


def _parse_dt(s):
    """Parse an OCDS timestamp (may end in 'Z') into an aware datetime, or None."""
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_date(s):
    """A UI date/datetime string → aware UTC datetime (start-of-day for bare dates)."""
    dt = _parse_dt(ft.to_api_datetime(s)) if s else None
    if dt and dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def months_in_range(frm_dt, to_dt):
    """'mm-yyyy' strings covering [frm_dt, to_dt] inclusive — the PCS page unit."""
    y, m = frm_dt.year, frm_dt.month
    out = []
    while (y, m) <= (to_dt.year, to_dt.month):
        out.append(f"{m:02d}-{y}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _buyer_region(rel):
    """Delivery region from the buyer party address (UK NUTS code, e.g. UKM50)."""
    for p in rel.get("parties", []) or []:
        if "buyer" in (p.get("roles") or []):
            reg = (p.get("address") or {}).get("region")
            if reg:
                return reg
    return None


def _buyer_name(rel):
    name = (rel.get("buyer") or {}).get("name")
    if name:
        return name
    for p in rel.get("parties", []) or []:
        if "buyer" in (p.get("roles") or []) and p.get("name"):
            return p["name"]
    return None


def notice_url(rel):
    """Human notice page — a PCS document link, else the canonical API family link."""
    docs = (rel.get("tender", {}) or {}).get("documents", []) or []
    for d in docs:
        if d.get("documentType") == "contractNotice" and d.get("url"):
            return d["url"]
    for d in docs:
        u = d.get("url")
        if u and "publiccontractsscotland.gov.uk" in u:
            return u
    for lnk in rel.get("links") or []:
        if lnk.get("rel") == "canonical" and lnk.get("href"):
            return lnk["href"]
    return None


def to_record(rel, all_cpv):
    """Map one PCS OCDS release into db.COMMON_FIELDS shape."""
    t = rel.get("tender", {}) or {}
    value = t.get("value") or {}
    min_v = t.get("minValue") or {}
    return {
        "source": SOURCE_NAME,
        "source_endpoint": API,
        "ocid": rel.get("ocid") or rel.get("id"),
        "notice_id": rel.get("id"),
        "title": t.get("title", "(no title)"),
        "buyer_name": _buyer_name(rel),
        "description": t.get("description") or rel.get("description"),
        "cpv_codes": ", ".join(all_cpv),
        "region": _buyer_region(rel),
        "country": "United Kingdom",
        "value_min": (min_v.get("amount") if min_v else value.get("amount")),
        "value_max": value.get("amount"),
        "currency": value.get("currency") or min_v.get("currency"),
        "published_date": rel.get("date"),
        "deadline_date": (t.get("tenderPeriod") or {}).get("endDate"),
        "notice_type": ", ".join(rel.get("tag") or []) or None,
        "status": t.get("status"),
        "url": notice_url(rel),
        "raw_json": rel,
    }


def run(days=120, cpv_codes=None, stage=STAGE, open_only=OPEN_ONLY,
        published_from=None, published_to=None, use_db=True):
    """PCS counterpart of find_tender_filter.run() — same parameters and summary
    shape so the source registry can call any connector uniformly. Fetches whole
    months (the PCS page unit) across the window, then trims by publication date
    and applies the same CPV + open-for-bids filters client-side."""
    if stage not in ft.STAGES:
        raise ValueError(f"unknown stage: {stage!r} (expected one of {ft.STAGES})")
    cpv_codes = cpv_codes or ft.TARGET_CPV
    prefixes = ft.build_prefixes(cpv_codes)
    now = datetime.datetime.now(datetime.timezone.utc)
    to_dt = _parse_date(published_to) or now
    frm_dt = _parse_date(published_from) or (now - datetime.timedelta(days=days))
    notice_types = STAGE_NOTICE_TYPES[stage]

    seen, records, pages = set(), [], 0
    for month in months_in_range(frm_dt, to_dt):
        for nt in notice_types:
            query = {"dateFrom": month, "noticeType": nt, "outputType": 0}
            url = f"{API}?{urllib.parse.urlencode(query)}"
            pages += 1
            pkg = fetch(url)
            for rel in pkg.get("releases", []):
                nid = rel.get("id")
                if nid in seen:
                    continue
                seen.add(nid)
                # We fetch whole months; keep only notices published inside the
                # requested window (trim the leading/trailing month's overhang).
                pub = _parse_dt(rel.get("date"))
                if pub and (pub < frm_dt or pub > to_dt):
                    continue
                matched = sorted({cid for cid, _ in ft.cpvs_in(rel)
                                  if ft.matches(cid, prefixes)})
                if not matched:
                    continue
                end = ((rel.get("tender") or {}).get("tenderPeriod") or {}).get("endDate")
                if open_only and not is_open(end, now):
                    continue
                records.append(to_record(rel, matched))
            time.sleep(PAGE_DELAY)

    records.sort(key=lambda r: r["deadline_date"] or "")

    inserted = updated = 0
    if use_db:
        conn = db.connect()
        db.init_db(conn)
        for rec in records:
            if db.upsert_opportunity(conn, rec) == "inserted":
                inserted += 1
            else:
                updated += 1
        conn.commit()
        db.record_source_run(conn, SOURCE_NAME, API, len(seen), len(records))
        conn.close()

    return {
        "source": SOURCE_NAME, "scanned": len(seen), "kept": len(records),
        "inserted": inserted, "updated": updated, "pages": pages, "records": records,
    }


def main():
    argv = [a for a in sys.argv[1:] if a != "--no-db"]
    use_db = "--no-db" not in sys.argv
    days = int(argv[0]) if argv else 120
    res = run(days=days, use_db=use_db)

    print(f"Scanned {res['scanned']} {STAGE}-stage notices from last {days} days "
          f"across {res['pages']} page(s).")
    print(f"Found {res['kept']} ACTIVE notices (open for bids) matching our CPV codes:\n")
    for r in res["records"]:
        print(f"• {r['title']}")
        print(f"  Buyer:  {r['buyer_name'] or '?'}")
        print(f"  Closes: {r['deadline_date']}   CPV: {r['cpv_codes']}")
        print(f"  {r['url']}\n")
    if use_db:
        print(f"DB: {res['inserted']} inserted, {res['updated']} updated → {db.DB_PATH}")
    else:
        print("DB write skipped (--no-db).")


if __name__ == "__main__":
    main()
