from __future__ import annotations

import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNBOOK_DIR = ROOT_DIR / "data" / "processed" / "runbooks"

REQUIRED_SECTIONS = [
    "## Metadata",
    "## Symptoms",
    "## Required Evidence",
    "## Verification Steps",
    "## Proposed Actions",
    "## Escalation",
    "## Safety Notes",
]

ALLOWED_CATEGORIES = {"network", "server_api", "database"}
ALLOWED_SERVICES = {
    "endpoint-device",
    "file-server",
    "dns-service",
    "vpn-gateway",
    "edge-gateway",
    "load-balancer",
    "proxy-service",
    "payment-api",
    "customer-api",
    "auth-service",
    "notification-api",
    "primary-db",
    "reporting-db",
    "customer-db",
    "backup-service",
}


def table_value(content: str, key: str) -> str:
    pattern = rf"^\| {re.escape(key)} \| (?P<value>.+?) \|$"
    match = re.search(pattern, content, flags=re.MULTILINE)
    return match.group("value").strip() if match else ""


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    content = path.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"{path.name}: missing section {section}")

    document_id = table_value(content, "document_id")
    if document_id != path.stem:
        errors.append(f"{path.name}: document_id does not match filename")

    service = table_value(content, "service")
    if service not in ALLOWED_SERVICES:
        errors.append(f"{path.name}: invalid service {service!r}")

    category = table_value(content, "category")
    if category not in ALLOWED_CATEGORIES:
        errors.append(f"{path.name}: invalid category {category!r}")

    if table_value(content, "source") != "synthetic":
        errors.append(f"{path.name}: source must be synthetic")

    if not table_value(content, "related_ticket_ids"):
        errors.append(f"{path.name}: missing related_ticket_ids")

    return errors


def validate() -> int:
    files = sorted(RUNBOOK_DIR.glob("RB-*.md"))
    errors: list[str] = []

    if len(files) < 30:
        errors.append(f"expected at least 30 runbooks, found {len(files)}")

    for path in files:
        errors.extend(validate_file(path))

    if errors:
        print("Runbook validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Runbook validation passed: {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
