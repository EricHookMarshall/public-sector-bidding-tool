# Evidence ledger

One ledger per answer. One row per claim made in that answer. Prevents
impressive-but-unsupported prose.

| Column | Purpose |
|--------|---------|
| Claim | The assertion made in the answer |
| Evidence | What proves it (project, method, certificate, metric, CV, policy) |
| Source | Link into the SharePoint Evidence Register |
| Owner | Who owns/approves that evidence |
| Status | Approved / Needs update / Expires DD/MM/YYYY |

## Rules

- Every claim in the answer must have a ledger row.
- Every row must have a real **Source** — no blank sources, no "TBC".
- A claim whose evidence is `Expired` or `Needs update` cannot ship until the
  evidence is refreshed (or the claim is cut).
- Claims with no possible evidence must be removed, not softened.

## Example

| Claim | Evidence | Source | Owner | Status |
|-------|----------|--------|-------|--------|
| We deliver Power Platform governance | prior project + method doc | SP link | Practice lead | Approved |
| We hold Cyber Essentials | certificate | SP link | Ops | Expires 01/09/2026 |
| We reduced a client's processing time by 40% | case study metric | SP link | Practice lead | Needs update |
