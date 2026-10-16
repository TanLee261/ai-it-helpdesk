# Elevated API p95 latency

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-002 |
| title | Elevated API p95 latency |
| service | customer-api |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00269, TCK-01209, TCK-01555, TCK-01602, TCK-01619 |

## Symptoms

- Symptoms may include users report slow responses or p95/p99 latency rises on `customer-api`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- latency by endpoint, request volume, error rate, slow-request traces, and dependency/resource metrics.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Identify affected endpoints; compare latency with a time-matched baseline; correlate traffic, errors, traces, CPU/memory, and dependency latency; determine whether impact is isolated or service-wide.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Apply approved traffic controls if demand is abnormal; optimize the evidenced slow dependency/query; scale only after capacity evidence and approval.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The API owner for endpoint-specific latency; Platform Operations for shared resource saturation.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
