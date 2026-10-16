# VPN connection failures

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-NET-004 |
| title | VPN connection failures |
| service | vpn-gateway |
| category | network |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00013, TCK-00157, TCK-00279, TCK-00364, TCK-00382 |

## Symptoms

- Symptoms may include one user or a group cannot establish a remote VPN session on `vpn-gateway`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- client error text, redacted authentication records, gateway health, active-session capacity, certificate status, and MFA state.
- Relevant network path, endpoint, or gateway health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Determine the affected user scope; correlate gateway authentication events; check account/MFA status, certificate validity, gateway health, and capacity.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Repair an individual client configuration when isolated; change access or fail over a gateway only with the required approval.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Identity and Access Management for account/MFA failures; Network Operations for gateway or certificate faults.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
