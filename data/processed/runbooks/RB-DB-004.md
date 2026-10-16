# Database replication lag

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-DB-004 |
| title | Database replication lag |
| service | reporting-db |
| category | database |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | None identified |

## Symptoms

- Symptoms may include replica reads are stale or replication-lag metrics increase on `reporting-db`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- lag by replica, replication error records, primary write timestamps, replica apply position, and replica resource metrics.
- Relevant database workload, connection, or storage layer health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Measure lag on each replica; inspect replication/network/disk errors; correlate with write bursts and batch jobs; check replica CPU/disk capacity; confirm the replica catches up before closing.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Route reads to a healthy replica only under the approved procedure; reduce a confirmed disruptive batch workload with owner approval.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The DBA for persistent lag; the data/reporting team for affected reports.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
