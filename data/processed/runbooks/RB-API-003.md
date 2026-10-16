# Application crash-loop investigation

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-003 |
| title | Application crash-loop investigation |
| service | customer-api |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-01567, TCK-02901, TCK-03013, TCK-06392, TCK-00358 |

## Symptoms

- Symptoms may include service instances restart repeatedly and users see intermittent failures on `customer-api`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- logs immediately before restarts, restart counts and exit codes, memory/CPU metrics, and recent release/configuration changes.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Establish restart onset and affected instances; inspect pre-restart exceptions and exit codes; compare resource limits and trends; correlate with recent deployments; check whether the issue affects one or all instances.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Roll back a release only with a clear time/evidence link and approval; adjust resource limits only when resource-exhaustion evidence supports it.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The backend team for application exceptions; Platform Operations for runtime or host failures.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
