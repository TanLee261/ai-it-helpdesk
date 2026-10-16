from __future__ import annotations

import csv
import json
from collections.abc import Generator
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.analysis.log_filter import load_logs, load_metrics
from app.analysis.schema import Evidence, RcaDraft
from app.db.base import Base
from app.db.models import Ticket
from app.db.session import get_db
from app.security.rbac import Actor, Role, get_actor
from app.ingestion.enricher import IngestDocument
from app.ingestion.pipeline import ingest_documents
from app.main import app


engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SessionLocal = sessionmaker(bind=engine)
client = TestClient(app)
PAYLOAD = {
    "ticket_id": "TCK-001",
    "window_start": "2026-09-01T11:00:00Z",
    "window_end": "2026-09-01T11:15:00Z",
}


def db_override() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_actor] = lambda: Actor("test-tech", Role.TECHNICIAN, 1)
    with SessionLocal() as db:
        db.add(Ticket(
            ticket_id="TCK-001", title="Gateway slow", description="Users see timeout",
            service="edge-gateway", category="network", priority="p2", impact="high",
            urgency="high", status="resolved", verified_root_cause="SECRET ANSWER",
            resolution="SECRET RESOLUTION", auto_resolve=False,
        ))
        db.commit()
        ingest_documents(db, [
            IngestDocument(
                document_id="KT-TCK-001", title="Current ticket", source_type="historical_ticket",
                source="test", service="edge-gateway", category="network", version="v1",
                access_scope="it_internal", content="Gateway slow SECRET ANSWER",
            ),
            IngestDocument(
                document_id="RB-NET-001", title="Gateway runbook", source_type="runbook",
                source="test", service="edge-gateway", category="network", version="v1",
                access_scope="it_internal", content="Check gateway timeout and latency",
            ),
        ])


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_insufficient_evidence_skips_llm(monkeypatch) -> None:
    monkeypatch.setattr("app.analysis.service.load_logs", lambda *args, **kwargs: [])
    monkeypatch.setattr("app.analysis.service.load_metrics", lambda *args, **kwargs: [])
    monkeypatch.setattr("app.analysis.service.get_generator", lambda: (_ for _ in ()).throw(AssertionError("LLM called")))
    response = client.post("/api/ai/analyze", json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_evidence"
    assert body["probable_root_cause"] is None
    assert body["review_required"] is True
    assert all(item["evidence_id"] != "KT-TCK-001-C001" for item in body["evidence"])
    assert "SECRET ANSWER" not in str(body)


def test_grounded_report_with_valid_ids(monkeypatch) -> None:
    log = Evidence(evidence_id="LOG-1", source_type="log", service="edge-gateway", content="Timeouts increased")
    metric = Evidence(evidence_id="MET-1", source_type="metric", service="edge-gateway", content="latency_p95_ms=4200 ms")
    monkeypatch.setattr("app.analysis.service.load_logs", lambda *args, **kwargs: [log])
    monkeypatch.setattr("app.analysis.service.load_metrics", lambda *args, **kwargs: [metric])

    class FakeGenerator:
        model = "fake-model"

        def generate(self, system_prompt, user_prompt):
            assert "SECRET ANSWER" not in user_prompt
            assert "LOG-1" in user_prompt
            return RcaDraft(
                status="grounded", observed_facts=[{"fact": "Timeouts increased", "evidence_ids": ["LOG-1"]}],
                hypotheses=[{"cause": "Gateway congestion", "supporting_evidence_ids": ["LOG-1", "MET-1"]}],
                probable_root_cause="Gateway congestion", root_cause_evidence_ids=["LOG-1", "MET-1"],
                confidence="medium", missing_evidence=["Upstream trace"],
                verification_steps=[{"step": "Inspect upstream latency", "evidence_ids": ["MET-1"]}],
                proposed_actions=["Ask technician to review gateway capacity"],
            )

    monkeypatch.setattr("app.analysis.service.get_generator", lambda: FakeGenerator())
    response = client.post("/api/ai/analyze", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json()["root_cause_evidence_ids"] == ["LOG-1", "MET-1"]
    assert response.json()["model"] == "fake-model"


def test_rejects_fabricated_citation(monkeypatch) -> None:
    monkeypatch.setattr("app.analysis.service.load_logs", lambda *args, **kwargs: [
        Evidence(evidence_id="LOG-1", source_type="log", service="edge-gateway", content="Timeouts increased")
    ])
    monkeypatch.setattr("app.analysis.service.load_metrics", lambda *args, **kwargs: [])

    class FakeGenerator:
        model = "fake-model"

        def generate(self, system_prompt, user_prompt):
            return RcaDraft(
                status="grounded", observed_facts=[], hypotheses=[],
                probable_root_cause="Invented", root_cause_evidence_ids=["LOG-DOES-NOT-EXIST"],
                confidence="high", missing_evidence=[], verification_steps=[], proposed_actions=[],
            )

    monkeypatch.setattr("app.analysis.service.get_generator", lambda: FakeGenerator())
    response = client.post("/api/ai/analyze", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_evidence"
    assert response.json()["probable_root_cause"] is None
    assert response.json()["review_required"] is True


def test_runbook_only_observation_is_discarded(monkeypatch) -> None:
    monkeypatch.setattr("app.analysis.service.load_logs", lambda *args, **kwargs: [
        Evidence(evidence_id="LOG-1", source_type="log", service="edge-gateway", content="Timeouts increased")
    ])
    monkeypatch.setattr("app.analysis.service.load_metrics", lambda *args, **kwargs: [])

    class FakeGenerator:
        model = "fake-model"

        def generate(self, system_prompt, user_prompt):
            return RcaDraft(
                status="grounded",
                observed_facts=[
                    {"fact": "Runbook says check gateway", "evidence_ids": ["RB-NET-001-C001"]},
                    {"fact": "Timeouts increased", "evidence_ids": ["LOG-1"]},
                ],
                hypotheses=[], probable_root_cause="Possible gateway issue",
                root_cause_evidence_ids=["LOG-1"], confidence="low",
                missing_evidence=[], verification_steps=[], proposed_actions=[],
            )

    monkeypatch.setattr("app.analysis.service.get_generator", lambda: FakeGenerator())
    response = client.post("/api/ai/analyze", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json()["status"] == "grounded"
    assert [fact["evidence_ids"] for fact in response.json()["observed_facts"]] == [["LOG-1"]]


def test_log_and_metric_filter_by_service_time_and_label_leak(tmp_path) -> None:
    log_path = tmp_path / "logs.jsonl"
    rows = [
        {"log_id": "L-1", "timestamp": "2026-09-01T11:01:00Z", "service": "edge-gateway", "level": "WARN", "message": "Timeout increased"},
        {"log_id": "L-2", "timestamp": "2026-09-01T11:02:00Z", "service": "edge-gateway", "level": "ERROR", "message": "root cause candidate: answer"},
        {"log_id": "L-3", "timestamp": "2026-09-01T11:01:00Z", "service": "other", "level": "WARN", "message": "Other service"},
    ]
    log_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    metric_path = tmp_path / "metrics.csv"
    with metric_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["metric_id", "timestamp", "service", "metric_name", "value", "unit", "is_anomaly", "phase"])
        writer.writeheader()
        writer.writerow({"metric_id": "M-1", "timestamp": "2026-09-01T11:03:00Z", "service": "edge-gateway", "metric_name": "latency", "value": "4200", "unit": "ms", "is_anomaly": "true", "phase": "peak"})
        writer.writerow({"metric_id": "M-2", "timestamp": "2026-09-01T10:00:00Z", "service": "edge-gateway", "metric_name": "latency", "value": "200", "unit": "ms", "is_anomaly": "false", "phase": "baseline"})
    start = datetime(2026, 9, 1, 11, tzinfo=timezone.utc)
    end = datetime(2026, 9, 1, 11, 15, tzinfo=timezone.utc)
    assert [item.evidence_id for item in load_logs("edge-gateway", start, end, path=log_path)] == ["L-1"]
    metrics = load_metrics("edge-gateway", start, end, path=metric_path)
    assert [item.evidence_id for item in metrics] == ["M-1"]
    assert "peak" not in metrics[0].content


def test_default_loader_reads_ticket_informed_synthetic_telemetry(tmp_path, monkeypatch) -> None:
    start = datetime(2026, 10, 16, 3, tzinfo=timezone.utc)
    end = start.replace(minute=15)
    log_path = tmp_path / "synthetic_logs.jsonl"
    log_path.write_text(json.dumps({
        "log_id": "SYNLOG-TCK-00006-01", "timestamp": "2026-10-16T03:00:00Z",
        "service": "edge-gateway", "level": "WARN", "incident_id": "SYN-TCK-00006",
        "ticket_id": "TCK-00006", "provenance": "synthetic_ticket_informed", "message": "Packet delivery degraded",
    }) + "\n", encoding="utf-8")
    metric_path = tmp_path / "synthetic_metrics.csv"
    with metric_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "metric_id", "timestamp", "service", "metric_name", "value", "unit", "ticket_id", "provenance",
        ])
        writer.writeheader()
        writer.writerow({
            "metric_id": "SYNMET-TCK-00006-01-02", "timestamp": "2026-10-16T03:04:00Z",
            "service": "edge-gateway", "metric_name": "packet_loss_percent", "value": "8.4",
            "unit": "percent", "ticket_id": "TCK-00006", "provenance": "synthetic_ticket_informed",
        })
    monkeypatch.setattr("app.analysis.log_filter.LOG_PATH", tmp_path / "no_legacy_logs.jsonl")
    monkeypatch.setattr("app.analysis.log_filter.METRIC_PATH", tmp_path / "no_legacy_metrics.csv")
    monkeypatch.setattr("app.analysis.log_filter.SYNTHETIC_LOG_PATH", log_path)
    monkeypatch.setattr("app.analysis.log_filter.SYNTHETIC_METRIC_PATH", metric_path)

    logs = load_logs("edge-gateway", start, end, ticket_id="TCK-00006")
    metrics = load_metrics("edge-gateway", start, end, ticket_id="TCK-00006")
    assert logs[0].evidence_id == "SYNLOG-TCK-00006-01"
    assert "SYNTHETIC DEMO DATA" in logs[0].content
    assert metrics[0].evidence_id == "SYNMET-TCK-00006-01-02"
    assert "SYNTHETIC DEMO DATA" in metrics[0].content


def test_default_loader_does_not_mix_synthetic_evidence_between_tickets(tmp_path, monkeypatch) -> None:
    start = datetime(2026, 10, 16, 3, tzinfo=timezone.utc)
    end = start.replace(minute=15)
    log_path = tmp_path / "synthetic_logs.jsonl"
    rows = [
        {"log_id": f"SYNLOG-{ticket_id}", "timestamp": "2026-10-16T03:02:00Z",
         "service": "edge-gateway", "level": "WARN", "incident_id": f"SYN-{ticket_id}",
         "ticket_id": ticket_id, "provenance": "synthetic_ticket_informed", "message": "Connectivity degraded"}
        for ticket_id in ("TCK-00006", "TCK-00063")
    ]
    log_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    metric_path = tmp_path / "synthetic_metrics.csv"
    with metric_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "metric_id", "timestamp", "service", "metric_name", "value", "unit", "ticket_id", "provenance",
        ])
        writer.writeheader()
        for ticket_id in ("TCK-00006", "TCK-00063"):
            writer.writerow({"metric_id": f"SYNMET-{ticket_id}", "timestamp": "2026-10-16T03:04:00Z",
                "service": "edge-gateway", "metric_name": "packet_loss_percent", "value": "8.4",
                "unit": "percent", "ticket_id": ticket_id, "provenance": "synthetic_ticket_informed"})
    monkeypatch.setattr("app.analysis.log_filter.LOG_PATH", tmp_path / "no_legacy_logs.jsonl")
    monkeypatch.setattr("app.analysis.log_filter.METRIC_PATH", tmp_path / "no_legacy_metrics.csv")
    monkeypatch.setattr("app.analysis.log_filter.SYNTHETIC_LOG_PATH", log_path)
    monkeypatch.setattr("app.analysis.log_filter.SYNTHETIC_METRIC_PATH", metric_path)

    logs = load_logs("edge-gateway", start, end, ticket_id="TCK-00006")
    metrics = load_metrics("edge-gateway", start, end, ticket_id="TCK-00006")
    assert [item.evidence_id for item in logs] == ["SYNLOG-TCK-00006"]
    assert [item.evidence_id for item in metrics] == ["SYNMET-TCK-00006"]


def test_real_telemetry_is_opt_in_and_marked_as_operational_export(tmp_path, monkeypatch) -> None:
    start = datetime(2026, 10, 16, 3, tzinfo=timezone.utc)
    end = start.replace(minute=15)
    logs_path = tmp_path / "real_logs.jsonl"
    logs_path.write_text(json.dumps({
        "log_id": "LOG-real-1", "timestamp": "2026-10-16T03:04:00Z", "service": "edge-gateway",
        "level": "ERROR", "message": "upstream timeout", "provenance": "production_export",
    }) + "\n", encoding="utf-8")
    metrics_path = tmp_path / "real_metrics.csv"
    with metrics_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["metric_id", "timestamp", "service", "metric_name", "value", "unit", "provenance"])
        writer.writeheader()
        writer.writerow({"metric_id": "MET-real-1", "timestamp": "2026-10-16T03:05:00Z", "service": "edge-gateway",
                         "metric_name": "latency_p95", "value": "900", "unit": "ms", "provenance": "production_export"})
    monkeypatch.setattr("app.analysis.log_filter.LOG_PATH", tmp_path / "missing_logs.jsonl")
    monkeypatch.setattr("app.analysis.log_filter.METRIC_PATH", tmp_path / "missing_metrics.csv")
    monkeypatch.setattr("app.analysis.log_filter.SYNTHETIC_LOG_PATH", tmp_path / "missing_synthetic_logs.jsonl")
    monkeypatch.setattr("app.analysis.log_filter.SYNTHETIC_METRIC_PATH", tmp_path / "missing_synthetic_metrics.csv")
    monkeypatch.setattr("app.analysis.log_filter.REAL_LOG_PATH", logs_path)
    monkeypatch.setattr("app.analysis.log_filter.REAL_METRIC_PATH", metrics_path)
    monkeypatch.delenv("ENABLE_REAL_TELEMETRY", raising=False)
    assert load_logs("edge-gateway", start, end) == []
    assert load_metrics("edge-gateway", start, end) == []
    monkeypatch.setenv("ENABLE_REAL_TELEMETRY", "true")
    logs = load_logs("edge-gateway", start, end)
    metrics = load_metrics("edge-gateway", start, end)
    assert logs[0].evidence_id == "LOG-real-1"
    assert "READ-ONLY OPERATIONAL EXPORT" in logs[0].content
    assert metrics[0].evidence_id == "MET-real-1"
    assert "READ-ONLY OPERATIONAL EXPORT" in metrics[0].content


def test_real_telemetry_importer_requires_timezone_and_maps_service(tmp_path) -> None:
    import importlib.util
    from pathlib import Path
    from types import SimpleNamespace
    import pytest

    script = Path(__file__).resolve().parents[3] / "scripts/import_real_telemetry.py"
    spec = importlib.util.spec_from_file_location("import_real_telemetry", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.parse_timestamp("2026-10-16T10:00:00+07:00") == "2026-10-16T03:00:00Z"
    with pytest.raises(ValueError, match="include timezone"):
        module.parse_timestamp("2026-10-16T10:00:00")
    assert module.service_name("payments-prod", {"payments-prod": "payment-api"}, tmp_path / "export.csv", 2) == "payment-api"
    with pytest.raises(ValueError, match="unmapped service"):
        module.service_name("unknown", {}, tmp_path / "export.csv", 2)

    logs_file = tmp_path / "source-logs.csv"
    logs_file.write_text(
        "timestamp,service,event_id,message,level\n"
        '2026-10-16T10:00:00+07:00,payments-prod,e-1,"timeout user@example.com token=abc123",ERROR\n',
        encoding="utf-8",
    )
    metrics_file = tmp_path / "source-metrics.csv"
    metrics_file.write_text(
        "timestamp,service,event_id,metric_name,value,unit\n"
        "2026-10-16T10:01:00+07:00,payments-prod,m-1,latency_p95,850,ms\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "normalized"
    output_dir.mkdir()
    args = SimpleNamespace(
        logs=logs_file, metrics=metrics_file, output_dir=output_dir, source_system="test-export",
        timestamp_field="timestamp", service_field="service", record_id_field="event_id",
        message_field="message", level_field="level", metric_name_field="metric_name",
        value_field="value", unit_field="unit",
    )
    assert module.normalize_logs(args, {"payments-prod": "payment-api"}) == 1
    assert module.normalize_metrics(args, {"payments-prod": "payment-api"}) == 1
    log = json.loads((output_dir / "logs.jsonl").read_text(encoding="utf-8"))
    metric = next(csv.DictReader((output_dir / "metrics.csv").open(encoding="utf-8", newline="")))
    assert log["timestamp"] == "2026-10-16T03:00:00Z"
    assert log["service"] == "payment-api"
    assert "[REDACTED_EMAIL]" in log["message"]
    assert "[REDACTED_SECRET]" in log["message"]
    assert log["provenance"] == metric["provenance"] == "production_export"
    assert metric["timestamp"] == "2026-10-16T03:01:00Z"


def test_ollama_rca_request_disables_thinking(monkeypatch) -> None:
    from app.models.llm.ollama import OllamaRcaGenerator

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps({"message": {"content": json.dumps({
                "status": "insufficient_evidence", "observed_facts": [], "hypotheses": [],
                "probable_root_cause": None, "root_cause_evidence_ids": [],
                "confidence": "low", "missing_evidence": ["More logs"],
                "verification_steps": [], "proposed_actions": [],
            })}}).encode()

    def fake_urlopen(request, timeout):
        captured.update(json.loads(request.data))
        return FakeResponse()

    monkeypatch.setattr("app.models.llm.ollama.urlopen", fake_urlopen)
    result = OllamaRcaGenerator().generate("system", "user")
    assert result.status == "insufficient_evidence"
    assert captured["think"] is False
    assert captured["stream"] is False
    assert captured["options"]["temperature"] == 0
