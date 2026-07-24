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
        # Grad-CAM explainability overlay
        assert body["gradcam_image"] is None or body["gradcam_image"].startswith(
            "data:image/png;base64,"
        )
        # Environmental impact facts are defined for every known class
        assert body["impact"] is not None
        assert "headline" in body["impact"]
        assert "fact" in body["impact"]


def test_predict_skips_gradcam_when_include_gradcam_false(client):
    img = Image.new("RGB", (224, 224), color=(80, 160, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        "/api/predict?include_gradcam=false",
        files={"image": ("test.png", buf, "image/png")},
    )
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        assert res.json()["gradcam_image"] is None


def test_predict_respects_disable_gradcam_config_override(client, monkeypatch):
    from waste_classifier import config

    monkeypatch.setattr(config, "DISABLE_GRADCAM", True)

    img = Image.new("RGB", (224, 224), color=(80, 160, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # include_gradcam=true is requested, but the server-side lite-deployment
    # flag must win to keep memory usage bounded.
    res = client.post(
        "/api/predict?include_gradcam=true",
        files={"image": ("test.png", buf, "image/png")},
    )
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        assert res.json()["gradcam_image"] is None


def test_detect_with_valid_image_or_503_if_model_missing(client):
    img = Image.new("RGB", (224, 224), color=(80, 160, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        "/api/detect",
        files={"image": ("test.png", buf, "image/png")},
    )
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        body = res.json()
        assert "detections" in body
        assert body["annotated_image"].startswith("data:image/png;base64,")
        for det in body["detections"]:
            assert len(det["box"]) == 4
            assert "label" in det


def test_transcribe_without_groq_key_returns_503(client, monkeypatch):
    from waste_classifier import config

    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    res = client.post(
        "/api/transcribe",
        files={"audio": ("test.webm", b"fake-audio-bytes", "audio/webm")},
    )
    assert res.status_code == 503


def test_transcribe_rejects_empty_audio(client):
    from waste_classifier import config

    if not config.GROQ_API_KEY:
        return  # covered by test_transcribe_without_groq_key_returns_503

    res = client.post(
        "/api/transcribe",
        files={"audio": ("test.webm", b"", "audio/webm")},
    )
    assert res.status_code == 400


def test_chat_without_groq_key_returns_503_or_200(client, monkeypatch):
    from waste_classifier import config

    if not config.GROQ_API_KEY:
        res = client.post("/api/chat", json={"question": "Can I recycle glass?"})
        assert res.status_code == 503


def test_agent_without_groq_key_returns_503(client, monkeypatch):
    from waste_classifier import config

    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    res = client.post("/api/agent", json={"question": "How much CO2 for 1kg of metal?"})
    assert res.status_code == 503


def test_agent_with_groq_key_calls_tools_and_answers(client):
    from waste_classifier import config

    if not config.GROQ_API_KEY:
        return  # covered by test_agent_without_groq_key_returns_503

    res = client.post(
        "/api/agent",
        json={"question": "How much CO2 do I save recycling 2kg of aluminum cans?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["answer"]
    assert isinstance(body["tools_used"], list)
    assert len(body["tools_used"]) > 0
    assert body["tools_used"][0]["name"] in (
        "estimate_environmental_impact",
        "lookup_recycling_guide",
        "check_recyclability",
    )
