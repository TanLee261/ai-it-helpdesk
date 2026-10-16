# API rate-limit and HTTP 429 errors

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-010 |
| title | API rate-limit and HTTP 429 errors |
| service | customer-api |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-02365 |

## Symptoms

- Symptoms may include clients receive HTTP 429/quota errors or request volume increases sharply on `customer-api`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- request rate by client/endpoint, gateway 429 records, current quota/policy, and traffic-change history.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Identify the affected client and endpoint; compare request rate with the configured quota; inspect gateway records and policy changes; determine whether the traffic is expected or abusive.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Ask legitimate clients to use backoff; change quotas only with owner approval; apply security controls when evidence indicates abuse.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The API owner for quota changes; Security for suspected abusive traffic.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
