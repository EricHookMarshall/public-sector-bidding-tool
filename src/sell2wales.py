#!/usr/bin/env python3
"""
Sell2Wales — Welsh public sector notices matching our CPV codes. Source #4, and
the second devolved-nation feed. Sell2Wales runs on the SAME Proactis/"klickstream"
platform as Public Contracts Scotland, so it reuses PCS's shared, platform-generic
helpers (month paging, date parsing, buyer/region extraction) rather than
re-implementing them — see the `pcs.*` calls below. What differs:

  - Host + source name (below), and a required bilingual `locale` param
    (en = 2057, cy = 1106) that PCS does not have.
  - Sub-threshold "website" notice types are 51/52/53 (PCS uses 101/102/103).
  - Same broken TLS chain as PCS (server omits its intermediate) → same pinned
    Sectigo intermediate, full verification kept. No verify=False.

RESILIENCE — Sell2Wales's list API is unreliable: as at 2026-07 its `/Notices`
endpoint returns HTTP 500 ("Error converting data type nvarchar to float", a
server-side SQL fault) for *every* query, including its own documented example.
So this connector treats each (month × noticeType) as an independent PARTITION:
a partition that fails after bounded retries is recorded as a structured error
and SKIPPED — it never aborts the other partitions or the wider search. When the
upstream is healthy the connector ingests normally; while it's broken it degrades
to "0 kept + partition errors" instead of failing the whole source.

Not yet built (explicit follow-ons, see _session/todo.md): the official monthly
bulk-download fallback (an aspx-postback form — needs its own work) and Find a
Tender cross-publish recovery for Welsh notices mirrored there.

Run:  python3 sell2wales.py [days_back] [--no-db]
"""
import datetime
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import db
import find_tender_filter as ft
import public_contracts_scotland as pcs  # reuse shared Proactis helpers (same platform)

SOURCE_NAME = "Sell2Wales"
API = "https://api.sell2wales.gov.wales/v1/Notices"
LOCALE_EN = 2057                 # Sell2Wales is bilingual; 2057 = English (1106 = Welsh)

# Stage → OJEU notice type + its Welsh sub-threshold "website" counterpart.
STAGE_NOTICE_TYPES = {
    "tender":   [2, 51],
    "planning": [1, 52],
    "award":    [3, 53],
}

STAGE = "tender"
OPEN_ONLY = True
PAGE_DELAY = 1.0                 # between partitions — be a good citizen
MAX_PARTITION_TRIES = 2         # bounded retry per partition (transient 500s), then record+skip
RETRY_BACKOFF = (2, 5)          # seconds before retry 2, retry 3, …

is_open = ft.is_open

# Same broken chain as PCS, same public Sectigo intermediate → full verification.
_PINNED_CA = os.path.join(os.path.dirname(__file__), "certs",
                          "sectigo_dv_r36_intermediate.pem")
_ctx = ssl.create_default_context()
_ctx.load_verify_locations(cafile=_PINNED_CA)


class PartitionError(RuntimeError):
    """A (month, noticeType) partition that failed after bounded retries. Carries
    the http status (if any) so run() can build the structured error record."""
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def _fetch(url):
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                             "Accept": "application/json"}),
        timeout=60, context=_ctx) as r:
        try:
            return json.load(r)
        except json.JSONDecodeError as e:
            raise RuntimeError("upstream returned a non-JSON body") from e


def fetch_partition(month, notice_type):
    """One partition's release package, with bounded retry + backoff. Raises
    PartitionError (with the http status where known) if it never succeeds — the
    caller records it and moves on, so one bad partition can't poison the source."""
    query = {"dateFrom": month, "noticeType": notice_type,
             "outputType": 0, "locale": LOCALE_EN}   # outputType 0 = OCDS (the only form we normalise)
    url = f"{API}?{urllib.parse.urlencode(query)}"
    last = None
    for attempt in range(MAX_PARTITION_TRIES):
        try:
            return fetch_partition._fetch(url)
        except urllib.error.HTTPError as e:
            last = PartitionError(f"HTTP {e.code}: {_http_reason(e)}", status=e.code)
        except (urllib.error.URLError, RuntimeError) as e:
            last = PartitionError(str(e))
        if attempt < MAX_PARTITION_TRIES - 1:
            time.sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])
    raise last


# Indirection so tests can substitute the network without monkeypatching urllib.
fetch_partition._fetch = _fetch


def _http_reason(err):
    """A short, safe reason from an HTTPError body (the SQL fault title, if any)."""
    try:
        body = err.read(400).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 — best-effort diagnostic only
        return "error"
    import re
    m = re.search(r"<title>(.*?)</title>", body, re.I | re.S)
    return (m.group(1).strip() if m else body[:80]).replace("\n", " ")[:120]


def notice_url(rel):
    """Human notice page — a Sell2Wales document link, else the canonical API link."""
    docs = (rel.get("tender", {}) or {}).get("documents", []) or []
    for d in docs:
        if d.get("documentType") == "contractNotice" and d.get("url"):
            return d["url"]
    for d in docs:
        u = d.get("url")
        if u and "sell2wales.gov.wales" in u:
            return u
    for lnk in rel.get("links") or []:
        if lnk.get("rel") == "canonical" and lnk.get("href"):
            return lnk["href"]
    return None


def to_record(rel, all_cpv):
    """Map one Sell2Wales OCDS release into db.COMMON_FIELDS shape. Field
    extraction is shared with PCS (same platform); only source/url differ."""
    t = rel.get("tender", {}) or {}
    value = t.get("value") or {}
    min_v = t.get("minValue") or {}
    return {
        "source": SOURCE_NAME,
        "source_endpoint": API,
        "ocid": rel.get("ocid") or rel.get("id"),
        "notice_id": rel.get("id"),
        "title": t.get("title", "(no title)"),
        "buyer_name": pcs._buyer_name(rel),
        "description": t.get("description") or rel.get("description"),
        "cpv_codes": ", ".join(all_cpv),
        "region": pcs._buyer_region(rel),
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
    """Sell2Wales counterpart of the other connectors' run() — same parameters and
    summary shape, plus a `partition_errors` list and an `incomplete` flag so a
    flaky upstream is reported, not silently swallowed. A partition (month ×
    noticeType) that fails after bounded retries is recorded and skipped."""
    if stage not in ft.STAGES:
        raise ValueError(f"unknown stage: {stage!r} (expected one of {ft.STAGES})")
    cpv_codes = cpv_codes or ft.TARGET_CPV
    prefixes = ft.build_prefixes(cpv_codes)
    now = datetime.datetime.now(datetime.timezone.utc)
    to_dt = pcs._parse_date(published_to) or now
    frm_dt = pcs._parse_date(published_from) or (now - datetime.timedelta(days=days))
    notice_types = STAGE_NOTICE_TYPES[stage]

    seen, records, pages = set(), [], 0
    partition_errors = []
    for month in pcs.months_in_range(frm_dt, to_dt):
        for nt in notice_types:
            try:
                pkg = fetch_partition(month, nt)
            except PartitionError as e:
                # Record the poisoned partition and move on — never abort the source.
                partition_errors.append({
                    "source": "sell2wales",
                    "partition": {"month": month, "noticeType": nt,
                                  "outputType": 0, "locale": LOCALE_EN},
                    "httpStatus": e.status,
                    "error": str(e)[:200],
                    "retryable": True,
                    "fallback": "official-monthly-download",
                })
                continue
            pages += 1
            for rel in pkg.get("releases", []):
                nid = rel.get("id")
                if nid in seen:
                    continue
                seen.add(nid)
                pub = pcs._parse_dt(rel.get("date"))
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
        "partition_errors": partition_errors, "incomplete": bool(partition_errors),
    }


def main():
    argv = [a for a in sys.argv[1:] if a != "--no-db"]
    use_db = "--no-db" not in sys.argv
    days = int(argv[0]) if argv else 120
    res = run(days=days, use_db=use_db)

    print(f"Scanned {res['scanned']} notices across {res['pages']} healthy "
          f"partition(s); {len(res['partition_errors'])} partition(s) failed.")
    print(f"Found {res['kept']} ACTIVE notices matching our CPV codes:\n")
    for r in res["records"]:
        print(f"• {r['title']}")
        print(f"  Buyer:  {r['buyer_name'] or '?'}")
        print(f"  Closes: {r['deadline_date']}   CPV: {r['cpv_codes']}")
        print(f"  {r['url']}\n")
    if res["partition_errors"]:
        print("Partition errors (upstream unavailable — will recover when fixed):")
        for pe in res["partition_errors"]:
            p = pe["partition"]
            print(f"  · {p['month']} nt={p['noticeType']}: {pe['httpStatus']} {pe['error']}")
    if use_db:
        print(f"\nDB: {res['inserted']} inserted, {res['updated']} updated → {db.DB_PATH}")
    else:
        print("\nDB write skipped (--no-db).")


if __name__ == "__main__":
    main()
