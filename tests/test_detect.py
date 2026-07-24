from PIL import Image

from waste_classifier.ml.classifier import WasteClassifier
from waste_classifier.ml.detect import (
    YOLO_EXCLUDED_CLASSES,
    _find_candidate_boxes_yolo,
    _get_yolo_model,
    detect_and_classify,
    draw_detections,
)


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


def test_get_yolo_model_does_not_raise_and_is_cached():
    # Whether ultralytics is installed or not, this must never raise — it
    # should gracefully return None so classical CV still works standalone
    # (e.g. on the lite deployment profile, which excludes ultralytics/torch).
    first = _get_yolo_model()
    second = _get_yolo_model()
    assert first is second  # cached after the first (successful or failed) load


class _FakeBox:
    def __init__(self, cls_idx, xyxy):
        self.cls = [cls_idx]
        self.xyxy = xyxy


class _FakeResult:
    def __init__(self, boxes, names):
        self.boxes = boxes
        self.names = names


class _FakeYoloModel:
    def __init__(self, boxes, names):
        self._result = _FakeResult(boxes, names)

    def predict(self, *args, **kwargs):
        return [self._result]


def test_find_candidate_boxes_yolo_excludes_person_class():
    import torch

    names = {0: "person", 1: "bottle"}
    boxes = [
        _FakeBox(0, torch.tensor([[10.0, 10.0, 50.0, 90.0]])),
        _FakeBox(1, torch.tensor([[100.0, 20.0, 180.0, 120.0]])),
    ]
    fake_model = _FakeYoloModel(boxes, names)

    img = Image.new("RGB", (224, 224))
    result = _find_candidate_boxes_yolo(fake_model, img)

    assert result == [(100, 20, 80, 100)]
    assert "person" in YOLO_EXCLUDED_CLASSES
