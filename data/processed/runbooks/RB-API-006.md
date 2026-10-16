# High API CPU utilization

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-006 |
| title | High API CPU utilization |
| service | customer-api |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-02595 |

## Symptoms

- Symptoms may include CPU remains elevated while latency rises or throughput falls on `customer-api`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- CPU by host/instance, request rate and endpoint distribution, application logs/profiles, and deployment history.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Identify affected instances; compare CPU with request volume; find high-cost endpoints or code paths; correlate with releases; verify whether CPU falls when load shifts or capacity changes.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Use approved scaling or rate controls when traffic/capacity evidence supports them; investigate abnormal code paths before treating scaling as the permanent fix.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Platform Operations for capacity changes; the backend team for inefficient or looping code paths.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
