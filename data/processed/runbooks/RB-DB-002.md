# Slow database query investigation

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-DB-002 |
| title | Slow database query investigation |
| service | reporting-db |
| category | database |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00005, TCK-00011, TCK-00015, TCK-00023, TCK-00073 |

## Symptoms

- Symptoms may include reports or database-backed screens are slow and query duration rises on `reporting-db`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- slow-query records/query IDs, p95/p99 duration, execution plans, relevant indexes, and schema/data changes.
- Relevant database workload, connection, or storage layer health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Identify the slow query and onset; inspect its execution plan for scans/expensive joins; review filter and sort columns/indexes; correlate with data growth or schema changes; validate candidate fixes outside production.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Propose query or index changes only after DBA review and safe testing; use pagination where result volume is excessive.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The DBA for query/index/schema changes; the report owner for report-generated queries.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
