"""Regression test for the event-loop-blocking bug (Phase 1.1).

`/api/predict` and `/api/detect` do CPU-bound TensorFlow/OpenCV work. FastAPI
only threadpool-offloads plain `def` handlers -- an `async def` handler with a
synchronous body runs directly on the event loop and blocks every other
concurrent request, including unrelated ones like `/health`. This test proves
a slow predict doesn't stall a concurrent health check.
"""

from __future__ import annotations

import io
import threading
import time

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def test_health_does_not_block_on_slow_predict(monkeypatch):
    from waste_classifier.api.main import app
    from waste_classifier.ml.classifier import classifier

    with TestClient(app) as client:
        # lifespan (entered above) is what actually calls classifier.load() --
        # is_ready is only meaningful to check once we're inside this context.
        if not classifier.is_ready:
            pytest.skip("model artifact not present in this environment")

        original_predict = classifier.predict

        def slow_predict(image):
            time.sleep(1.5)
            return original_predict(image)

        monkeypatch.setattr(classifier, "predict", slow_predict)

        img = Image.new("RGB", (224, 224), color=(80, 160, 80))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        predict_started = threading.Event()
        results = {}

        def do_predict():
            predict_started.set()
            res = client.post(
                "/api/predict", files={"image": ("t.png", buf, "image/png")}
            )
            results["status_code"] = res.status_code

        thread = threading.Thread(target=do_predict)
        thread.start()
        predict_started.wait(timeout=2)
        time.sleep(0.3)  # let the request actually enter the slow predict call

        start = time.perf_counter()
        health_res = client.get("/health")
        health_duration = time.perf_counter() - start

        thread.join(timeout=5)

        assert health_res.status_code == 200
        assert results.get("status_code") == 200
        assert health_duration < 1.0, (
            f"/health took {health_duration:.2f}s while a slow predict was in "
            "flight -- the predict handler may be blocking the event loop"
        )
