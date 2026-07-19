"""Inference wrapper around the trained MobileNetV2 waste classifier."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from waste_classifier import config

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    label: str
    label_index: int
    confidence: float
    recyclable: bool
    probabilities: dict[str, float]


class WasteClassifier:
    """Loads the trained Keras model once and serves predictions."""

    def __init__(
        self,
        model_path: Path = config.MODEL_PATH,
        class_names_path: Path = config.CLASS_NAMES_PATH,
    ) -> None:
        self._model = None
        self._class_names: list[str] = []
        self._model_path = model_path
        self._class_names_path = class_names_path

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def model(self):
        return self._model

    @property
    def class_names(self) -> list[str]:
        return list(self._class_names)

    def load(self) -> None:
        # Imported lazily: tensorflow is a heavy import and the API should be
        # able to start (e.g. for /health) even before the model is loaded.
        import tensorflow as tf

        if not self._model_path.exists():
            logger.warning("Model file not found at %s", self._model_path)
            return

        self._model = tf.keras.models.load_model(self._model_path)
        with open(self._class_names_path) as f:
            self._class_names = json.load(f)
        logger.info("Loaded model from %s (%d classes)", self._model_path, len(self._class_names))

    def predict(self, image: Image.Image) -> Prediction:
        if not self.is_ready:
            raise RuntimeError("Model is not loaded. Call load() first or run training.")

        img = image.convert("RGB").resize(config.IMG_SIZE)
        arr = np.expand_dims(np.array(img), axis=0)

        preds = self._model.predict(arr, verbose=0)[0]
        idx = int(np.argmax(preds))
        label = self._class_names[idx]

        probabilities = {
            name: round(float(score) * 100, 2)
            for name, score in zip(self._class_names, preds)
        }

        return Prediction(
            label=label,
            label_index=idx,
            confidence=round(float(preds[idx]) * 100, 2),
            recyclable=label in config.RECYCLABLE_CLASSES,
            probabilities=probabilities,
        )


# Module-level singleton used by the API layer.
classifier = WasteClassifier()
