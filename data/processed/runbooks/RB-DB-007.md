# Database backup job failures

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-DB-007 |
| title | Database backup job failures |
| service | backup-service |
| category | database |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00547, TCK-00995, TCK-01018, TCK-01037, TCK-01264 |

## Symptoms

- Symptoms may include backup/snapshot jobs fail or the latest restore point is missing on `backup-service`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- backup job logs and status, latest restore point, target capacity, permissions/credential status, and retention policy.
- Relevant database workload, connection, or storage layer health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Identify failed jobs and onset; classify the error (permissions, timeout, capacity, or target); verify the latest usable restore point and target capacity; confirm credentials through the approved secret process.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Retry only after the cause is addressed and the approved procedure permits it; expand storage or rotate credentials through change/security controls.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The DBA for critical database backups; Storage/Security for target capacity or credential failures.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
