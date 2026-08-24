"""Phase 1.5: feedback capture on a past Scan (POST /api/scans/{id}/feedback).

Same isolated in-memory SQLite pattern as tests/test_persistence.py.
"""

from __future__ import annotations

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


def _seed_scan(engine) -> int:
    from waste_classifier.db.models import Scan

    with Session(engine) as session:
        scan = Scan(
            session_id="seed",
            mode="upload",
            predicted_label="plastic",
            confidence=55.0,
            all_probabilities="{}",
            latency_ms=120,
            image_hash="a" * 64,
        )
        session.add(scan)
        session.commit()
        session.refresh(scan)
        return scan.id


def test_feedback_updates_the_correct_row(client):
    from waste_classifier.db.models import Scan
    from waste_classifier.ml.classifier import classifier

    if not classifier.class_names:
        pytest.skip("requires a trained model artifact to be present")

    scan_id = _seed_scan(client.db_engine)
    correct_label = next(name for name in classifier.class_names if name != "plastic")

    res = client.post(f"/api/scans/{scan_id}/feedback", json={"corrected_label": correct_label})
    assert res.status_code == 200
    body = res.json()
    assert body["scan_id"] == scan_id
    assert body["feedback_label"] == correct_label

    with Session(client.db_engine) as session:
        row = session.get(Scan, scan_id)
    assert row.feedback_label == correct_label
    assert row.feedback_at is not None


def test_feedback_with_invalid_label_returns_400(client):
    from waste_classifier.ml.classifier import classifier

    if not classifier.class_names:
        pytest.skip("requires a trained model artifact to be present")

    scan_id = _seed_scan(client.db_engine)
    res = client.post(f"/api/scans/{scan_id}/feedback", json={"corrected_label": "banana-peel"})
    assert res.status_code == 400


def test_feedback_on_nonexistent_scan_returns_404(client):
    res = client.post("/api/scans/999999/feedback", json={"corrected_label": "plastic"})
    assert res.status_code == 404
