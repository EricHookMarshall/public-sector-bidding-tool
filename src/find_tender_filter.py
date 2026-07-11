#!/usr/bin/env python3
"""
Find a Tender — active, early-stage (open-for-bids) notices matching our CPV codes.

Uses the official OCDS API (stages=tender) and filters client-side to:
  - notices whose CPV classification matches our target codes, AND
  - notices still open for bids (tenderPeriod.endDate in the future).

Run:  python3 find_tender_filter.py [days_back] [--no-db]
      Persists matching open notices into bids.db via db.upsert_opportunity()
      and also prints them. Pass --no-db to print only (no DB write).
"""
import json, sys, urllib.request, datetime

import db

SOURCE_NAME = "Find a Tender"
API = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"

# ---------------------------------------------------------------------------
# CONFIG  — these three knobs are what a future UI will drive.
# ---------------------------------------------------------------------------
# 1) CPV codes (from cpv_codes.md). Add/remove codes here to widen/narrow scope.
#    Trailing zeros are stripped to a prefix, so a group code (72000000 -> "72")
#    catches all of its sub-codes; a specific code (72222300) matches only itself.
TARGET_CPV = [
    "72000000", "72211000", "72212920", "72222300",
    "72223000", "72262000", "72263000",
]
# 2) Procurement stage: "tender" = live, open for bids (early/active).
#    The OCDS API also accepts "planning" (pipeline) and "award".
STAGE = "tender"
# 3) Only show notices still open for bids (closing date in the future).
OPEN_ONLY = True
# Stages a connector can be asked to fetch (surfaced to the UI via api.py).
STAGES = ["tender", "planning", "award"]
# ---------------------------------------------------------------------------


def build_prefixes(cpv_codes):
    """CPV ids → match prefixes (trailing zeros stripped so a group code catches
    all of its sub-codes). Longest-first so the most specific prefix wins."""
    return sorted({c.rstrip("0") for c in cpv_codes}, key=len, reverse=True)


# Default prefixes for the module-level TARGET_CPV (CLI / back-compat default).
PREFIXES = build_prefixes(TARGET_CPV)

def matches(cpv_id, prefixes=PREFIXES):
    for p in prefixes:
        if cpv_id.startswith(p):
            return p
    return None


def to_api_datetime(s):
    """Normalise a UI date/datetime string into the ISO form the OCDS APIs want.
    A bare date ("2026-01-01") becomes start-of-day; anything else passes through."""
    if not s:
        return s
    return f"{s}T00:00:00" if len(s) == 10 else s

def is_open(end_date, now):
    """True if a tenderPeriod.endDate is in the future. Parses the offset-aware
    ISO string (the OCDS APIs stamp e.g. +01:00) so the comparison is correct
    across timezones — a lexicographic string compare on an offset-stamped date
    can wrongly call an already-closed tender "open". Falls back to a string
    compare only if parsing fails. Shared by both connectors."""
    if not end_date:
        return False
    try:
        return datetime.datetime.fromisoformat(end_date) >= now
    except ValueError:
        return end_date >= now.isoformat()


def cpvs_in(release):
    out = []
    t = release.get("tender", {}) or {}
    def grab(c):
        if c and c.get("scheme") == "CPV" and c.get("id"):
            out.append((c["id"], c.get("description", "")))
    grab(t.get("classification"))
    for it in t.get("items", []) or []:
        grab(it.get("classification"))
        for a in it.get("additionalClassifications", []) or []:
            grab(a)
    for lot in t.get("lots", []) or []:
        grab(lot.get("classification"))
    return out

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def region_country(t):
    """Best-effort delivery region + country from an OCDS tender block."""
    region = country = None
    for it in t.get("items", []) or []:
        for addr in it.get("deliveryAddresses", []) or []:
            region = region or addr.get("region")
            country = country or addr.get("countryName") or addr.get("country")
    return region, country or "United Kingdom"


def to_record(rel, all_cpv):
    """Map one OCDS release into db.COMMON_FIELDS shape."""
    t = rel.get("tender", {}) or {}
    value = t.get("value") or {}
    min_v = t.get("minValue") or {}
    region, country = region_country(t)
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
        "published_date": rel.get("date"),
        "deadline_date": (t.get("tenderPeriod") or {}).get("endDate"),
        "notice_type": ", ".join(rel.get("tag") or []) or None,
        "status": t.get("status"),
        "url": f"https://www.find-tender.service.gov.uk/Notice/{rel.get('id')}",
        "raw_json": rel,
    }

def run(days=120, cpv_codes=None, stage=STAGE, open_only=OPEN_ONLY,
        published_from=None, published_to=None, use_db=True):
    """Fetch → normalise → (optionally) upsert. All search knobs are parameters
    so the UI can drive the search; the CLI just calls this with defaults.

    Returns a summary dict: source, scanned, kept, inserted, updated, records.
    `published_from`/`published_to` (ISO date or datetime) override the rolling
    `days` window when supplied — the API filters on its `updated` timestamp.
    """
    cpv_codes = cpv_codes or TARGET_CPV
    prefixes = build_prefixes(cpv_codes)
    now = datetime.datetime.now(datetime.timezone.utc)
    frm = (to_api_datetime(published_from) if published_from
           else (now - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S"))
    url = f"{API}?stages={stage}&limit=100&updatedFrom={frm}"
    if published_to:
        url += f"&updatedTo={to_api_datetime(published_to)}"

    seen, records, pages = set(), [], 0
    while url and pages < 200:
        pages += 1
        pkg = fetch(url)
        for rel in pkg.get("releases", []):
            nid = rel.get("id")
            if nid in seen:
                continue
            seen.add(nid)
            matched = sorted({cid for cid, _ in cpvs_in(rel) if matches(cid, prefixes)})
            if not matched:
                continue
            t = rel.get("tender", {}) or {}
            end = (t.get("tenderPeriod") or {}).get("endDate")
            # active = still open for bids (offset-aware; see is_open)
            if open_only and not is_open(end, now):
                continue
            records.append(to_record(rel, matched))
        nxt = (pkg.get("links") or {}).get("next")
        url = nxt if nxt and nxt != url else None

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
