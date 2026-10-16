# DNS resolution failures

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-NET-003 |
| title | DNS resolution failures |
| service | dns-service |
| category | network |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-01240, TCK-01442, TCK-02789, TCK-07899, TCK-09289 |

## Symptoms

- Symptoms may include a hostname fails to resolve while direct-IP connectivity may still work on `dns-service`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- the hostname, client and server lookup results, resolver logs, DNS records, and TTL values.
- Relevant network path, endpoint, or gateway health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Compare lookups from affected and unaffected clients and resolvers; inspect A/AAAA/CNAME records, TTL, and recent changes; distinguish DNS failure from general network failure.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Correct an inaccurate record or use an approved secondary resolver; verify propagation before closing the incident.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- DNS/Network Operations for resolver issues; the service owner for application-managed records.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
