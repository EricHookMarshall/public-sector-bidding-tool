# downloads/ — what's here and what still needs a manual fetch

## Captured into this folder
- **questionnaire_register_export.csv** — the full "Export questionnaires as CSV" from the GCA
  Supplier Registration dashboard, reconstructed faithfully (17 rows incl. header). This is the
  master register of every FWF questionnaire/DPS/MSA record on the portal, with status, reference,
  last-edited date and assigned owner.

## Needs a manual browser download (binary — could not be routed through the automation channel)
These are authenticated files behind FWF's login. Fastest way to save each into this folder:

1. **Financial Report (PDF, ~38 KB)**
   - Confirmed present. File title: `future_work_force_limited_financial_report`, generated 13/07/2026.
   - Get it: GCA dashboard → right-hand **Reports** panel → **Financial Report (Opens in a new window)** →
     save/print to PDF into this `downloads/` folder.

2. **"Download questions" per agreement (optional, portal-native full Q&A export)**
   - Each agreement's View page has an **Options → Download questions** button that exports the complete
     question set with FWF's answers. The key answers are already summarised in `../captures/`, but if you
     want the portal's own file for the record, download from:
     - AI DPS (SQ-A3P6TMM)
     - RM6173 Automation Marketplace (SQ-GYHB4TU)
     - Spark DPS (SQ-3PG928A)

> Note: the portal times out after ~a few minutes idle — click "Ok" on the session prompt if it appears.
