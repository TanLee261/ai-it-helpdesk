# HTTP 500 errors on payment-api

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-001 |
| title | HTTP 500 errors on payment-api |
| service | payment-api |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00681, TCK-02320, TCK-02950, TCK-03402, TCK-03638 |

## Symptoms

- Symptoms may include payment requests fail with HTTP 500 and may affect checkout completion on `payment-api`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- trace/request IDs, payment-api error records, error rate and p95 latency, dependency health, and recent deployment/configuration changes.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Measure HTTP 500 rate by endpoint; correlate application records by trace ID; compare latency/error metrics; inspect database, identity, and payment-provider dependencies; review changes near the onset.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Use degraded mode or reduce traffic only under the incident procedure; roll back a release only when evidence links it to the failure and approval is recorded.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The backend service owner for application errors; the DBA for verified database evidence.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
