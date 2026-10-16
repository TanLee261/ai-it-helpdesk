# Authentication service failures

## Metadata

| Field | Value |
| --- | --- |
| document_id | RB-API-008 |
| title | Authentication service failures |
| service | auth-service |
| category | server_api |
| source | synthetic |
| access_scope | it_internal |
| version | v1 |
| related_ticket_ids | TCK-00888, TCK-01561, TCK-05370, TCK-05411, TCK-05462 |

## Symptoms

- Symptoms may include users cannot sign in or tokens are rejected/not issued on `auth-service`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- redacted auth records, login error rate, request IDs, identity-provider/MFA health, and account state.
- Relevant application endpoint, runtime, or dependency health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. Determine whether one account or many are affected; inspect redacted auth errors and codes; compare login-error metrics; check identity-provider/MFA health and account lock/authorization state.
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. Guide an individual user through approved password/MFA recovery; treat broad service failures as an incident; revert configuration only with evidence and approval.
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- Identity and Access Management for account/MFA issues; the authentication service owner for service-wide faults.
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
