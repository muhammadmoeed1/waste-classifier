"""Export the trained Keras model to ONNX, quantize it, and benchmark all three
serving paths (Keras, ONNX fp32, ONNX int8 dynamic-quantized) on latency and
on-disk size.

Usage:
    python -m waste_classifier.ml.export_onnx
"""

from __future__ import annotations

import json
import time

import numpy as np

from waste_classifier import config

ONNX_PATH = config.MODEL_PATH.with_suffix(".onnx")
ONNX_QUANT_PATH = config.MODEL_PATH.parent / "waste_model_quant.onnx"
BENCHMARK_RUNS = 30


def _build_inference_only_model(model):
    """Rebuild the model without its training-only data-augmentation layers.

    The augmentation Sequential (RandomFlip/RandomRotation/...) is a no-op at
    inference (training=False), but its internal SeedGenerator state variables
    aren't reachable from the SavedModel root when exporting a serving
    signature that wraps the full model — tf.saved_model.save fails with
    "captures tensor ... which is unsupported or not reachable from root".
    Reusing the same trained layer objects (Rescaling, base, pooling, dropout,
    dense) in a new Sequential that excludes the augmentation layer sidesteps
    this without needing to manually copy any weights.
    """
    import tensorflow as tf

    inference_layers = [layer for layer in model.layers if layer.name != "augmentation"]
    inference_model = tf.keras.Sequential(inference_layers)
    inference_model.build((None, *config.IMG_SIZE, 3))
    return inference_model


def export_to_onnx() -> None:
    import tensorflow as tf
    import tf2onnx

    model = tf.keras.models.load_model(config.MODEL_PATH)
    inference_model = _build_inference_only_model(model)

    # tf2onnx's from_keras() doesn't reliably support Keras 3's internal graph
    # representation (KeyError on keras_tensor_* names), so convert directly
    # from a concrete tf.function instead.
    @tf.function(
        input_signature=[tf.TensorSpec([1, *config.IMG_SIZE, 3], tf.float32, name="input")]
    )
    def serving_fn(x):
        return {"output": inference_model(x, training=False)}

    tf2onnx.convert.from_function(
        serving_fn,
        input_signature=[tf.TensorSpec([1, *config.IMG_SIZE, 3], tf.float32, name="input")],
        opset=13,
        output_path=str(ONNX_PATH),
    )

    print(f"Exported ONNX model to {ONNX_PATH}")


def quantize_onnx() -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(str(ONNX_PATH), str(ONNX_QUANT_PATH), weight_type=QuantType.QUInt8)
    print(f"Quantized ONNX model saved to {ONNX_QUANT_PATH}")


def _benchmark_keras(sample: np.ndarray) -> float:
    import tensorflow as tf

    model = tf.keras.models.load_model(config.MODEL_PATH)
    model.predict(sample, verbose=0)  # warm up

    start = time.perf_counter()
    for _ in range(BENCHMARK_RUNS):
        model.predict(sample, verbose=0)
    return (time.perf_counter() - start) / BENCHMARK_RUNS


def _benchmark_onnx(path, sample: np.ndarray) -> float:
    import onnxruntime as ort

    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    session.run(None, {input_name: sample})  # warm up

    start = time.perf_counter()
    for _ in range(BENCHMARK_RUNS):
        session.run(None, {input_name: sample})
    return (time.perf_counter() - start) / BENCHMARK_RUNS


def main() -> None:
    export_to_onnx()
    quantize_onnx()

    sample = np.random.rand(1, *config.IMG_SIZE, 3).astype(np.float32) * 255.0

    print(f"\nBenchmarking ({BENCHMARK_RUNS} runs each, single image, CPU)...")
    keras_latency = _benchmark_keras(sample)
    onnx_latency = _benchmark_onnx(ONNX_PATH, sample)
    onnx_quant_latency = _benchmark_onnx(ONNX_QUANT_PATH, sample)

    keras_size = config.MODEL_PATH.stat().st_size
    onnx_size = ONNX_PATH.stat().st_size
    onnx_quant_size = ONNX_QUANT_PATH.stat().st_size

    results = {
        "benchmark_runs": BENCHMARK_RUNS,
        "keras": {
            "latency_ms": round(keras_latency * 1000, 2),
            "size_mb": round(keras_size / 1e6, 2),
        },
        "onnx_fp32": {
            "latency_ms": round(onnx_latency * 1000, 2),
            "size_mb": round(onnx_size / 1e6, 2),
            "speedup_vs_keras": round(keras_latency / onnx_latency, 2),
        },
        "onnx_int8_quantized": {
            "latency_ms": round(onnx_quant_latency * 1000, 2),
            "size_mb": round(onnx_quant_size / 1e6, 2),
            "speedup_vs_keras": round(keras_latency / onnx_quant_latency, 2),
            "size_reduction_vs_keras_pct": round((1 - onnx_quant_size / keras_size) * 100, 1),
        },
    }

    config.METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.METRICS_DIR / "onnx_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"\nSaved benchmark to {config.METRICS_DIR / 'onnx_benchmark.json'}")


if __name__ == "__main__":
    main()
