# Database service unavailable

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-DB-008 |
| title | Database service unavailable |
| service | primary-db |
| category | database |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | None identified |

## Symptoms

- Symptoms may include applications cannot connect and multiple dependent services may fail on `primary-db`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- database health/process status, application connection errors, host CPU/memory/disk/network metrics, and maintenance/failover events.
- Relevant database workload, connection, or storage layer health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Check database health and process state; test reachability from an authorized application host; inspect host resources; correlate with maintenance or failover; verify recovery from dependent services.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Follow the dedicated DBA failover/recovery procedure; do not restart a production database outside that procedure; notify affected service owners.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The DBA immediately for production unavailability; the incident commander for multi-service impact.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
