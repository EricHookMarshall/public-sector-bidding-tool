# B00 — record schema

## Answer record (Approved Answer Bank)

```json
{
  "buyer": "Example Council",                    // required
  "sector": "local_gov",                          // NHS|local_gov|central_gov|education|blue_light|other
  "framework": "G-Cloud 15",
  "route": "framework_calloff",                   // framework|dps|open_tender|framework_calloff
  "rm_code": "RM1557.15",
  "regime": "PA23",                               // PA23|PCR2015
  "lot": "Lot 3",
  "question_text": "Describe your approach to ...", // required — retrieval searches this
  "answer_text": "...",                            // required
  "theme": "incident response",
  "question_type": "technical",                    // eligibility|technical|commercial|legal|social_value|pricing
  "service_line": "Azure AI",
  "outcome": "won",                                // won|lost|shortlisted|non_compliant|withdrawn|unknown
  "score_feedback": "9/10, praised clarity",
  "date_submitted": "2025-11-02",
  "content_owner": "Practice Lead",                // who can approve reuse
  "reuse_status": "needs_update",                  // approved|needs_update|do_not_reuse (default needs_update)
  "approved_by": "",                               // required if reuse_status=approved
  "confidentiality": "internal",                   // public|internal|client_confidential|commercially_sensitive
  "timebound": true,                               // does it contain time-bound facts?
  "expiry_date": "2026-06-30",                     // required if timebound
  "source_link": "https://.../source.docx",        // required — traceability
  "evidence_used": [
    {"type": "certificate", "claim": "Cyber Essentials", "owner": "Ops",
     "expiry_date": "2026-09-01", "approved_external": true,
     "source_link": "https://.../ce-cert.pdf"}
  ]
}
```

## Defaults & rules

- `reuse_status` defaults to **needs_update**. Never auto-`approved`.
- `approved` requires a named `approved_by` — enforced by the validator.
- `confidentiality` defaults to **internal** (conservative).
- A record missing `buyer`, `question_text`, `answer_text` or `source_link` is
  **quarantined**, not written.
- `timebound: true` without an `expiry_date` is flagged in coverage.

## Enums

- sector: NHS, local_gov, central_gov, education, blue_light, other
- outcome: won, lost, shortlisted, non_compliant, withdrawn, unknown
- reuse_status: approved, needs_update, do_not_reuse
- confidentiality: public, internal, client_confidential, commercially_sensitive
- question_type: eligibility, technical, commercial, legal, social_value, pricing
- evidence_type: case_study, certificate, metric, CV, method, policy
