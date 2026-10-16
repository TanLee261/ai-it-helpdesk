# TLS certificate and handshake failures

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-NET-009 |
| title | TLS certificate and handshake failures |
| service | edge-gateway |
| category | network |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-04670, TCK-08040, TCK-00514, TCK-02354, TCK-03598 |

## Symptoms

- Symptoms may include clients report an expired certificate or TLS handshake failure on `edge-gateway`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- affected hostname, presented certificate chain and expiry, gateway/proxy TLS records, and deployment status.
- Relevant network path, endpoint, or gateway health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Inspect the certificate chain, hostname/SAN, issuer, and expiry; verify the certificate deployed on every relevant endpoint; correlate handshake errors with the deployment time.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Renew and deploy a valid certificate through the approved change process; roll back an invalid deployment only with authorization.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Security/Platform Operations for certificate issuance and deployment; the domain owner for hostname/SAN issues.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
