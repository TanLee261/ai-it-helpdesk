# Errors following an application release

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-004 |
| title | Errors following an application release |
| service | customer-api |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-01013, TCK-00836, TCK-01453, TCK-01516, TCK-02262 |

## Symptoms

- Symptoms may include error rate rises or behavior changes after a deployment on `customer-api`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- release/version and deployment time, before/after error metrics, logs by version, migration/configuration changes, and canary results.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Confirm the deployed version and onset; compare errors before and after release; isolate metrics/logs by version; inspect accompanying migrations/config changes; review canary and rollout scope.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Pause rollout when the canary is failing; propose rollback only when release evidence supports causality and the release owner approves.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- The release owner for deployment decisions; the incident commander for broad production impact.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
