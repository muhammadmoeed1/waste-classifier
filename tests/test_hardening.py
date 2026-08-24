"""Phase 1.2 input-hardening tests: size limits, content-type allowlist,
rate limiting, and chat history capping."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client():
    from waste_classifier.api.main import app

    with TestClient(app) as c:
        yield c


def test_oversized_upload_rejected_with_413(client, monkeypatch):
    from waste_classifier import config

    img = Image.new("RGB", (224, 224), color=(80, 160, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    payload = buf.getvalue()

    # Use a limit smaller than this specific (flat-color, highly compressible)
    # test PNG, rather than building an 8MB+ payload just to exceed the real default.
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", len(payload) - 1)

    res = client.post(
        "/api/predict",
        files={"image": ("test.png", payload, "image/png")},
    )
    assert res.status_code == 413


def test_wrong_content_type_rejected_with_400(client):
    img = Image.new("RGB", (224, 224), color=(80, 160, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # Valid PNG bytes, but declared as a disallowed content-type.
    res = client.post(
        "/api/predict",
        files={"image": ("test.png", buf, "image/gif")},
    )
    assert res.status_code == 400
    assert "content type" in res.json()["detail"].lower()


def test_corrupt_image_bytes_rejected_with_400(client):
    res = client.post(
        "/api/predict",
        files={"image": ("test.png", b"not actually a png", "image/png")},
    )
    assert res.status_code == 400


def test_rate_limit_returns_429_after_burst(client):
    """/api/chat is limited to config.RATE_LIMIT_CHAT (default 10/minute).
    The rate limiter runs before the handler body, so this doesn't require a
    configured GROQ_API_KEY -- a request that would otherwise 503 still
    counts against the limit."""
    from waste_classifier import config

    limit_str = config.RATE_LIMIT_CHAT  # e.g. "10/minute"
    limit_count = int(limit_str.split("/")[0])

    statuses = []
    for _ in range(limit_count + 3):
        res = client.post("/api/chat", json={"question": "Can I recycle glass?"})
        statuses.append(res.status_code)

    tries = limit_count + 3
    assert 429 in statuses, f"expected a 429 within {tries} rapid requests, got {statuses}"
    # Everything before the limit was hit should be a normal response (200/503),
    # never 429 -- confirms the limit boundary itself, not blanket throttling.
    first_429 = statuses.index(429)
    assert first_429 >= limit_count, "rate limit triggered earlier than configured"


def test_chat_history_is_truncated_not_rejected(client):
    from waste_classifier import config
    from waste_classifier.api.schemas import ChatRequest

    limit = config.MAX_CHAT_HISTORY_MESSAGES
    oversized_history = [{"role": "user", "content": f"message {i}"} for i in range(limit + 10)]

    request = ChatRequest(question="hi", history=oversized_history)
    assert len(request.history) == limit
    # Truncation keeps the most recent messages, not the oldest.
    assert request.history[-1].content == f"message {limit + 9}"
