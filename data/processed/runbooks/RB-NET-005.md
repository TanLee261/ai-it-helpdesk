# Gateway timeout investigation

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-NET-005 |
| title | Gateway timeout investigation |
| service | edge-gateway |
| category | network |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-01722, TCK-04842, TCK-04970, TCK-05574, TCK-06131 |

## Symptoms

- Symptoms may include requests through the edge gateway time out or return HTTP 504 on `edge-gateway`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- gateway request/trace IDs, upstream health checks, upstream latency, and timeout settings.
- Relevant network path, endpoint, or gateway health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Compare gateway and upstream records for the same request and time window; inspect upstream health and p95/p99 latency; verify timeout settings and whether failures are endpoint-specific.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Remove an unhealthy upstream from service only under the approved procedure; change timeout values only when measurements justify it.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Platform/Network Operations for gateway faults; the upstream service owner for slow or unavailable backends.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
