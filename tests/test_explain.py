from PIL import Image

from waste_classifier.ml.classifier import WasteClassifier
from waste_classifier.ml.explain import generate_gradcam


def test_gradcam_produces_a_valid_png_data_uri_if_model_present():
    clf = WasteClassifier()
    clf.load()
    if not clf.is_ready:
        return  # model artifact not present in this environment (e.g. fresh CI)

    img = Image.new("RGB", (224, 224), color=(100, 140, 90))
    uri = generate_gradcam(clf.model, img)

    assert uri.startswith("data:image/png;base64,")
    assert len(uri) > 1000
