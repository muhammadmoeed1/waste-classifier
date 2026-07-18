import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client():
    from waste_classifier.api.main import app

    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "model_loaded" in body
    assert "retriever_ready" in body


def test_predict_rejects_non_image(client):
    res = client.post(
        "/api/predict",
        files={"image": ("not-an-image.txt", b"hello world", "text/plain")},
    )
    assert res.status_code in (400, 503)


def test_predict_with_valid_image_or_503_if_model_missing(client):
    img = Image.new("RGB", (224, 224), color=(80, 160, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        "/api/predict",
        files={"image": ("test.png", buf, "image/png")},
    )
    # 200 if the trained model artifact is present, 503 if not (e.g. fresh CI checkout).
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        body = res.json()
        assert "label" in body
        assert "confidence" in body
        assert "probabilities" in body


def test_chat_without_groq_key_returns_503_or_200(client, monkeypatch):
    from waste_classifier import config

    if not config.GROQ_API_KEY:
        res = client.post("/api/chat", json={"question": "Can I recycle glass?"})
        assert res.status_code == 503
