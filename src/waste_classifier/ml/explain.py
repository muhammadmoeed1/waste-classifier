"""Grad-CAM explainability for the waste classifier.

Grad-CAM (Gradient-weighted Class Activation Mapping) produces a heatmap over the
input image highlighting the regions that most influenced the model's predicted
class — i.e. "where the model looked". This turns the classifier from a black box
into something you can visually audit.

Reference: Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks via
Gradient-based Localization" (2017).
"""

from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

from waste_classifier import config

LAST_CONV_LAYER = "out_relu"  # final conv activation of the MobileNetV2 base


def _colorize_heatmap(heatmap: np.ndarray) -> np.ndarray:
    """Map a [0,1] heatmap to an RGB 'jet'-style colormap without matplotlib."""
    # Simple blue->green->red ramp.
    r = np.clip(1.5 - np.abs(4 * heatmap - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * heatmap - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * heatmap - 1), 0, 1)
    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255).astype(np.uint8)


def generate_gradcam(model, image: Image.Image, pred_index: int | None = None) -> str:
    """Return a Grad-CAM overlay of `image` as a base64-encoded PNG data URI."""
    import tensorflow as tf

    original = image.convert("RGB")
    resized = original.resize(config.IMG_SIZE)
    arr = np.array(resized, dtype=np.float32)
    # The training pipeline rescales pixels to [0, 1] via a Rescaling layer before
    # the MobileNetV2 base, so replicate that here since we feed the base directly.
    rescaled = np.expand_dims(arr / 255.0, axis=0)

    base = model.get_layer("mobilenetv2_1.00_224")
    conv_model = tf.keras.models.Model(base.input, base.get_layer(LAST_CONV_LAYER).output)
    gap_layer = model.get_layer("global_average_pooling2d")
    dense_layer = model.get_layer("dense")

    with tf.GradientTape() as tape:
        conv_output = conv_model(rescaled)  # (1, 7, 7, 1280)
        tape.watch(conv_output)
        pooled = gap_layer(conv_output)
        predictions = dense_layer(pooled)  # dropout is inactive at inference
        if pred_index is None:
            pred_index = int(tf.argmax(predictions[0]))
        class_channel = predictions[:, pred_index]

    grads = tape.gradient(class_channel, conv_output)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))  # (1280,)

    conv_output = conv_output[0]  # (7, 7, 1280)
    heatmap = tf.reduce_sum(conv_output * pooled_grads, axis=-1)  # (7, 7)
    heatmap = tf.maximum(heatmap, 0)  # ReLU
    max_val = tf.reduce_max(heatmap)
    if max_val > 0:
        heatmap = heatmap / max_val
    heatmap = heatmap.numpy()

    # Upscale heatmap to the original image size and blend as an overlay.
    heatmap_img = Image.fromarray((heatmap * 255).astype(np.uint8)).resize(
        original.size, resample=Image.BILINEAR
    )
    heatmap_arr = np.array(heatmap_img) / 255.0
    colored = _colorize_heatmap(heatmap_arr)

    original_arr = np.array(original, dtype=np.float32)
    overlay = (0.6 * original_arr + 0.4 * colored).astype(np.uint8)
    overlay_img = Image.fromarray(overlay)

    buf = io.BytesIO()
    overlay_img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
