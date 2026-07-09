---
name: fwf-tender-sweep
description: >
  Sweep UK public-sector procurement portals for tender and framework
  opportunities relevant to FWF (Future WorkForce UK Ltd), the Microsoft,
  AI and automation consultancy. Use this whenever a user asks to find,
  search for, sweep, hunt, or check tenders, bids, contracts, procurements,
  RFPs or framework opportunities, or mentions Find a Tender, Contracts
  Finder, CPV codes, or a specific public-sector buyer, even when they do
  not say the word "skill" or "sweep". It carries the CPV code set, the FWF
  keyword taxonomy, the triage rules including the financial-standing
  constraint, and the verify discipline that separates live results from
  cached ones. Reach for it on any phrasing like "find me tenders", "what's
  out there for FWF", "anything new on Find a Tender", or "check for Copilot
  work".
---

# FWF Tender Sweep

A shared FWF skill. Run a structured search of UK public-sector procurement
portals, then hand back a triaged shortlist matched to FWF's Microsoft, AI
and automation lane.

## Read this limitation first, and state it plainly to the user

A skill does not add capability. `web_search` queries a search engine's
index, which is a cache that lags the source by hours to weeks. It is not a
real-time read of the portal database. So the sweep produces leads, not
confirmed-open tenders. The only authoritative check is fetching the notice
page itself, and even portal fetches are sometimes rate-limited (429).

Because of this, the verify step below is not optional. Never present a
shortlist as confirmed-live. Always state, per item, whether it is
source-confirmed or snippet-level.

## Run parameters

If the user has not specified these, assume the defaults and state the
assumptions in one line rather than stopping to ask.

- Sectors: default all. The user may include or exclude (for example NHS and
  central government only, or exclude police and defence).
- Value band: default ignore. The user may set a floor or ceiling.
- Results wanted: default the strongest 6 to 8.
- Focus: default the full net. The user may narrow it (for example Copilot
  enablement only, or RPA only).
- Entity: this skill is scoped to FWF opportunities only. If the request is
  for a different entity, confirm the positioning first, because the
  constraints and messaging differ.

## FWF context that shapes triage

FWF is the small UK arm of Arobs Group, a listed Romanian software company.
Two staff plus delivery recharged from the Romanian arm. The practice covers
Power Platform, M365, Azure, Copilot and Dynamics, plus AI and RPA (UiPath),
with a strong financial-services background.

The binding constraint is economic and financial standing. FWF's standalone
accounts are thin and there is no default parent company guarantee from
Arobs. Any framework that gates hard at selection on turnover multiples or a
PCG is lower priority, and this is the exact wall that G-Cloud 15 hit. Flag
it on each affected item rather than dropping it silently. Routes that gate
less hard, such as sub-threshold Contracts Finder work and DPS or membership
systems, are often the more realistic near-term targets.

## Where to search

Search Find a Tender (find-tender.service.gov.uk) and Contracts Finder
(contractsfinder.service.gov.uk). Contracts Finder holds the smaller,
sub-threshold work that suits a two-person entity, so include it unless the
user scopes it out. Ignore paid aggregators completely (Tender Impulse,
GlobalTenders, TendersOnTime and the like); they resell the same public data
behind a subscription and add nothing.

Run one site-targeted query per keyword cluster. A single broad query
returns shallow results across everything, so keep the queries narrow and
numerous. Add the year only as the current year, never a stale one.

## CPV codes

CPV is a 2008 vocabulary with no clean code for AI or RPA, so buyers scatter
this work across the IT services family. Treat CPV as a coarse net and let
keywords do the filtering. Cast wide with:

- 72000000 IT services: consulting, software development, internet, support
- 72200000 software programming and consultancy
- 72220000 systems and technical consultancy
- 72222300 information technology services
- 72300000 data services
- 72500000 computer-related services
- 72600000 computer support and consultancy
- 48000000 software packages and information systems
- 79400000 business and management consultancy

## Keyword clusters

Query each cluster separately. Copilot is the single highest-signal term.

- Microsoft stack: Power Platform, Power Apps, Power Automate, Power BI,
  Copilot, Copilot Studio, Dynamics 365, Microsoft 365, M365, SharePoint,
  Microsoft Fabric, Azure, Azure OpenAI
- Automation: robotic process automation, RPA, UiPath, Blue Prism,
  intelligent automation, workflow automation, process automation, document
  automation, hyperautomation
- AI: artificial intelligence, machine learning, generative AI, agentic AI,
  chatbot, conversational AI, cognitive services
- Wrapper terms buyers put in titles: digital transformation, low-code,
  cloud migration, application modernisation, systems integration, data
  platform, data analytics, managed services

## Buyer types

Use these to include or exclude sectors: central government departments and
their arm's-length bodies, NHS trusts and ICBs, local councils, universities
and colleges plus their buying consortia (CPC, ESPO), police and blue-light,
housing associations, the devolved administrations, and regulated utilities.
Copilot and M365 estates cluster in central government and NHS; utilities and
police are running large automation and transformation programmes.

## Method

1. Read the run parameters and state any assumptions in one line.
2. Run a site-targeted `web_search` for each keyword cluster in scope,
   across both portals. Reformulate and retry any query that misses.
3. Discard aggregators, closed notices and contract award notices (unless
   the user asked for awards as pipeline intel), and anything clinical-only
   or hardware-only.
4. Verify (see below).
5. Triage and present in the output format below.

## Verify discipline

For the top few candidates, attempt to fetch the notice page with
`web_fetch` to confirm open status, deadline and CPV from source.

- If a fetch succeeds, mark the item source-confirmed and quote the deadline
  and status from the page.
- If a fetch returns 429 or otherwise fails, say so plainly and mark the
  item snippet-level and unverified. Do not retry more than once or twice;
  portal throttling is common and hammering it wastes the turn.
- Treat snippet dates as indicative only. A notice can close after it was
  indexed. Distinguish open tenders from award or closed notices explicitly.

Close the shortlist with a one-line statement of what is source-confirmed
versus snippet-level this run.

## Output format

UK English, concise and direct, pitched for a bid or delivery professional.
Rank by fit to the Microsoft, AI and automation lane, freshest first. For
each item:

- Buyer and notice title
- One-line scope
- Why it fits FWF
- Route type: open tender, framework, or DPS or membership (frameworks and
  DPS are get-listed plays, say so)
- Financial-standing flag where the route gates hard on turnover or a PCG
- The direct notice URL
- Verification state: source-confirmed or snippet-level

Note any contract too large for a two-person entity to prime, marking it
sub-contract only rather than dropping it.

End by offering the complementary next step: a Contracts Finder sweep if the
run focused on Find a Tender, and a refresh of the saved-search and email
alert configuration, since the portal's own alerts are the only genuinely
live monitoring and this sweep is not a substitute for them.
