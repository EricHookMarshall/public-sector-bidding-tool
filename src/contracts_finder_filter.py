#!/usr/bin/env python3
"""
Contracts Finder (UK) — active, open-for-bids notices matching our CPV codes.

Source #2 for the PoC. Contracts Finder publishes an OCDS-shaped feed, so this is
a near drop-in of find_tender_filter.py: same release structure, same CPV match
logic, same open-for-bids filter (tenderPeriod.endDate in the future).

Differences from Find a Tender:
  - Endpoint + source name (below).
  - The search window param is `publishedFrom` (FTS uses `updatedFrom`).
  - Notices carry CPV at tender.classification (often nothing at item level).
  - Notice value is frequently absent on CF — value_min/value_max store NULL.
  - Human URL is .../Notice/{guid} (the notice id minus its trailing -<digits>).

CPV scope, prefix matching and the per-release CPV/region extraction are reused
verbatim from find_tender_filter so there is a single source of truth for scope.

Run:  python3 contracts_finder_filter.py [days_back] [--no-db]
      Default 120 days. Persists open matching notices into bids.db; pass --no-db
      to print only.
"""
import re, sys, time, datetime
import urllib.error

import db
import find_tender_filter as ft  # reuse cpvs_in, matches, PREFIXES, region_country, fetch

SOURCE_NAME = "Contracts Finder"
API = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"

# CF rate-limits more aggressively than FTS. Pace page fetches and back off on 429.
PAGE_DELAY = 1.5      # seconds between successful page fetches (be a good citizen)
MAX_RETRIES = 5


def fetch_polite(url):
    """ft.fetch with exponential backoff on HTTP 429 (Too Many Requests)."""
    for attempt in range(MAX_RETRIES):
        try:
            return ft.fetch(url)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES - 1:
                wait = 5 * (attempt + 1)
                print(f"  429 rate-limited; backing off {wait}s "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            raise

# Procurement stage + open-only mirror the reference connector. CPV scope lives
# in find_tender_filter.TARGET_CPV (shared) so both sources stay in lockstep.
STAGE = "tender"
OPEN_ONLY = True


# Offset-aware open/closed check lives in find_tender_filter (shared by both
# connectors). Re-exported so `cf.is_open` keeps resolving.
is_open = ft.is_open


def notice_url(rel):
    """Canonical CF notice page. Prefer a document link, else derive from the id."""
    for d in (rel.get("tender", {}) or {}).get("documents", []) or []:
        u = d.get("url")
        if u and "/Notice/" in u:
            return u
    guid = re.sub(r"-\d+$", "", rel.get("id", ""))
    return f"https://www.contractsfinder.service.gov.uk/Notice/{guid}"


def to_record(rel, all_cpv):
    """Map one CF OCDS release into db.COMMON_FIELDS shape."""
    t = rel.get("tender", {}) or {}
    value = t.get("value") or {}
    min_v = t.get("minValue") or {}
    region, country = ft.region_country(t)
    return {
        "source": SOURCE_NAME,
        "source_endpoint": API,
        "ocid": rel.get("ocid") or rel.get("id"),
        "notice_id": rel.get("id"),
        "title": t.get("title", "(no title)"),
        "buyer_name": (rel.get("buyer") or {}).get("name"),
        "description": t.get("description"),
        "cpv_codes": ", ".join(all_cpv),
        "region": region,
        "country": country,
        "value_min": (min_v.get("amount") if min_v else value.get("amount")),
        "value_max": value.get("amount"),
        "currency": value.get("currency") or min_v.get("currency"),
        "published_date": t.get("datePublished") or rel.get("date"),
        "deadline_date": (t.get("tenderPeriod") or {}).get("endDate"),
        "notice_type": ", ".join(rel.get("tag") or []) or None,
        "status": t.get("status"),
        "url": notice_url(rel),
        "raw_json": rel,
    }


def run(days=120, cpv_codes=None, stage=STAGE, open_only=OPEN_ONLY,
        published_from=None, published_to=None, use_db=True):
    """CF counterpart of find_tender_filter.run(). Same parameters and summary
    shape so the source registry can call either connector uniformly. CF filters
    on `published` rather than `updated`, and paces page fetches (rate limits)."""
    cpv_codes = cpv_codes or ft.TARGET_CPV
    prefixes = ft.build_prefixes(cpv_codes)
    now = datetime.datetime.now(datetime.timezone.utc)
    frm = (ft.to_api_datetime(published_from) if published_from
           else (now - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S"))
    url = f"{API}?stages={stage}&limit=100&publishedFrom={frm}"
    if published_to:
        url += f"&publishedTo={ft.to_api_datetime(published_to)}"

    seen, records, pages = set(), [], 0
    while url and pages < 200:
        pages += 1
        pkg = fetch_polite(url)
        for rel in pkg.get("releases", []):
            nid = rel.get("id")
            if nid in seen:
                continue
            seen.add(nid)
            matched = sorted({cid for cid, _ in ft.cpvs_in(rel) if ft.matches(cid, prefixes)})
            if not matched:
                continue
            end = (rel.get("tender", {}) or {}).get("tenderPeriod", {}) or {}
            if open_only and not is_open(end.get("endDate"), now):
                continue
            records.append(to_record(rel, matched))
        nxt = (pkg.get("links") or {}).get("next")
        url = nxt if nxt and nxt != url else None
        if url:
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
