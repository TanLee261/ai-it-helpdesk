# Database connection timeouts

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-DB-010 |
| title | Database connection timeouts |
| service | customer-db |
| category | database |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-01722, TCK-04970, TCK-06599, TCK-09205 |

## Symptoms

- Symptoms may include applications time out while establishing database connections on `customer-db`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- application connection errors, database CPU/connection counts, network latency, firewall/security-group records, and traffic/deployment timing.
- Relevant database workload, connection, or storage layer health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Identify the caller and database endpoint; test authorized reachability; inspect database load and connection counts; correlate with firewall/network changes; compare the timeout window with traffic spikes and deployments.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Correct a verified network block only with approval; tune timeouts/pools only when evidence supports it; reduce load or scale through the approved DBA procedure.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The DBA for database saturation; Network Operations for blocked or high-latency paths.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
