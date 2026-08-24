"""Phase 1.3: real SSE framing for /api/chat/stream, including in-band error
frames for upstream Groq failures that occur mid-stream (after the HTTP
response has already started, so the status code can no longer change)."""

from __future__ import annotations

import json

import groq
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from waste_classifier.api.main import app

    with TestClient(app) as c:
        yield c


def _parse_sse(raw_text: str) -> list[tuple[str, dict]]:
    """Parse raw SSE body text into a list of (event_type, data_dict) frames."""
    frames = []
    for raw_frame in raw_text.split("\n\n"):
        if not raw_frame.strip():
            continue
        event_type = "message"
        data_line = ""
        for line in raw_frame.split("\n"):
            if line.startswith("event:"):
                event_type = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_line = line[len("data:") :].strip()
        if data_line:
            frames.append((event_type, json.loads(data_line)))
    return frames


def test_stream_emits_token_and_done_frames_on_success(client, monkeypatch):
    from waste_classifier import config

    if not config.GROQ_API_KEY:
        pytest.skip("requires a configured GROQ_API_KEY")

    res = client.post("/api/chat/stream", json={"question": "Can I recycle glass?"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")

    frames = _parse_sse(res.text)
    event_types = [f[0] for f in frames]
    assert "token" in event_types
    assert event_types[-1] == "done"
    assert "error" not in event_types


def test_stream_emits_error_frame_on_upstream_failure(client, monkeypatch):
    """Simulates a Groq failure partway through the stream. Regression test
    for the bug where an upstream failure mid-stream just silently truncated
    the HTTP response instead of surfacing any error to the client."""
    from waste_classifier import config
    from waste_classifier.genai import assistant

    monkeypatch.setattr(config, "GROQ_API_KEY", "fake-key-for-this-test")

    def fake_ask_stream(*args, **kwargs):
        yield "partial answer, then it breaks... "
        raise groq.GroqError("simulated upstream failure")

    monkeypatch.setattr(assistant, "ask_stream", fake_ask_stream)

    res = client.post("/api/chat/stream", json={"question": "Can I recycle glass?"})
    assert res.status_code == 200  # headers already sent; can't change to 5xx now

    frames = _parse_sse(res.text)
    event_types = [f[0] for f in frames]
    assert "token" in event_types
    assert "error" in event_types
    assert "done" not in event_types  # stream stopped at the error, not a clean finish

    error_frame = next(data for etype, data in frames if etype == "error")
    assert "detail" in error_frame
    assert "simulated upstream failure" in error_frame["detail"]
