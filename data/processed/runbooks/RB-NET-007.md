# Firewall rule blocking traffic

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-NET-007 |
| title | Firewall rule blocking traffic |
| service | edge-gateway |
| category | network |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-01210, TCK-00037, TCK-00314, TCK-00367, TCK-00408 |

## Symptoms

- Symptoms may include a service cannot reach an expected destination and traffic may be denied on `edge-gateway`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- source/destination addresses, port/protocol, firewall deny records, and the relevant change record.
- Relevant network path, endpoint, or gateway health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Define the expected flow; correlate deny/drop records with the exact flow and time; inspect rule order and recent changes; validate the narrowest required access in a test environment.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Propose the minimum rule change and obtain security approval; roll back a recent rule only when evidence links it to the failure.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Security and Network Operations for production rule changes; the service owner to confirm the required flow.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
