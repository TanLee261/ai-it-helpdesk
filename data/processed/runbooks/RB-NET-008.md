# Load-balancer health-check failures

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-NET-008 |
| title | Load-balancer health-check failures |
| service | load-balancer |
| category | network |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-01763, TCK-02720, TCK-05593, TCK-09212 |

## Symptoms

- Symptoms may include one or more backend targets are marked unhealthy or service capacity drops on `load-balancer`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- target health state, health-check path/port/status, per-target request and error metrics, and backend logs.
- Relevant network path, endpoint, or gateway health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Identify affected targets and onset time; verify health-check response expectations; compare backend logs and per-target metrics; inspect path, port, timeout, and threshold configuration.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Drain an unhealthy target only under the approved procedure; correct a health-check setting only after confirming the application endpoint contract.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Platform Operations for load-balancer configuration; the service owner for failing application health endpoints.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
