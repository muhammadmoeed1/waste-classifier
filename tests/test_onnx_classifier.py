from PIL import Image

from waste_classifier.ml.classifier import WasteClassifier
from waste_classifier.ml.onnx_classifier import OnnxWasteClassifier


def test_onnx_classifier_not_ready_before_load():
    clf = OnnxWasteClassifier()
    assert clf.is_ready is False


def test_onnx_predict_raises_if_not_loaded():
    clf = OnnxWasteClassifier()
    img = Image.new("RGB", (224, 224))
    try:
        clf.predict(img)
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass


def test_onnx_classifier_matches_keras_classifier_if_both_present():
    keras_clf = WasteClassifier()
    keras_clf.load()
    onnx_clf = OnnxWasteClassifier()
    onnx_clf.load()

    if not keras_clf.is_ready or not onnx_clf.is_ready:
        return  # ONNX export (python -m waste_classifier.ml.export_onnx) not run in this env

    img = Image.new("RGB", (224, 224), color=(90, 150, 90))
    keras_result = keras_clf.predict(img)
    onnx_result = onnx_clf.predict(img)

    assert keras_result.label == onnx_result.label
    assert abs(keras_result.confidence - onnx_result.confidence) < 0.5
