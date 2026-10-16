from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw" / "tickets"
MAIN_TICKETS = RAW_DIR / "Final_Balanced_10000_IT_Support_Tickets.csv"
ERROR_DESCRIPTIONS = RAW_DIR / "dataset.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "processed" / "tickets"
OUTPUT_TICKETS = OUTPUT_DIR / "normalized_tickets.csv"
OUTPUT_DESCRIPTIONS = OUTPUT_DIR / "error_descriptions.csv"


PRIORITY_MAP = {
    "critical": "p1",
    "high": "p2",
    "medium": "p3",
    "low": "p4",
}


SERVICE_RULES = [
    ("dns-service", ["dns", "domain", "resolver"]),
    ("vpn-gateway", ["vpn", "remote access"]),
    ("file-server", ["network drive", "shared drive", "file server"]),
    ("endpoint-device", ["printer", "print", "laptop", "monitor", "keyboard", "mouse", "touchscreen"]),
    ("proxy-service", ["proxy"]),
    ("edge-gateway", ["internet slow", "slow internet", "network connectivity", "wifi", "connection"]),
    ("auth-service", ["password", "login", "mfa", "account", "access request", "account unlock", "account locked"]),
    ("notification-api", ["email", "notification", "mail"]),
    ("primary-db", ["data loss", "database", "db", "storage", "record"]),
    ("reporting-db", ["performance", "slow query", "report", "analytics"]),
    ("backup-service", ["backup", "restore"]),
    ("customer-api", ["application error", "software support", "software install", "installation", "configuration"]),
    ("customer-api", ["software", "application", "app"]),
    ("edge-gateway", ["network"]),
    ("endpoint-device", ["hardware malfunction", "hardware failure", "hardware"]),
]


CATEGORY_BY_SERVICE = {
    "endpoint-device": "network",
    "file-server": "network",
    "dns-service": "network",
    "vpn-gateway": "network",
    "edge-gateway": "network",
    "load-balancer": "network",
    "proxy-service": "network",
    "payment-api": "server_api",
    "customer-api": "server_api",
    "auth-service": "server_api",
    "notification-api": "server_api",
    "primary-db": "database",
    "reporting-db": "database",
    "customer-db": "database",
    "backup-service": "database",
}


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def normalize_priority(value: str) -> str:
    return PRIORITY_MAP.get(value.strip().lower(), "p3")


def impact_urgency(priority: str) -> tuple[str, str]:
    if priority == "p1":
        return "high", "high"
    if priority == "p2":
        return "high", "medium"
    if priority == "p3":
        return "medium", "medium"
    return "low", "low"


def infer_service(text: str, raw_category: str, sub_category: str, assigned_team: str) -> str:
    haystack = f"{text} {raw_category} {sub_category} {assigned_team}".lower()
    for service, keywords in SERVICE_RULES:
        if any(keyword in haystack for keyword in keywords):
            return service

    category = raw_category.strip().lower()
    if category == "access":
        return "auth-service"
    if category == "network":
        return "edge-gateway"
    if category == "software":
        return "customer-api"
    if category == "hardware":
        return "endpoint-device"
    return "customer-api"


def make_title(text: str, sub_category: str) -> str:
    clean = " ".join(text.strip().split())
    if not clean:
        return sub_category or "IT support request"
    if len(clean) <= 72:
        return clean
    return f"{clean[:69].rstrip()}..."


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="", errors="replace") as handle:
        return list(csv.DictReader(handle))


def normalize_main_tickets() -> int:
    rows = read_csv(MAIN_TICKETS)
    fieldnames = [
        "ticket_id",
        "source_ticket_id",
        "title",
        "description",
        "service",
        "category",
        "raw_category",
        "sub_category",
        "priority",
        "impact",
        "urgency",
        "assigned_team",
        "auto_resolve",
        "status",
        "created_at",
        "requester_email_redacted",
        "verified_root_cause",
        "resolution",
        "source",
    ]

    with OUTPUT_TICKETS.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in enumerate(rows, start=1):
            description = row.get("user_input_text", "").strip()
            raw_category = row.get("category", "").strip()
            sub_category = row.get("sub_category", "").strip()
            assigned_team = row.get("assigned_team", "").strip()
            service = infer_service(description, raw_category, sub_category, assigned_team)
            category = CATEGORY_BY_SERVICE[service]
            priority = normalize_priority(row.get("Priority", row.get("priority", "")))
            impact, urgency = impact_urgency(priority)

            writer.writerow(
                {
                    "ticket_id": f"TCK-{index:05d}",
                    "source_ticket_id": stable_hash(f"main:{index}:{description}"),
                    "title": make_title(description, sub_category),
                    "description": description,
                    "service": service,
                    "category": category,
                    "raw_category": raw_category,
                    "sub_category": sub_category,
                    "priority": priority,
                    "impact": impact,
                    "urgency": urgency,
                    "assigned_team": assigned_team,
                    "auto_resolve": row.get("auto_resolve", "").strip().upper(),
                    "status": "resolved",
                    "created_at": "",
                    "requester_email_redacted": "redacted",
                    "verified_root_cause": "",
                    "resolution": "",
                    "source": "HELPDESK.AI/Final_Balanced_10000_IT_Support_Tickets.csv",
                }
            )

    return len(rows)


def normalize_error_descriptions() -> int:
    rows = read_csv(ERROR_DESCRIPTIONS)
    fieldnames = [
        "description_id",
        "description",
        "service",
        "category",
        "raw_category",
        "sub_category",
        "priority",
        "assigned_team",
        "auto_resolve",
        "source",
    ]

    with OUTPUT_DESCRIPTIONS.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in enumerate(rows, start=1):
            description = row.get("user_input_text", "").strip()
            raw_category = row.get("category", "").strip()
            sub_category = row.get("sub_category", "").strip()
            assigned_team = row.get("assigned_team", "").strip()
            service = infer_service(description, raw_category, sub_category, assigned_team)

            writer.writerow(
                {
                    "description_id": f"DESC-{index:05d}",
                    "description": description,
                    "service": service,
                    "category": CATEGORY_BY_SERVICE[service],
                    "raw_category": raw_category,
                    "sub_category": sub_category,
                    "priority": normalize_priority(row.get("priority", row.get("Priority", ""))),
                    "assigned_team": assigned_team,
                    "auto_resolve": row.get("auto_resolve", "").strip().upper(),
                    "source": "HELPDESK.AI/dataset.csv",
                }
            )

    return len(rows)


def normalize() -> tuple[int, int]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ticket_count = normalize_main_tickets()
    description_count = normalize_error_descriptions()
    return ticket_count, description_count


if __name__ == "__main__":
    tickets, descriptions = normalize()
    print(f"Normalized {tickets} main tickets -> {OUTPUT_TICKETS}")
    print(f"Normalized {descriptions} error descriptions -> {OUTPUT_DESCRIPTIONS}")
