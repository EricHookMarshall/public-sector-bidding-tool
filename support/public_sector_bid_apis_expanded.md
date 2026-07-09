# Public Sector Bid APIs and Open Data Sources

_Last updated: 2026-06-30_

This file lists publicly available APIs and open-data feeds that can be used by a local proof-of-concept tool to retrieve public-sector bidding, tender, opportunity, notice, award, and procurement data.

## Recommended PoC Priority

For a UK-first PoC, start with sources that are official, stable, documented, and easy to normalize:

1. UK Find a Tender Service
2. UK Contracts Finder
3. Public Contracts Scotland
4. Sell2Wales
5. TED API v3
6. SAM.gov Contract Opportunities API
7. CanadaBuys open procurement datasets
8. World Bank Procurement Notices API
9. UNGM notices API
10. IDB procurement notices dataset

## API and Data Source Inventory

| # | Source | Geography / Coverage | Data type | Primary endpoint / access point | Auth | PoC fit | Notes |
|---:|---|---|---|---|---|---|---|
| 1 | UK Find a Tender Service | UK high-value public procurement | OCDS JSON | `GET https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages` | No public read auth expected | Excellent | You already identified this. Use for high-value UK notices. |
| 2 | UK Find a Tender Service records | UK high-value public procurement | OCDS JSON record packages | `GET https://www.find-tender.service.gov.uk/api/1.0/ocdsRecordPackages` | No public read auth expected | Excellent | Useful when you want a full procurement-process record by OCID rather than only releases. |
| 3 | UK Contracts Finder OCDS Search | England / non-devolved UK lower-value and wider public-sector contracts | OCDS JSON | `GET https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?publishedFrom={date}&publishedTo={date}&stages={stages}&limit={limit}&cursor={cursor}` | No public read auth expected | Excellent | Important UK complement to Find a Tender. Supports cursor pagination and stage filtering. |
| 4 | UK Contracts Finder OCDS Record | England / non-devolved UK procurement records | OCDS JSON | `GET https://www.contractsfinder.service.gov.uk/Published/OCDS/Record/{ocid}` | No public read auth expected | Excellent | Use for full lifecycle record retrieval after finding an OCID. |
| 5 | Public Contracts Scotland | Scotland | OCDS JSON / notice feed | `GET https://api.publiccontractsscotland.gov.uk/v1/Notices` | No public read auth expected | Excellent | Supports notice-list retrieval, with optional date and notice-type parameters. |
| 6 | Public Contracts Scotland notice family | Scotland | OCDS JSON / notice family | `GET https://api.publiccontractsscotland.gov.uk/v1/Notice?id={ocid}` | No public read auth expected | Excellent | Use to retrieve all notices in a procurement process family. |
| 7 | Sell2Wales | Wales | OCDS JSON / notice feed | `GET https://api.sell2wales.gov.wales/v1/Notices` | No public read auth expected | Excellent | Supports notices in OCDS and other output formats. |
| 8 | Sell2Wales notice family | Wales | OCDS JSON / notice family | `GET https://api.sell2wales.gov.wales/v1/Notice?id={ocid}` | No public read auth expected | Excellent | Use to retrieve the notice family by OCID. |
| 9 | TED Search API v3 | EU and EEA public procurement notices | eForms / XML / notice search | `POST https://api.ted.europa.eu/v3/notices/search` | No auth for published-notice search | Very good | Use TED API v3, not deprecated TED API v2 or older v3.0 URLs. Data shape differs from OCDS. |
| 10 | SAM.gov Contract Opportunities | United States federal opportunities | REST JSON | `GET https://api.sam.gov/opportunities/v2/search` | API key required | Very good | Returns active/current US federal contract opportunities. Requires pagination and date filtering. |
| 11 | CanadaBuys tender notices | Canada federal procurement | Open datasets / downloadable data | `https://canadabuys.canada.ca/en/procurement-and-contracting-data` | Usually no auth for public datasets | Good | Better treated as dataset ingestion rather than a live search API. Includes active, expired, and cancelled tender notices. |
| 12 | CanadaBuys support datasets | Canada federal procurement | CSV / open data | `https://donnees-data.tpsgc-pwgsc.gc.ca/ba2/ac-cb/soutien-support-eng.html` | No public auth expected | Good | Useful for bulk ingest and periodic refresh workflows. |
| 13 | AusTender OCDS API | Australian Government procurement | OCDS API | `https://github.com/austender/austender-ocds-api` | Check implementation | Good | Provides AusTender contract notice data in OCDS-compatible machine-readable format. Verify runtime endpoint before integrating. |
| 14 | AusTender public site / contract notices | Australian Government procurement | Search / open data | `https://www.tenders.gov.au/cn/search` | No public read auth expected | Medium | Good source, but the public UI may require more work than the OCDS API route. |
| 15 | New Zealand GETS open data | New Zealand procurement award notices | CSV / open data | `https://www.mbie.govt.nz/cross-government-functions/new-zealand-government-procurement-and-property/open-data` | No public auth expected | Medium | Good for award/market intelligence. Not ideal as a live opportunity API. |
| 16 | World Bank Procurement Notices | World Bank-financed project procurement | Public JSON API / dataset | `http://search.worldbank.org/api/procnotices` | No public auth expected | Very good | Useful global development-project tender source. Filter for open notices and deadlines. |
| 17 | World Bank Finances One procurement dataset | World Bank-financed procurement notices | Dataset / API-backed portal | `https://financesone.worldbank.org/procurement-notice/DS00979` | No public auth expected | Good | Official dataset view; useful for validation and manual inspection. |
| 18 | UNGM Developer Center | United Nations procurement | REST API | `https://developer.ungm.org/` | Some endpoints public; some require token | Good | Covers UN procurement opportunities. Use notice APIs, helper endpoints, and notice-by-key flows. |
| 19 | UNGM get notices | United Nations procurement | REST API | `https://developer.ungm.org/Article/GetNotices` | Check endpoint-specific auth | Good | Use for notice search/list retrieval if access requirements fit the PoC. |
| 20 | UNGM get notice by key | United Nations procurement | REST API | `https://developer.ungm.org/Article/GetNoticeByKey` | Check endpoint-specific auth | Good | Use after retrieving or storing a notice key. |
| 21 | IDB Project Procurement Notices | Inter-American Development Bank-financed projects | Open data / CSV | `https://data.iadb.org/dataset/project-procurement-bidding-notices-and-notification-of-contract-awards` | No public auth expected | Good | Includes general/specific notices, EOIs, open bidding, and contract awards. Treat as dataset ingestion. |
| 22 | IDB Procurement Opportunities | Latin America and Caribbean IDB-financed opportunities | Search portal / data-backed site | `https://www.iadb.org/en/how-we-can-work-together/procurement/procurement-projects` | No public read auth expected | Medium | Useful to validate open opportunities and procurement categories. |
| 23 | Ireland eTenders open data | Ireland public procurement | Open datasets | `https://www.gov.ie/en/office-of-government-procurement/collections/opendata/` | No public auth expected | Medium | Treat as open-data ingestion rather than a stable tender search API. |
| 24 | Ireland data.gov.ie procurement datasets | Ireland public procurement | CSV / open data | `https://data.gov.ie/en_GB/dataset?organization=office-of-government-procurement` | No public auth expected | Medium | Useful for historic/periodic procurement analysis. |
| 25 | Open Contracting Partnership Data Registry | Global OCDS publishers | Registry / downloads | `https://data.open-contracting.org/en/search/` | No public auth expected | Good discovery source | Not a single procurement API, but useful for finding OCDS datasets and publishers globally. |
| 26 | Italy ANAC OCDS portal | Italy public procurement | OCDS open data | `https://dati.anticorruzione.it/opendata/ocds_en` | No public auth expected | Medium | Useful if expanding into EU national OCDS datasets beyond TED. Verify endpoints and refresh method. |
| 27 | OpenTender via OCP registry | EU plus selected jurisdictions | Normalized contracting data | `https://data.open-contracting.org/en/search/` | No public auth expected | Medium | Aggregated/republished data from TED and national portals; useful for analysis but not always ideal for live bid intake. |

## Sources to Treat Carefully

These are useful public procurement portals, but they may not expose a clean, documented, unauthenticated public API suitable for a quick local PoC.

| Source | Coverage | Suggested treatment |
|---|---|---|
| eTendersNI | Northern Ireland opportunities | Use Find a Tender for above-threshold NI notices where possible. Treat eTendersNI itself as portal-first unless a documented API is confirmed. |
| EBRD ECEPP | EBRD-financed procurement | Portal-first. Good opportunity source, but do not assume open API access. |
| ADB procurement notices | Asian Development Bank project procurement | Portal-first unless a supported API or data export is confirmed. |
| AfDB procurement notices | African Development Bank procurement | Portal/RSS-first unless a supported API or data export is confirmed. |
| New Zealand GETS live opportunities | New Zealand public procurement | Official opportunity portal exists; open data appears stronger for award notices than live opportunity API access. |

## Suggested Normalized Fields

Use a lightweight local database table that stores both normalized fields and raw source payloads.

```sql
source TEXT,
source_type TEXT,
source_url TEXT,
ocid TEXT,
notice_id TEXT,
external_reference TEXT,
title TEXT,
buyer_name TEXT,
buyer_country TEXT,
buyer_region TEXT,
description TEXT,
cpv_codes TEXT,
naics_codes TEXT,
unspsc_codes TEXT,
notice_type TEXT,
procurement_stage TEXT,
status TEXT,
value_min NUMERIC,
value_max NUMERIC,
currency TEXT,
published_date TEXT,
updated_date TEXT,
deadline_date TEXT,
award_date TEXT,
contact_name TEXT,
contact_email TEXT,
contact_url TEXT,
notice_url TEXT,
raw_json TEXT,
raw_xml TEXT,
last_seen_at TEXT,
is_active INTEGER
```

## PoC Integration Notes

- Prefer official APIs and open-data feeds over scraping.
- Store raw payloads so mappings can be improved later.
- Normalize only fields needed for searching, filtering, and deduplication.
- Filter local records to active/open notices where possible.
- Keep award/historic data optional unless it helps supplier intelligence.
- Use per-source sync scripts rather than one generic connector, because OCDS, eForms XML, SAM.gov JSON, and CSV datasets differ significantly.
- Implement source-level status tracking: last sync, number of records fetched, number inserted, number expired, and errors.

## Suggested Initial Connector Set

For a practical UK-first local PoC:

1. `find_tender.py`
2. `contracts_finder.py`
3. `public_contracts_scotland.py`
4. `sell2wales.py`
5. `ted_v3.py`
6. `sam_gov.py`
7. `world_bank.py`
8. `ungm.py`

Keep CanadaBuys, IDB, AusTender, Ireland, and New Zealand as second-phase connectors because they are more likely to need dataset ingestion or additional endpoint verification.
