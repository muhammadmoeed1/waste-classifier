"""Phase 1.4: Scan/ChatTurn persistence and the /api/stats aggregate endpoint.

Each test gets its own isolated in-memory SQLite engine (monkeypatched over
`waste_classifier.db.session.engine`) so these tests never touch the real
dev database at data/app.db and can't leak state between tests.
"""

from __future__ import annotations

import hashlib
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select


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
        c.db_engine = test_engine  # convenience handle for assertions below
        yield c


def _sample_image_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), color=(80, 160, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_predict_writes_exactly_one_scan_row_with_no_image_bytes(client):
    from waste_classifier.db.models import Scan

    image_bytes = _sample_image_bytes()
    res = client.post(
        "/api/predict",
        files={"image": ("test.png", image_bytes, "image/png")},
        headers={"X-Session-Id": "test-session-1"},
    )
    if res.status_code == 503:
        pytest.skip("requires a trained model artifact to be present")
    assert res.status_code == 200

    with Session(client.db_engine) as session:
        rows = session.exec(select(Scan)).all()

    assert len(rows) == 1
    row = rows[0]
    body = res.json()
    assert row.session_id == "test-session-1"
    assert row.mode == "upload"
    assert row.predicted_label == body["label"]
    assert row.confidence == pytest.approx(body["confidence"])
    assert row.image_hash == hashlib.sha256(image_bytes).hexdigest()

    # The whole point of image_hash: never store the actual image bytes anywhere in the row.
    dumped = row.model_dump_json().encode()
    assert image_bytes not in dumped


def test_predict_mode_query_param_is_recorded(client):
    from waste_classifier.db.models import Scan

    res = client.post(
        "/api/predict?mode=camera",
        files={"image": ("frame.jpg", _sample_image_bytes(), "image/jpeg")},
    )
    if res.status_code == 503:
        pytest.skip("requires a trained model artifact to be present")

    with Session(client.db_engine) as session:
        row = session.exec(select(Scan)).one()
    assert row.mode == "camera"
    assert row.session_id == "anonymous"  # no X-Session-Id header sent


def test_chat_writes_a_chat_turn_row(client):
    from waste_classifier import config
    from waste_classifier.db.models import ChatTurn

    if not config.GROQ_API_KEY:
        pytest.skip("requires a configured GROQ_API_KEY")

    res = client.post(
        "/api/chat",
        json={"question": "Can I recycle glass?"},
        headers={"X-Session-Id": "test-session-2"},
    )
    assert res.status_code == 200

    with Session(client.db_engine) as session:
        row = session.exec(select(ChatTurn)).one()
    assert row.mode == "rag"
    assert row.session_id == "test-session-2"
    assert row.question == "Can I recycle glass?"
    assert row.latency_ms >= 0


def test_stats_reflects_seeded_scan_rows(client):
    from waste_classifier.db.models import Scan

    with Session(client.db_engine) as session:
        session.add(
            Scan(
                session_id="seed-1",
                mode="upload",
                predicted_label="plastic",
                confidence=90.0,
                all_probabilities="{}",
                latency_ms=100,
                image_hash="a" * 64,
            )
        )
        session.add(
            Scan(
                session_id="seed-2",
                mode="upload",
                predicted_label="plastic",
                confidence=70.0,
                all_probabilities="{}",
                latency_ms=300,
                image_hash="b" * 64,
            )
        )
        session.add(
            Scan(
                session_id="seed-3",
                mode="upload",
                predicted_label="glass",
                confidence=80.0,
                all_probabilities="{}",
                latency_ms=200,
                image_hash="c" * 64,
            )
        )
        session.commit()

    res = client.get("/api/stats")
    assert res.status_code == 200
    body = res.json()
    assert body["total_scans"] == 3
    assert body["class_distribution"] == {"plastic": 2, "glass": 1}
    assert body["mean_confidence"] == pytest.approx(80.0)
    assert body["latency_p50_ms"] == pytest.approx(200.0)


def test_stats_with_no_data_returns_zeroed_response(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    body = res.json()
    assert body["total_scans"] == 0
    assert body["class_distribution"] == {}
    assert body["mean_confidence"] == 0.0
    assert body["agent_tool_usage"] == {}
