# Public Sector Bidding API Platform — PoC Brief

## Overview

This proof of concept will be a basic local platform for collecting, storing, filtering, and displaying public sector bidding opportunities from multiple API sources. The platform will include a simple user interface, a lightweight database, and scripts that connect to relevant public sector procurement APIs.

The goal is to demonstrate that bidding opportunity data can be retrieved from multiple public sources, stored locally, kept relevant, and explored through an intuitive interface.

## Objectives

- Build a simple local platform with a user interface and database.
- Connect to public sector bidding APIs using lightweight scripts.
- Store procurement opportunity data locally for reference and filtering.
- Display bidding opportunities from multiple API sources in one place.
- Keep the database focused on active, relevant, and open opportunities.
- Provide intuitive filtering across all available data fields.
- Deliver a proof of concept, not a scaled production system.

## Scope

The platform will run locally and is intended for demonstration and validation purposes only. It will not be designed for high availability, heavy traffic, complex user management, or production-scale data processing.

The PoC will focus on:

- API data retrieval
- Local data storage
- Data refresh and cleanup scripts
- Basic opportunity display
- Filtering and search
- Source comparison across API responses

## Core Components

### 1. User Interface

The UI should be simple, intuitive, and easy to navigate. It should allow users to browse public sector bidding opportunities and filter results by available data fields.

Expected UI features include:

- Dashboard or list view of active opportunities
- Filters for all stored data fields
- Search by keyword
- Source/API indicator for each opportunity
- Opportunity detail view
- Clear status indicators for open, closed, or inactive opportunities

### 2. Lightweight Database

The platform should use a lightweight local database, such as SQLite, to store opportunity data for reference. The database should be simple to maintain and suitable for a local PoC environment.

The database should store only data that is useful for reviewing and acting on open public sector bidding opportunities.

Example stored fields may include:

- Opportunity title
- Description or summary
- Buyer or public body
- Source API
- Reference ID
- Category or sector
- Location
- Published date
- Closing date
- Status
- URL to the original notice
- Last updated timestamp

### 3. API Connector Scripts

The platform should include scripts that connect to public sector bidding APIs, retrieve responses, normalise the data, and write relevant records into the local database.

The scripts should support:

- Pulling data from multiple API sources
- Mapping different API response formats into a common structure
- Updating existing records when source data changes
- Ignoring irrelevant, expired, or closed opportunities
- Recording the source of each opportunity

### 4. Data Maintenance

The database should be maintained so that it contains only active and relevant opportunities that are open to work with.

Maintenance behaviour should include:

- Removing or archiving closed opportunities
- Updating records when APIs return changed details
- Avoiding duplicate entries across sources where possible
- Keeping only opportunities that match the PoC’s relevance criteria
- Recording when each source was last checked

## Data Sources

The platform will display results from multiple public sector bidding API sources. Each source may return different fields and response formats, so the platform should normalise the data into a consistent format before storing and displaying it.

The UI should make it clear which API source each opportunity came from.

## Technical Approach

The PoC can be built using a simple local architecture:

- Frontend/UI: lightweight web interface
- Backend: simple local application server
- Database: SQLite or similar lightweight local database
- Scripts: API connector and data refresh scripts
- Runtime: local development environment

The platform does not need cloud hosting, authentication, enterprise security, or production deployment as part of the PoC.

## Success Criteria

The PoC will be considered successful if it can:

- Retrieve public sector bidding data from more than one API source.
- Store relevant active opportunities in a lightweight local database.
- Remove or ignore closed, expired, or irrelevant records.
- Display opportunities in a simple UI.
- Allow users to filter across all stored data fields.
- Show the source of each API response.
- Run locally without requiring production infrastructure.

## Out of Scope

The following are not required for the PoC:

- Production-scale hosting
- Multi-user permissions
- Advanced analytics
- Automated bid writing
- Payment systems
- Enterprise-grade monitoring
- Complex data warehousing
- Long-term historical storage

## Summary

This project will deliver a local proof-of-concept platform that connects to public sector bidding APIs, stores active and relevant opportunities in a lightweight database, and displays them through an intuitive UI with full filtering. The focus is on validating the workflow and data model rather than building a scalable production platform.
