# Missing or ineffective database index

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-DB-009 |
| title | Missing or ineffective database index |
| service | reporting-db |
| category | database |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00059, TCK-05953 |

## Symptoms

- Symptoms may include queries scan large tables and slow down as data volume grows on `reporting-db`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- execution plans, query predicates/joins/sorts, existing index definitions, table size, and before/after duration.
- Relevant database workload, connection, or storage layer health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Capture the plan for the affected query; confirm whether a large scan is material; map WHERE/JOIN/ORDER BY columns to existing indexes; check for redundant or unsuitable indexes; test safely before production.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Ask a DBA to review any index proposal; optimize the query when an index is not appropriate; measure duration after an approved change.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The DBA for index design; the report owner for report query changes.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
