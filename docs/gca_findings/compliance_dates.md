# Compliance items & dates — GCA portal vs FWF bid library

Prepared 13/07/2026. Answers two questions: (1) where "contracts" and compliance live on the GCA portal, and
(2) the update/expiry dates for each compliance item.

## Where things are stored
- **The GCA Supplier Registration portal does NOT store awarded contracts.** It holds framework/DPS
  *appointments*, the DPSQ/SQ submissions, and *self-declared* compliance answers. The "Buyers" tab only lists
  **Government Commercial Agency** (DUNS 232204180) and **H M Government** — the framework authority, not
  contract awards. Actual call-off contracts sit with each buyer / their own procurement portal.
- **The portal does NOT keep a dated compliance ledger per agreement.** The "DPS Evidence Submission" page for
  AI DPS returns *"there is currently no evidence submission required"* — evidence is only uploaded when GCA
  asks. So there is no per-DPS "Cyber Essentials updated on X" record on the portal.
- **The authoritative dated compliance documents live in the FWF bid library**
  (`knowledge/SharePoint Folder/Bids/02 Bid Library/Company Credentials/`), summarised below.

## What the portal self-declares (per agreement)
| Item | AI DPS | RM6173 | Spark |
|---|---|---|---|
| Cyber Essentials (Q155) | **No** ⚠️ (stale) | **Yes** — certified **06/06/2025**, serial `7887de7c-3c00-4bea-e4495d9747a3` | **No** ⚠️ (stale) |
| Cyber Essentials Plus | No | No | No |
| Insurance declared | EL £5m / PL £10m / PI £10m | EL £5m / PL £10m / PI £10m | EL £5m / PL £1m+ / PI £1m+ |

Only RM6173 carries the Cyber Essentials date/serial; AI DPS and Spark still say "No" and need updating.

## Actual compliance dates (from the bid library) — ⚠️ several at/past expiry
### Cyber Essentials
- Certificate **dated 06/06/2025** (`Cyber Essentials 06062025.png`; serial matches the RM6173 declaration).
- Cyber Essentials is valid **12 months → expires ~06/06/2026**. As at 13/07/2026 this is **~5 weeks past
  expiry** — **confirm it has been renewed** (and then update AI DPS & Spark Q155 to Yes).

### Insurance (Insurance Tracker.xlsx — current schedule, all Hiscox, policy PL-PSC10002770678/08)
| Cover | Level | Start | Expiry | Note |
|---|---|---|---|---|
| Professional Indemnity | **£2m** | 28/05/2025 | **27/05/2026** | ⚠️ portal declares **£10m** — mismatch |
| Employers' Liability | £5m | 28/05/2025 | 27/05/2026 | matches portal |
| Public Liability | £10m | 28/05/2025 | 27/05/2026 | matches portal |
| Cyber & Data | £1m | 28/05/2025 | 27/05/2026 | |
- **All four expired 27/05/2026** per the tracker — as at 13/07/2026 that is **~7 weeks ago**. Either the
  2026–27 renewal exists but isn't logged, or cover has lapsed — **confirm current insurance is in place.**
- **Level mismatch:** portal SQ declares **Professional Indemnity £10m**, but the current policy is **£2m**
  (the £10m PI was the 2024–25 policy). Align the declared figure with the actual cover.

### ISO certifications
- **ISO 27001 (FWF's own): EXPIRED** (`FUTURE WORK FORCE - ISO 27001_Expired.pdf`). FWF now relies on the
  **parent (Arobs) ISO 27001**, confirmed by letter dated **10/2025** (`Letter of Confirmation AROBS - ISO27001_10_2025.pdf`).
- **ISO 9001:** certificate present (`FUTURE WORK FORCE - ISO 9001.pdf`) — date not verified here.

### Financials
- Financial Accounts on file for 2022, 2023, 2024; P&L 2024. (Relevant to the EFS/turnover reconciliation in FINDINGS §4b.)

## Bottom line
There is **no per-contract compliance-date view on the portal** — the portal only self-declares status.
The real dates live in the bid library, and three items need urgent confirmation of currency:
**Cyber Essentials (exp ~06/06/2026), the insurance schedule (exp 27/05/2026), and FWF's own ISO 27001 (expired,
now covered by Arobs)** — plus the PI £10m-vs-£2m mismatch between the portal and the actual policy.
