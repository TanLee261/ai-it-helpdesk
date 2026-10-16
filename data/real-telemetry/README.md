# Real telemetry workspace

This directory is a local-only destination for authorized, read-only telemetry exports. `README.md`, `.gitignore`, and the sanitized mapping example are tracked; imported exports and `backend.log` are excluded from Git.

The local observability profile also writes the Helpdesk API process log to `backend.log`. Grafana Alloy mounts only this file read-only and forwards it to the local Loki instance.

Do not put credentials, unrestricted production logs, or personal data here. Export only the approved service and time window, redact sensitive fields before import, and follow your organization's retention and access-control policy. The importer writes normalized files here; the API reads them only when `ENABLE_REAL_TELEMETRY=true`.

Normalized logs use JSONL fields `log_id`, `timestamp` (UTC RFC 3339), `service`, `level`, `message`, `provenance`, `source_system`, and `source_record_id`.

Normalized metrics use CSV fields `metric_id`, `timestamp` (UTC RFC 3339), `service`, `metric_name`, `value`, `unit`, `provenance`, `source_system`, and `source_record_id`.

The service map is an explicit JSON object from source service/resource names to the project's canonical service names. Do not infer service names from ticket text.
