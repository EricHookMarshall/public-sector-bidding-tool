# Award refresh attempt log

> Durable record of G1 own-award refresh attempts so retries have context.
> Most-recent-first. Each entry: wall-clock start/end (BST), window, result.

## 2026-07-12 ~20:45 BST — findings (why the awards table stays empty)

Chased the specific target: **one contract, buyer "NHS Barnsley", 3–4 years ago** (user).

- **Rate limit was the VPN.** With the VPN off (a normal residential IP) a 7-day probe
  walked **930 award notices with zero 429s**. The earlier 429s were the shared VPN exit IP.
- **BUT the full 4-yr feed walk is still impractical:** a `days=1460` run ran **42 min then was
  killed** — output fully buffered (unobservable), and `_fetch_source` caps at `max_pages=200`
  (~5 months of feed volume at ~930 notices/week), so "4-yr window" ≠ "4 yrs scanned".
- **CH number verified correct:** `11934102` = **"FUTURE WORK FORCE LIMITED"** (two words),
  active, SIC 62020 IT consultancy, Weybridge. So the G1 matcher key is valid — not the problem.
- **The award is NOT discoverable in public OCDS under FWF:** Contracts Finder supplier search +
  web search under BOTH spellings ("Future Workforce" / "Future Work Force") return **no NHS
  Barnsley award to FWF** — only the unrelated national NHSBSA/Infosys ESR deal.
- **Conclusion:** G1 matches suppliers by GB-COH identifier (by design — no false records). The
  NHS Barnsley win most likely (a) named FWF by name only with **no CH identifier** on the notice,
  (b) was **below the CF publication threshold**, or (c) FWF was a **subcontractor** (not the named
  awarded supplier). Any of these makes it invisible to the CH-match connector. The website search
  and the OCDS feed read the same data, so **more scanning won't change the answer** — this award
  must be captured from FWF's **internal records** (Stage-6 Learn / bid library), like the already-
  logged `g1_lost_bids_from_internal` sibling. Filed as `g1_won_but_unpublished_from_internal`.


## 2026-07-12 19:56:47 BST — attempt (session 22 follow-on)

- **Window:** last 1460 days (~4yr) · **CH:** 11934102 · **sources:** FTS + Contracts Finder (award stage)
- **Started:** 2026-07-12 19:56:47 BST
- **Ended:** 2026-07-12 20:38:49 BST  (**2522s**)
- **Exit code:** 143
- **awards table after:** 0

```
```

## 2026-07-12 19:40:24 BST — attempt (session 22 follow-on)

- **Window:** last 1460 days (~4yr) · **CH:** 11934102 · **sources:** FTS + Contracts Finder (award stage)
- **Started:** 2026-07-12 19:40:24 BST
- **Ended:** 2026-07-12 19:45:15 BST  (**291s**)
- **Exit code:** 0
- **awards table after:** 0

```
429 rate-limited; backing off 5s (attempt 1/5)
429 rate-limited; backing off 10s (attempt 2/5)
429 rate-limited; backing off 15s (attempt 3/5)
429 rate-limited; backing off 20s (attempt 4/5)
own_awards source Find a Tender (awards) failed: HTTP Error 429: Too Many Requests
429 rate-limited; backing off 5s (attempt 1/5)
429 rate-limited; backing off 10s (attempt 2/5)
429 rate-limited; backing off 15s (attempt 3/5)
429 rate-limited; backing off 20s (attempt 4/5)
429 rate-limited; backing off 5s (attempt 1/5)
429 rate-limited; backing off 10s (attempt 2/5)
429 rate-limited; backing off 15s (attempt 3/5)
429 rate-limited; backing off 20s (attempt 4/5)
own_awards source Contracts Finder (awards) failed: HTTP Error 429: Too Many Requests
Matched CH 11934102 across 0 award notices (last 1460 days).
  ! Find a Tender (awards) unavailable: HTTP Error 429: Too Many Requests
  ! Contracts Finder (awards) unavailable: HTTP Error 429: Too Many Requests
Found 0 award(s) for us:

DB: 0 inserted, 0 updated → /Users/erichook-marshall/Downloads/Code/public-sector-bidding-tool/src/bids.db
```

