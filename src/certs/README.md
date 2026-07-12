# Pinned CA certificates

Public CA certificates deliberately committed here. **These are not secrets** —
they are public intermediate CA certs, published by the issuing CA, that a
misconfigured upstream server fails to send in its TLS handshake. Pinning the
omitted intermediate lets us keep **full** certificate verification (no
`verify=False`) instead of disabling it.

| File | Why | Used by | Refresh |
|------|-----|---------|---------|
| `sectigo_dv_r36_intermediate.pem` | Both `api.publiccontractsscotland.gov.uk` **and** `api.sell2wales.gov.wales` (same Proactis platform) omit their intermediate (`Sectigo Public Server Authentication CA DV R36`), so the chain to the trusted Sectigo root can't be built. Valid to **2036**. | `public_contracts_scotland.py`, `sell2wales.py` | Re-fetch from the AIA "CA Issuers" URL in the leaf cert (see the `_ctx` note in those modules) if either site reissues under a different CA. |
