# Endpoint and printer troubleshooting

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-NET-001 |
| title | Endpoint and printer troubleshooting |
| service | endpoint-device |
| category | network |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00117, TCK-00219, TCK-00565, TCK-00754, TCK-01506 |

## Symptoms

- Symptoms may include endpoint devices or printers on `endpoint-device`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- device event records, driver or firmware versions, connectivity status, and print-queue state.
- Relevant network path, endpoint, or gateway health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Check device events and driver/firmware status; for printers, verify IP, DHCP/DNS, and queue state; for peripherals, inspect cables and hardware health.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Update a driver only when version-specific evidence supports it; use an approved temporary replacement for confirmed hardware failure.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Office IT for hardware; Network Services for DHCP, DNS, or reachability.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
