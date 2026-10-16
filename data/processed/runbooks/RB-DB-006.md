# Database deadlock investigation

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-DB-006 |
| title | Database deadlock investigation |
| service | primary-db |
| category | database |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | None identified |

## Symptoms

- Symptoms may include transactions are rolled back and logs report deadlock detection on `primary-db`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- deadlock graph/logs, involved queries/tables, affected endpoints, transaction timing, and code/deployment changes.
- Relevant database workload, connection, or storage layer health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Collect the deadlock graph; identify statements and lock order; correlate with the affected application path and recent changes; check whether bounded retries are safe and already configured.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Propose consistent lock ordering, shorter transactions, or bounded retries after review; validate query/index changes safely.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The backend team for application transaction logic; the DBA for deadlock-graph analysis.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
