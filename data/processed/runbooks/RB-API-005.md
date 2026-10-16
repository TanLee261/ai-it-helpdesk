# High application memory usage

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-005 |
| title | High application memory usage |
| service | customer-api |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00989, TCK-01205, TCK-01812, TCK-06252, TCK-00033 |

## Symptoms

- Symptoms may include memory rises, approaches its limit, or instances are terminated for OOM on `customer-api`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- memory trends by instance, OOM/heap/GC records, traffic volume, deployment time, and container limits.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Compare memory trends across instances and time; inspect OOM/heap/GC records; correlate with traffic and releases; check for sustained growth consistent with a leak; establish whether impact is isolated.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Restart only with an impact plan and approval; increase limits as a temporary mitigation only when measurements justify it; open a follow-up investigation for repeatable growth.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The backend team for suspected leaks; Platform Operations for runtime limits.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
