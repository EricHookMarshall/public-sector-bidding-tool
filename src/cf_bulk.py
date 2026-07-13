#!/usr/bin/env python3
"""Contracts Finder / Central Digital Platform — DAILY BULK notice extracts.

Why this module exists (the short version: the OCDS APIs cannot answer "who won?").

The opportunity connectors ask the APIs a narrow question — "what's open, in my CPV
scope, right now" — and the APIs answer it well. But "who won the contracts WE bid for"
is a different question, and the OCDS search APIs cannot express it:

  - Find a Tender enumerates its own allowed params in its 400 response:
    stages, limit, cursor, updatedFrom, updatedTo. There is no buyer/supplier/keyword.
  - Contracts Finder SILENTLY IGNORES unknown params — a `keyword=` query returns
    unfiltered rows that look filtered. (Verified: a nonsense keyword returns the same
    rows as a real one. That failure mode is worse than a 400, because it lies.)

So the only way to answer it is to read the whole window and match client-side. Walking
the API for 14 months costs ~10 hours serially, and parallelising it 429s instantly
(measured: 126 of 126 shards failed, 124 of them HTTP 429 — these APIs do not tolerate
concurrency, and the earlier VPN diagnosis was only half the story).

data.gov.uk publishes the SAME notices as one CSV per day on S3. S3 is not the
rate-limited API, so it parallelises safely: the same 14 months took **12 minutes and
50,742 notices with zero failed days**. That is the whole reason this module exists.

Provenance note: the bucket is `cdp-sirsi-*` — the Central Digital Platform — so under
the Procurement Act 2023 this feed carries central-government notices too, not just
low-value Contracts Finder ones (empirically confirmed: Home Office, UK SBS, Office for
Students all appear). It does NOT carry the devolved portals: Scottish (PCS) and Welsh
(Sell2Wales) notices are absent, so a miss for a Scottish/Welsh buyer is a COVERAGE GAP,
never evidence of a loss.

Cached per-day and resumable — a re-run fetches only what's missing. A day that fails is
reported, never silently recorded as "no notices that day".

Run:  python3 cf_bulk.py <from:YYYY-MM-DD> <to:YYYY-MM-DD>
"""
import csv
import datetime
import io
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cache lives next to the code (same convention as bids.db / .env) so it travels with it.
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "cf_bulk")

BASE = ("https://cdp-sirsi-production-cfs-471112843276.s3.eu-west-2.amazonaws.com"
        "/Harvester-new")
WORKERS = 10          # S3, not the throttled API — but stay a good citizen

_lock = threading.Lock()
_stat = {"days": 0, "rows": 0}


def slim_row(row):
    """One flattened-OCDS CSV row -> just the fields outcome-matching needs.

    The CSV is one column per JSON path (releases/0/awards/N/suppliers/M/name) and the
    COLUMN SET VARIES BY DAY (1372 columns one day, 574 another) because it's generated
    from whatever that day's notices happen to contain. So never assume a column exists:
    walk the award/supplier/party indices until they run out.
    """
    g = lambda k: (row.get(k) or "").strip()

    awards, ai = [], 0
    while True:
        pre = f"releases/0/awards/{ai}"
        if not any(k.startswith(pre + "/") for k in row):
            break
        sups, si = [], 0
        while True:
            spre = f"{pre}/suppliers/{si}"
            if not g(f"{spre}/name") and not g(f"{spre}/id"):
                break
            sups.append({"name": g(f"{spre}/name"), "id": g(f"{spre}/id")})
            si += 1
        if g(f"{pre}/id") or sups:
            awards.append({
                "id": g(f"{pre}/id"), "status": g(f"{pre}/status"),
                "date": g(f"{pre}/date") or g(f"{pre}/datePublished"),
                "amount": g(f"{pre}/value/amount"), "currency": g(f"{pre}/value/currency"),
                "suppliers": sups,
            })
        ai += 1

    parties, pi = [], 0
    while True:
        ppre = f"releases/0/parties/{pi}"
        if not g(f"{ppre}/name") and not g(f"{ppre}/id"):
            break
        parties.append({"id": g(f"{ppre}/id"), "name": g(f"{ppre}/name"),
                        "scheme": g(f"{ppre}/identifier/scheme"),
                        "ident": g(f"{ppre}/identifier/id"), "roles": g(f"{ppre}/roles")})
        pi += 1

    return {
        "ocid": g("releases/0/ocid"),
        "buyer": g("releases/0/buyer/name"),
        "title": g("releases/0/tender/title") or g("releases/0/title"),
        "description": g("releases/0/tender/description")[:300],
        "tender_id": g("releases/0/tender/id"),
        "tender_status": g("releases/0/tender/status"),
        "deadline": g("releases/0/tender/tenderPeriod/endDate"),
        "awards": awards,
        "parties": parties,
    }


def fetch_day(day):
    """Cache one day's notices. Returns (n_rows, error_or_None)."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{day.isoformat()}.json")
    if os.path.exists(path):
        try:
            with open(path) as fh:
                return len(json.load(fh)), None
        except Exception:
            os.remove(path)                    # corrupt entry -> refetch

    url = f"{BASE}/{day.strftime('%Y-%m')}/Contracts%20Finder%20OCDS%20{day.isoformat()}.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "fwf-bid-tool"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 404):             # no file published that day (weekends/holidays)
            with open(path, "w") as fh:
                json.dump([], fh)
            return 0, None
        return 0, f"HTTP {exc.code}"
    except Exception as exc:
        return 0, f"{type(exc).__name__}: {exc}"

    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig", errors="replace")))
        rows = [slim_row(r) for r in reader]
    except Exception as exc:
        return 0, f"parse: {type(exc).__name__}: {exc}"

    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(rows, fh)
    os.replace(tmp, path)                      # atomic: a killed run leaves no half-file
    with _lock:
        _stat["days"] += 1
        _stat["rows"] += len(rows)
    return len(rows), None


def run(frm, to, workers=WORKERS):
    """Fetch every day in [frm, to]. Returns {days, notices, errors}."""
    days, day = [], frm
    while day <= to:
        days.append(day)
        day += datetime.timedelta(days=1)

    errors = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fetch_day, d): d for d in days}
        for fut in as_completed(futs):
            day = futs[fut]
            try:
                _n, err = fut.result()
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"
            if err:
                errors.append({"day": day.isoformat(), "error": err})
    return {"days": len(days), "notices": _stat["rows"], "errors": errors}


def load_cached():
    """Every cached notice, de-duped on (ocid, title). Empty if nothing fetched yet."""
    if not os.path.isdir(CACHE):
        return []
    seen, out = set(), []
    for fn in sorted(os.listdir(CACHE)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(CACHE, fn)) as fh:
            for row in json.load(fh):
                k = (row.get("ocid"), row.get("title"))
                if k in seen:
                    continue
                seen.add(k)
                out.append(row)
    return out


def main():
    if len(sys.argv) < 3:
        print("usage: python3 cf_bulk.py <from:YYYY-MM-DD> <to:YYYY-MM-DD>")
        raise SystemExit(2)
    frm = datetime.date.fromisoformat(sys.argv[1])
    to = datetime.date.fromisoformat(sys.argv[2])
    print(f"bulk: {frm} -> {to} ({WORKERS} workers)")
    t0 = time.time()
    res = run(frm, to)
    print(f"DONE {res['notices']:,} notices over {res['days']} days, "
          f"{len(res['errors'])} failed days, {(time.time()-t0)/60:.1f} min")
    for e in res["errors"][:10]:
        print(f"  MISSING {e['day']}: {e['error']}")   # a gap is a KNOWN gap, not a zero


if __name__ == "__main__":
    main()
