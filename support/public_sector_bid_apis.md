# Public Sector Bid API Endpoints

This file lists publicly available APIs and open-data endpoints that can be used in a local PoC to retrieve public-sector bidding, tender, opportunity, notice, and award information.

## Recommended UK-first sources

| Source | Coverage | Endpoint / documentation | Format | PoC notes |
|---|---|---|---|---|
| Find a Tender Service | UK high-value public procurement notices | `https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages` | OCDS JSON release packages | Primary UK source already identified. Use for high-value notices and store `ocid`, title, buyer, deadline, status, CPV, value, source URL, and raw JSON. |
| Find a Tender Service Record Packages | UK procurement records | `https://www.find-tender.service.gov.uk/api/1.0/ocdsRecordPackages` | OCDS JSON record packages | Useful where the PoC needs the whole contracting process/record rather than individual notice releases. |
| Contracts Finder | UK / England public contracts, often lower-value opportunities | `https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search` | OCDS JSON release package | Use alongside Find a Tender to cover lower-value UK opportunities. Filter to active/open opportunities before storing. |
| Public Contracts Scotland | Scotland public-sector notices | `https://api.publiccontractsscotland.gov.uk/v1/Notices` | OCDS / JSON | Use for Scottish public-sector opportunities. Supports notice-list retrieval. |
| Public Contracts Scotland notice family | Scotland notice family lookup by OCID | `https://api.publiccontractsscotland.gov.uk/v1/Notice` | OCDS / JSON | Use when you need all notices related to a contracting process. |
| Sell2Wales | Wales public-sector notices | `https://api.sell2wales.gov.wales/v1/Notices` | OCDS / JSON or custom/TED-style output depending on parameters | Use for Welsh public-sector opportunities. Supports filters such as `dateFrom`, `noticeType`, `outputType`, and `locale`. |
| Sell2Wales notice family | Wales notice family lookup | `https://api.sell2wales.gov.wales/v1/Notice` | OCDS / JSON | Use for detail pages or to collect all related notices by contracting process. |

## Wider public-sector sources

| Source | Coverage | Endpoint / documentation | Format | PoC notes |
|---|---|---|---|---|
| TED / Tenders Electronic Daily | EU public procurement notices | `POST https://api.ted.europa.eu/v3/notices/search` | XML / eForms notice data | TED is live, but build against current TED API v3, not deprecated TED API v2. Data shape is not OCDS, so map into the local schema separately. |
| SAM.gov Contract Opportunities | US federal contract opportunities | `https://api.sam.gov/opportunities/v2/search` | JSON | Requires an API key. Returns current active opportunity data with pagination. Useful only if the PoC will include non-UK sources. |
| CanadaBuys tender notices | Government of Canada tenders | `https://open.canada.ca/data/en/dataset/6abd20d4-7a1c-4b38-baa2-9525d0bb2fd2` | CSV / XML / open-data files | More dataset-oriented than API-first. Useful for batch import, not ideal for real-time PoC querying. |
| CanadaBuys OCDS pilot data | Canadian federal procurement history | `https://canadabuys.canada.ca/en/procurement-and-contracting-data` | OCDS JSON file | Includes tenders, awards, standing offers, supply arrangements, and contract history. Useful as sample normalized data. |
| Open Contracting Data Registry | Global OCDS publishers | `https://data.open-contracting.org/` | JSON / CSV / Excel downloads | Good discovery source for additional OCDS publishers. Use as reference, not necessarily as a live bidding feed. |
| AusTender | Australian Government opportunities and contract notices | `https://www.tenders.gov.au/` | Portal / export datasets | Official source for Australian procurement opportunities and awarded contracts. Data exports are more reliable for PoC use than scraping. |
| AusTender Contract Notice Export | Australian Government contract notices | `https://data.gov.au/data/dataset/austender-contract-notice-export` | Export files | Weekly export files; useful for batch loading but not ideal for live opportunity search. |
| AusTender OCDS API project | Australian Government contract notice data | `https://github.com/austender/austender-ocds-api` | OCDS API project / documentation | Check project status before implementation. Useful if the API is available and maintained. |

## Suggested local PoC priority

1. Find a Tender Service — `ocdsReleasePackages`
2. Contracts Finder — `Published/Notices/OCDS/Search`
3. Public Contracts Scotland — `v1/Notices`
4. Sell2Wales — `v1/Notices`
5. TED API v3 — `POST /v3/notices/search`

This priority keeps the first version UK-focused while still proving that the tool can display multiple public-sector bid sources in one UI.

## Suggested normalized local database fields

```text
source
source_endpoint
ocid
notice_id
title
buyer_name
description
cpv_codes
region
country
value_min
value_max
currency
published_date
deadline_date
notice_type
status
url
raw_json_or_xml
last_seen_at
```

## Data retention rule for PoC

Only keep records that are still active, open, or relevant for current bidding work. A simple local rule could be:

```text
keep_notice = deadline_date >= today AND status IN ('active', 'open', 'planned')
```

For sources that do not provide a clean status field, use the deadline date, notice type, and source-specific metadata to decide whether to keep or archive the record.

## Implementation notes

- Store raw source responses for debugging and remapping.
- Normalize only the fields needed for filtering and UI display.
- Add a `source` filter in the UI so users can compare Find a Tender, Contracts Finder, Scotland, Wales, TED, and other feeds.
- Run locally using a lightweight database such as SQLite.
- Do not scale initially; this is a PoC designed to validate source connectivity, filtering, and usefulness of the data.
