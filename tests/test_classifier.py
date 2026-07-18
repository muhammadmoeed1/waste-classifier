from PIL import Image

from waste_classifier.ml.classifier import WasteClassifier


def test_classifier_not_ready_before_load():
    clf = WasteClassifier()
    assert clf.is_ready is False


def test_predict_raises_if_not_loaded():
    clf = WasteClassifier()
    img = Image.new("RGB", (224, 224))
    try:
        clf.predict(img)
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass


def test_classifier_loads_and_predicts_if_artifacts_present():
    clf = WasteClassifier()
    clf.load()
    if not clf.is_ready:
        # Model artifact not present in this environment (e.g. CI without the
        # trained .keras file) — nothing more to assert.
        return

    img = Image.new("RGB", (224, 224), color=(120, 120, 120))
    prediction = clf.predict(img)

    assert prediction.label
    assert 0 <= prediction.confidence <= 100
    assert isinstance(prediction.recyclable, bool)
    assert abs(sum(prediction.probabilities.values()) - 100) < 1.0
