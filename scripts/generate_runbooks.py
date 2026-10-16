from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SPEC_FILE = ROOT_DIR / "data" / "specs" / "runbook_specs.yaml"
NORMALIZED_TICKETS = ROOT_DIR / "data" / "processed" / "tickets" / "normalized_tickets.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "processed" / "runbooks"


# English operational guidance keyed by stable document ID. The source specs
# retain the project taxonomy and matching keywords; these entries define the
# human-facing runbook content used for ingestion.
ENGLISH_GUIDANCE = {
    "RB-NET-001": ("Endpoint and printer troubleshooting", "endpoint devices or printers", "device event records, driver or firmware versions, connectivity status, and print-queue state", "Check device events and driver/firmware status; for printers, verify IP, DHCP/DNS, and queue state; for peripherals, inspect cables and hardware health.", "Update a driver only when version-specific evidence supports it; use an approved temporary replacement for confirmed hardware failure.", "Office IT for hardware; Network Services for DHCP, DNS, or reachability."),
    "RB-NET-002": ("Shared network drive access failures", "a user cannot access a shared folder or receives access-denied errors", "the affected path and user, file-server access audit records, group membership, and effective ACLs", "Confirm the exact path and user; inspect group membership, effective ACLs, and inheritance; correlate file-server denial records with the reported time.", "Correct group membership or ACLs only after authorization; ask the user to refresh their session after approved changes.", "Identity and Access Management for membership; Storage Services for file-server availability."),
    "RB-NET-003": ("DNS resolution failures", "a hostname fails to resolve while direct-IP connectivity may still work", "the hostname, client and server lookup results, resolver logs, DNS records, and TTL values", "Compare lookups from affected and unaffected clients and resolvers; inspect A/AAAA/CNAME records, TTL, and recent changes; distinguish DNS failure from general network failure.", "Correct an inaccurate record or use an approved secondary resolver; verify propagation before closing the incident.", "DNS/Network Operations for resolver issues; the service owner for application-managed records."),
    "RB-NET-004": ("VPN connection failures", "one user or a group cannot establish a remote VPN session", "client error text, redacted authentication records, gateway health, active-session capacity, certificate status, and MFA state", "Determine the affected user scope; correlate gateway authentication events; check account/MFA status, certificate validity, gateway health, and capacity.", "Repair an individual client configuration when isolated; change access or fail over a gateway only with the required approval.", "Identity and Access Management for account/MFA failures; Network Operations for gateway or certificate faults."),
    "RB-NET-005": ("Gateway timeout investigation", "requests through the edge gateway time out or return HTTP 504", "gateway request/trace IDs, upstream health checks, upstream latency, and timeout settings", "Compare gateway and upstream records for the same request and time window; inspect upstream health and p95/p99 latency; verify timeout settings and whether failures are endpoint-specific.", "Remove an unhealthy upstream from service only under the approved procedure; change timeout values only when measurements justify it.", "Platform/Network Operations for gateway faults; the upstream service owner for slow or unavailable backends."),
    "RB-NET-006": ("High packet-loss investigation", "connections are intermittent or packet loss is reported", "packet-loss measurements by host/subnet, ping/traceroute/MTR results, interface errors, and network-device records", "Measure from multiple points; identify the affected path and scope; inspect interface drops/errors and recent route changes; compare results across affected and control paths.", "Fail over traffic or reduce load only when measurements identify the affected path and an approved change is available.", "Network Operations for internal paths; the ISP/vendor for verified external-path loss."),
    "RB-NET-007": ("Firewall rule blocking traffic", "a service cannot reach an expected destination and traffic may be denied", "source/destination addresses, port/protocol, firewall deny records, and the relevant change record", "Define the expected flow; correlate deny/drop records with the exact flow and time; inspect rule order and recent changes; validate the narrowest required access in a test environment.", "Propose the minimum rule change and obtain security approval; roll back a recent rule only when evidence links it to the failure.", "Security and Network Operations for production rule changes; the service owner to confirm the required flow."),
    "RB-NET-008": ("Load-balancer health-check failures", "one or more backend targets are marked unhealthy or service capacity drops", "target health state, health-check path/port/status, per-target request and error metrics, and backend logs", "Identify affected targets and onset time; verify health-check response expectations; compare backend logs and per-target metrics; inspect path, port, timeout, and threshold configuration.", "Drain an unhealthy target only under the approved procedure; correct a health-check setting only after confirming the application endpoint contract.", "Platform Operations for load-balancer configuration; the service owner for failing application health endpoints."),
    "RB-NET-009": ("TLS certificate and handshake failures", "clients report an expired certificate or TLS handshake failure", "affected hostname, presented certificate chain and expiry, gateway/proxy TLS records, and deployment status", "Inspect the certificate chain, hostname/SAN, issuer, and expiry; verify the certificate deployed on every relevant endpoint; correlate handshake errors with the deployment time.", "Renew and deploy a valid certificate through the approved change process; roll back an invalid deployment only with authorization.", "Security/Platform Operations for certificate issuance and deployment; the domain owner for hostname/SAN issues."),
    "RB-NET-010": ("Proxy timeout investigation", "requests through a proxy time out for one or more upstreams", "proxy access/error records and request IDs, affected upstream, upstream latency, connection-pool state, and timeout settings", "Identify the affected endpoint and upstream; correlate proxy and upstream records; compare latency and error rates in the same window; inspect connection-pool and keepalive behavior.", "Tune timeouts only when upstream measurements support the change; prioritize correcting an unhealthy upstream and add monitoring for recurring timeouts.", "Platform Operations for proxy configuration; the upstream service owner for backend latency."),
    "RB-API-001": ("HTTP 500 errors on payment-api", "payment requests fail with HTTP 500 and may affect checkout completion", "trace/request IDs, payment-api error records, error rate and p95 latency, dependency health, and recent deployment/configuration changes", "Measure HTTP 500 rate by endpoint; correlate application records by trace ID; compare latency/error metrics; inspect database, identity, and payment-provider dependencies; review changes near the onset.", "Use degraded mode or reduce traffic only under the incident procedure; roll back a release only when evidence links it to the failure and approval is recorded.", "The backend service owner for application errors; the DBA for verified database evidence."),
    "RB-API-002": ("Elevated API p95 latency", "users report slow responses or p95/p99 latency rises", "latency by endpoint, request volume, error rate, slow-request traces, and dependency/resource metrics", "Identify affected endpoints; compare latency with a time-matched baseline; correlate traffic, errors, traces, CPU/memory, and dependency latency; determine whether impact is isolated or service-wide.", "Apply approved traffic controls if demand is abnormal; optimize the evidenced slow dependency/query; scale only after capacity evidence and approval.", "The API owner for endpoint-specific latency; Platform Operations for shared resource saturation."),
    "RB-API-003": ("Application crash-loop investigation", "service instances restart repeatedly and users see intermittent failures", "logs immediately before restarts, restart counts and exit codes, memory/CPU metrics, and recent release/configuration changes", "Establish restart onset and affected instances; inspect pre-restart exceptions and exit codes; compare resource limits and trends; correlate with recent deployments; check whether the issue affects one or all instances.", "Roll back a release only with a clear time/evidence link and approval; adjust resource limits only when resource-exhaustion evidence supports it.", "The backend team for application exceptions; Platform Operations for runtime or host failures."),
    "RB-API-004": ("Errors following an application release", "error rate rises or behavior changes after a deployment", "release/version and deployment time, before/after error metrics, logs by version, migration/configuration changes, and canary results", "Confirm the deployed version and onset; compare errors before and after release; isolate metrics/logs by version; inspect accompanying migrations/config changes; review canary and rollout scope.", "Pause rollout when the canary is failing; propose rollback only when release evidence supports causality and the release owner approves.", "The release owner for deployment decisions; the incident commander for broad production impact."),
    "RB-API-005": ("High application memory usage", "memory rises, approaches its limit, or instances are terminated for OOM", "memory trends by instance, OOM/heap/GC records, traffic volume, deployment time, and container limits", "Compare memory trends across instances and time; inspect OOM/heap/GC records; correlate with traffic and releases; check for sustained growth consistent with a leak; establish whether impact is isolated.", "Restart only with an impact plan and approval; increase limits as a temporary mitigation only when measurements justify it; open a follow-up investigation for repeatable growth.", "The backend team for suspected leaks; Platform Operations for runtime limits."),
    "RB-API-006": ("High API CPU utilization", "CPU remains elevated while latency rises or throughput falls", "CPU by host/instance, request rate and endpoint distribution, application logs/profiles, and deployment history", "Identify affected instances; compare CPU with request volume; find high-cost endpoints or code paths; correlate with releases; verify whether CPU falls when load shifts or capacity changes.", "Use approved scaling or rate controls when traffic/capacity evidence supports them; investigate abnormal code paths before treating scaling as the permanent fix.", "Platform Operations for capacity changes; the backend team for inefficient or looping code paths."),
    "RB-API-007": ("API request timeouts", "clients report request timeouts or traces show deadline/upstream timeout errors", "request/trace IDs, service and dependency logs, latency/error metrics, and timeout configuration changes", "Identify the endpoint and trace; follow the request across dependencies; determine which hop is slow; inspect recent timeout/configuration changes; distinguish local processing from upstream delay.", "Address the measured slow dependency; change timeout settings only with technical justification and approval; apply load shedding only through the incident procedure.", "The dependency owner for upstream delays; the backend lead for internal processing delays."),
    "RB-API-008": ("Authentication service failures", "users cannot sign in or tokens are rejected/not issued", "redacted auth records, login error rate, request IDs, identity-provider/MFA health, and account state", "Determine whether one account or many are affected; inspect redacted auth errors and codes; compare login-error metrics; check identity-provider/MFA health and account lock/authorization state.", "Guide an individual user through approved password/MFA recovery; treat broad service failures as an incident; revert configuration only with evidence and approval.", "Identity and Access Management for account/MFA issues; the authentication service owner for service-wide faults."),
    "RB-API-009": ("Unavailable service dependency", "an API returns HTTP 503 or reports that a dependency is unavailable", "caller and dependency records, dependency health checks, per-dependency error metrics, network/firewall changes, and fallback status", "Identify the failing dependency; compare its health and error rate with caller records; inspect network changes if connections are refused; verify whether fallback/degraded behavior is operating.", "Use an approved degraded mode or bounded retry policy; avoid retry amplification; escalate rather than repeatedly retrying an unavailable dependency.", "The dependency team for its service; the incident commander when multiple services are affected."),
    "RB-API-010": ("API rate-limit and HTTP 429 errors", "clients receive HTTP 429/quota errors or request volume increases sharply", "request rate by client/endpoint, gateway 429 records, current quota/policy, and traffic-change history", "Identify the affected client and endpoint; compare request rate with the configured quota; inspect gateway records and policy changes; determine whether the traffic is expected or abusive.", "Ask legitimate clients to use backoff; change quotas only with owner approval; apply security controls when evidence indicates abuse.", "The API owner for quota changes; Security for suspected abusive traffic."),
    "RB-DB-001": ("Database connection-pool exhaustion", "applications cannot obtain connections and database-related latency/timeouts rise", "application pool errors, pool utilization/active connections, database connection limits, traffic, and deployment/configuration changes", "Check pool utilization and active connections in the incident window; compare with configured and database limits; identify the services consuming connections; inspect for leaks and correlate with traffic/releases.", "Change pool or database limits only after DBA/backend review; reduce load through an approved mitigation; create a follow-up for confirmed connection leaks.", "The DBA for database limits; the application owner for pool behavior or leaks."),
    "RB-DB-002": ("Slow database query investigation", "reports or database-backed screens are slow and query duration rises", "slow-query records/query IDs, p95/p99 duration, execution plans, relevant indexes, and schema/data changes", "Identify the slow query and onset; inspect its execution plan for scans/expensive joins; review filter and sort columns/indexes; correlate with data growth or schema changes; validate candidate fixes outside production.", "Propose query or index changes only after DBA review and safe testing; use pagination where result volume is excessive.", "The DBA for query/index/schema changes; the report owner for report-generated queries."),
    "RB-DB-003": ("Database lock contention", "queries wait on locks, transactions block one another, or writes time out", "blocking/blocked sessions, lock-wait records, transaction duration, query text/IDs, and batch/deployment timing", "Identify blocking and blocked sessions; inspect transaction age and statements; correlate with batch jobs or releases; assess impact before terminating any session; confirm lock release and latency recovery.", "Contact the workload owner first; terminate a session only with DBA approval and impact review; reduce transaction duration in a reviewed change.", "The DBA for broad contention; the application owner for transactions creating long-held locks."),
    "RB-DB-004": ("Database replication lag", "replica reads are stale or replication-lag metrics increase", "lag by replica, replication error records, primary write timestamps, replica apply position, and replica resource metrics", "Measure lag on each replica; inspect replication/network/disk errors; correlate with write bursts and batch jobs; check replica CPU/disk capacity; confirm the replica catches up before closing.", "Route reads to a healthy replica only under the approved procedure; reduce a confirmed disruptive batch workload with owner approval.", "The DBA for persistent lag; the data/reporting team for affected reports."),
    "RB-DB-005": ("Low database disk space", "database storage approaches capacity or writes fail for lack of space", "disk/free-space metrics and growth rate, database write errors, tablespace/WAL/temp-file usage, and recent imports/jobs", "Measure free space and growth rate; identify the files/tablespaces growing fastest; inspect WAL/binlogs and temporary files; correlate with jobs/imports; verify recovered capacity after an approved change.", "Expand storage or remove eligible files only under retention and change-control policies; pause a confirmed space-intensive job with owner approval.", "The DBA for database storage; Infrastructure for volume capacity."),
    "RB-DB-006": ("Database deadlock investigation", "transactions are rolled back and logs report deadlock detection", "deadlock graph/logs, involved queries/tables, affected endpoints, transaction timing, and code/deployment changes", "Collect the deadlock graph; identify statements and lock order; correlate with the affected application path and recent changes; check whether bounded retries are safe and already configured.", "Propose consistent lock ordering, shorter transactions, or bounded retries after review; validate query/index changes safely.", "The backend team for application transaction logic; the DBA for deadlock-graph analysis."),
    "RB-DB-007": ("Database backup job failures", "backup/snapshot jobs fail or the latest restore point is missing", "backup job logs and status, latest restore point, target capacity, permissions/credential status, and retention policy", "Identify failed jobs and onset; classify the error (permissions, timeout, capacity, or target); verify the latest usable restore point and target capacity; confirm credentials through the approved secret process.", "Retry only after the cause is addressed and the approved procedure permits it; expand storage or rotate credentials through change/security controls.", "The DBA for critical database backups; Storage/Security for target capacity or credential failures."),
    "RB-DB-008": ("Database service unavailable", "applications cannot connect and multiple dependent services may fail", "database health/process status, application connection errors, host CPU/memory/disk/network metrics, and maintenance/failover events", "Check database health and process state; test reachability from an authorized application host; inspect host resources; correlate with maintenance or failover; verify recovery from dependent services.", "Follow the dedicated DBA failover/recovery procedure; do not restart a production database outside that procedure; notify affected service owners.", "The DBA immediately for production unavailability; the incident commander for multi-service impact."),
    "RB-DB-009": ("Missing or ineffective database index", "queries scan large tables and slow down as data volume grows", "execution plans, query predicates/joins/sorts, existing index definitions, table size, and before/after duration", "Capture the plan for the affected query; confirm whether a large scan is material; map WHERE/JOIN/ORDER BY columns to existing indexes; check for redundant or unsuitable indexes; test safely before production.", "Ask a DBA to review any index proposal; optimize the query when an index is not appropriate; measure duration after an approved change.", "The DBA for index design; the report owner for report query changes."),
    "RB-DB-010": ("Database connection timeouts", "applications time out while establishing database connections", "application connection errors, database CPU/connection counts, network latency, firewall/security-group records, and traffic/deployment timing", "Identify the caller and database endpoint; test authorized reachability; inspect database load and connection counts; correlate with firewall/network changes; compare the timeout window with traffic spikes and deployments.", "Correct a verified network block only with approval; tune timeouts/pools only when evidence supports it; reduce load or scale through the approved DBA procedure.", "The DBA for database saturation; Network Operations for blocked or high-latency paths."),
}


def load_specs() -> list[dict]:
    return json.loads(SPEC_FILE.read_text(encoding="utf-8"))


def load_tickets() -> list[dict]:
    with NORMALIZED_TICKETS.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def score_ticket(ticket: dict, spec: dict) -> int:
    haystack = " ".join(
        [
            ticket.get("title", ""),
            ticket.get("description", ""),
            ticket.get("service", ""),
            ticket.get("category", ""),
        ]
    ).lower()
    keywords = [keyword.lower() for keyword in spec.get("match_keywords", [])]
    return sum(1 for keyword in keywords if keyword in haystack)


def find_related_tickets(tickets: list[dict], spec: dict, limit: int = 5) -> list[str]:
    same_service = [ticket for ticket in tickets if ticket.get("service") == spec["service"]]
    candidates = same_service or tickets
    scored = [
        (score_ticket(ticket, spec), ticket.get("ticket_id", ""))
        for ticket in candidates
        if score_ticket(ticket, spec) > 0
    ]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [ticket_id for _, ticket_id in scored[:limit]]


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered_lines(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def escalation_lines(value: str | list[str]) -> str:
    if isinstance(value, list):
        return bullet_lines(value)
    return f"- {value}"


def render_runbook(spec: dict, related_ticket_ids: list[str]) -> str:
    title, failure_mode, evidence, checks, actions, escalation = ENGLISH_GUIDANCE[spec["document_id"]]
    tickets = ", ".join(related_ticket_ids) if related_ticket_ids else "None identified"
    category_context = {
        "network": "network path, endpoint, or gateway",
        "server_api": "application endpoint, runtime, or dependency",
        "database": "database workload, connection, or storage layer",
    }[spec["category"]]
    metadata = {
        "document_id": spec["document_id"],
        "title": title,
        "service": spec["service"],
        "category": spec["category"],
        "source": "synthetic",
        "access_scope": "it_internal",
        "version": "v1",
        "related_ticket_ids": tickets,
    }
    metadata_table = "\n".join(f"| {key} | {value} |" for key, value in metadata.items())

    return f"""# {title}

## Metadata

| Field | Value |
| --- | --- |
{metadata_table}

## Symptoms

- Symptoms may include {failure_mode} on `{spec["service"]}`.
- Impact may be isolated or broad; confirm the affected users, endpoints, and start time before assigning cause.
- Similar symptoms can have different causes; do not treat this runbook match as proof of root cause.

## Required Evidence

- The ticket, affected scope, timestamps, and request/trace identifiers where available.
- {evidence}.
- Relevant {category_context} health and change records for the same time window.
- A comparison with a healthy instance, endpoint, or baseline when available.

## Verification Steps

1. Confirm impact, affected scope, onset time, and the applicable time zone.
2. Collect the identifiers needed to correlate ticket, logs, metrics, and change records; redact credentials and personal data.
3. Inspect service logs for the incident window and correlate errors with the affected request or resource.
4. Compare relevant metrics with a healthy baseline and check whether the signal is service-wide or isolated.
5. {checks}
6. Review recent deployments, configuration changes, dependencies, and plausible alternative explanations.
7. After an approved mitigation, verify recovery using the same logs and metrics; record residual impact.

## Proposed Actions

1. Preserve evidence and communicate the confirmed impact and current uncertainty.
2. {actions}
3. Make production changes only through the applicable approval and change-control process; document the outcome.

## Escalation

- {escalation}
- Escalate to the incident commander when impact is broad, increasing, or affects a critical service.
- Include timestamps, affected scope, evidence IDs, actions taken, and remaining uncertainty in the handoff.

## Safety Notes

- This runbook is advisory only and must not execute production commands automatically.
- Any risky action requires technician approval before execution.
- Evidence from ticket, log, and metric sources must be cited before publishing RCA output.
"""


def generate() -> int:
    specs = load_specs()
    tickets = load_tickets()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expected_ids = {entry["document_id"] for entry in specs}
    if expected_ids != set(ENGLISH_GUIDANCE):
        raise ValueError("English runbook guidance IDs do not match runbook specs")

    for spec in specs:
        related_ticket_ids = find_related_tickets(tickets, spec)
        output_file = OUTPUT_DIR / f"{spec['document_id']}.md"
        output_file.write_text(render_runbook(spec, related_ticket_ids), encoding="utf-8")

    return len(specs)


if __name__ == "__main__":
    count = generate()
    print(f"Generated {count} runbooks -> {OUTPUT_DIR}")
