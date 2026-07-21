from PIL import Image

from waste_classifier.ml.classifier import WasteClassifier
from waste_classifier.ml.detect import detect_and_classify, draw_detections


def test_detect_falls_back_to_whole_image_when_no_contours_found():
    clf = WasteClassifier()
    clf.load()
    if not clf.is_ready:
        return  # model artifact not present in this environment (e.g. fresh CI)

    # A perfectly flat, featureless image has no edges/contours to detect.
    blank = Image.new("RGB", (224, 224), color=(200, 200, 200))
    detections = detect_and_classify(blank, clf)

    assert len(detections) == 1
    assert detections[0].box == (0, 0, 224, 224)
    assert detections[0].label
    assert 0 <= detections[0].confidence <= 100


def test_draw_detections_returns_annotated_image_same_size():
    clf = WasteClassifier()
    clf.load()
    if not clf.is_ready:
        return

    img = Image.new("RGB", (300, 200), color=(180, 180, 170))
    detections = detect_and_classify(img, clf)
    annotated = draw_detections(img, detections)

    assert annotated.size == img.size
    assert annotated.mode == "RGB"
