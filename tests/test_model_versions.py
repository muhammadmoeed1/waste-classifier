"""Phase 3.1: GET /api/scans/review and GET /api/models.

Same isolated in-memory SQLite pattern as tests/test_persistence.py.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def client(monkeypatch):
    import waste_classifier.db.session as db_session

    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(test_engine)
    monkeypatch.setattr(db_session, "engine", test_engine)

    from waste_classifier.api.main import app

    with TestClient(app) as c:
        c.db_engine = test_engine
        yield c


def _seed_scan(engine, **overrides):
    from waste_classifier.db.models import Scan

    defaults = {
        "session_id": "s1",
        "mode": "upload",
        "predicted_label": "glass",
        "confidence": 90.0,
        "all_probabilities": "{}",
        "latency_ms": 100,
        "image_hash": "a" * 64,
    }
    defaults.update(overrides)
    with Session(engine) as session:
        row = Scan(**defaults)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def test_review_queue_includes_low_confidence_and_corrected_scans(client):
    _seed_scan(client.db_engine, confidence=95.0)  # neither low-confidence nor corrected
    _seed_scan(client.db_engine, confidence=40.0)  # low confidence
    _seed_scan(client.db_engine, confidence=90.0, feedback_label="plastic")  # corrected

    res = client.get("/api/scans/review")
    assert res.status_code == 200
    scans = res.json()["scans"]
    assert len(scans) == 2
    reasons = {s["reason"] for s in scans}
    assert reasons == {"low_confidence", "corrected"}


def test_review_queue_excludes_scan_corrected_to_the_same_label(client):
    """A feedback_label equal to predicted_label isn't really a correction --
    the user confirmed the model was right, not that it was wrong."""
    _seed_scan(client.db_engine, confidence=95.0, predicted_label="glass", feedback_label="glass")

    res = client.get("/api/scans/review")
    assert res.json()["scans"] == []


def test_review_queue_empty_when_nothing_needs_review(client):
    _seed_scan(client.db_engine, confidence=95.0)
    res = client.get("/api/scans/review")
    assert res.status_code == 200
    assert res.json()["scans"] == []


def test_models_endpoint_reports_production_and_retrained_versions(client, monkeypatch, tmp_path):
    from waste_classifier import config

    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    (metrics_dir / "metrics.json").write_text(
        json.dumps({"accuracy": 0.83, "per_class": {"glass": {"f1": 0.82}}})
    )
    monkeypatch.setattr(config, "METRICS_DIR", metrics_dir)

    models_dir = tmp_path / "models"
    v1_dir = models_dir / "v1"
    v1_dir.mkdir(parents=True)
    (v1_dir / "metrics.json").write_text(
        json.dumps(
            {"accuracy": 0.85, "per_class": {"glass": {"f1": 0.86}}, "num_correction_examples": 4}
        )
    )
    monkeypatch.setattr(config, "MODELS_DIR", models_dir)
    monkeypatch.setattr(config, "MODEL_VERSION", "")  # "production" is active

    res = client.get("/api/models")
    assert res.status_code == 200
    body = res.json()

    assert body["active_version"] == "production"
    versions_by_name = {v["version"]: v for v in body["versions"]}
    assert versions_by_name["production"]["is_active"] is True
    assert versions_by_name["production"]["overall_accuracy"] == 0.83
    assert versions_by_name["v1"]["is_active"] is False
    assert versions_by_name["v1"]["per_class_f1"]["glass"] == 0.86
    assert versions_by_name["v1"]["num_correction_examples"] == 4


def test_models_endpoint_respects_active_model_version(client, monkeypatch, tmp_path):
    from waste_classifier import config

    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    (metrics_dir / "metrics.json").write_text(json.dumps({"accuracy": 0.83, "per_class": {}}))
    monkeypatch.setattr(config, "METRICS_DIR", metrics_dir)

    models_dir = tmp_path / "models"
    v2_dir = models_dir / "v2"
    v2_dir.mkdir(parents=True)
    (v2_dir / "metrics.json").write_text(json.dumps({"accuracy": 0.9, "per_class": {}}))
    monkeypatch.setattr(config, "MODELS_DIR", models_dir)
    monkeypatch.setattr(config, "MODEL_VERSION", "v2")

    res = client.get("/api/models")
    body = res.json()
    assert body["active_version"] == "v2"
    versions_by_name = {v["version"]: v for v in body["versions"]}
    assert versions_by_name["v2"]["is_active"] is True
    assert versions_by_name["production"]["is_active"] is False
    # Drift's baseline should come from the ACTIVE version (v2), not production
    assert body["drift"]["baseline_accuracy"] == 0.9


def test_models_endpoint_flags_drift_when_recent_confidence_is_low(client, monkeypatch, tmp_path):
    from waste_classifier import config

    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    (metrics_dir / "metrics.json").write_text(json.dumps({"accuracy": 0.9, "per_class": {}}))
    monkeypatch.setattr(config, "METRICS_DIR", metrics_dir)
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(config, "MODEL_VERSION", "")

    # 50% mean confidence vs. a 90% baseline is a clear drift signal.
    _seed_scan(client.db_engine, confidence=50.0)
    _seed_scan(client.db_engine, confidence=50.0)

    res = client.get("/api/models")
    drift = res.json()["drift"]
    assert drift["rolling_7day_mean_confidence"] == pytest.approx(0.5)
    assert drift["is_drifting"] is True


def test_models_endpoint_with_no_data_reports_no_drift(client, monkeypatch, tmp_path):
    from waste_classifier import config

    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    (metrics_dir / "metrics.json").write_text(json.dumps({"accuracy": 0.9, "per_class": {}}))
    monkeypatch.setattr(config, "METRICS_DIR", metrics_dir)
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(config, "MODEL_VERSION", "")

    res = client.get("/api/models")
    drift = res.json()["drift"]
    assert drift["rolling_7day_mean_confidence"] is None
    assert drift["is_drifting"] is False
