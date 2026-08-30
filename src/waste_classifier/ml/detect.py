"""Multi-item detection: locate multiple objects in one image, then classify each.

Localization ("where are the objects?") and classification ("what material is
this object?") are deliberately split into two stages, because TrashNet has no
bounding-box labels to train a waste-specific detector on:

  1. Localize candidate regions from **two complementary sources** and union
     them: a pretrained YOLOv8n (trained on COCO, used only for "where is *an*
     object" — its COCO class label is discarded) when ultralytics is
     installed, plus classical CV (OpenCV contour/edge detection) always.
     Neither alone is sufficient in practice — YOLO's learned priors catch
     upright, COCO-familiar shapes (bottles, books) that classical CV can miss
     amid background clutter, but has no COCO class for e.g. a can lying on
     its side, which classical CV's contrast-based contours catch fine.
     When ultralytics isn't installed (the lite deployment profile, which
     deliberately excludes the torch-based dependency stack), classical CV
     alone still works unchanged.
  2. Classify each localized region with our own fine-tuned MobileNetV2
     classifier — the actual material label (cardboard/glass/.../trash) comes
     from here, not from YOLO. The confidence-based suppression step below
     also resolves duplicate/overlapping regions from the two sources.

This two-stage "detect, then classify" design is a common, legitimate pattern
for domains without detector-ready labeled data.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from waste_classifier.ml.confidence import (
    TOP2_MARGIN_THRESHOLD,
    is_out_of_distribution,
    top2_margin_and_runnerup,
)

MIN_AREA_FRACTION = 0.015  # ignore contours smaller than 1.5% of the image area
MAX_AREA_FRACTION = 0.85  # ignore contours that basically span the whole image
IOU_MERGE_THRESHOLD = 0.4  # drop boxes that overlap an already-kept box this much
CONTAINMENT_THRESHOLD = 0.75  # drop boxes mostly contained within (or containing) a kept box
PADDING_FRACTION = 0.08  # padding added around each crop before classifying

YOLO_CONFIDENCE_THRESHOLD = 0.25
YOLO_EXCLUDED_CLASSES = {"person"}  # not relevant to a waste-sorting photo

_yolo_model = None
_yolo_load_attempted = False


def _get_yolo_model():
    """Lazily load a pretrained YOLOv8n model if ultralytics is available.

    Returns None (rather than raising) when ultralytics isn't installed, so
    callers can fall back to classical CV — this keeps the lite deployment
    profile (which excludes ultralytics/torch) working unchanged.
    """
    global _yolo_model, _yolo_load_attempted
    if _yolo_load_attempted:
        return _yolo_model

    _yolo_load_attempted = True
    try:
        from ultralytics import YOLO

        _yolo_model = YOLO("yolov8n.pt")
    except ImportError:
        _yolo_model = None
    return _yolo_model

_PALETTE = [
    (29, 158, 117),  # accent green
    (230, 126, 34),
    (52, 152, 219),
    (231, 76, 60),
    (155, 89, 182),
    (241, 196, 15),
]


@dataclass
class Detection:
    box: tuple[int, int, int, int]  # x, y, w, h in original image pixels
    label: str
    confidence: float
    recyclable: bool
    is_out_of_distribution: bool = False
    is_ambiguous: bool = False


def _intersection_area(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2, bx2, by2 = ax + aw, ay + ah, bx + bw, by + bh

    inter_x1, inter_y1 = max(ax, bx), max(ay, by)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    return max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    aw, ah = a[2], a[3]
    bw, bh = b[2], b[3]
    inter_area = _intersection_area(a, b)
    if inter_area == 0:
        return 0.0
    union_area = aw * ah + bw * bh - inter_area
    return inter_area / union_area


def _is_covered(candidate: tuple[int, int, int, int], kept: tuple[int, int, int, int]) -> bool:
    """True if `candidate` overlaps `kept` enough that it should be suppressed.

    Plain IoU under-triggers for nested boxes (a small box fully inside a much
    larger one has low IoU despite being entirely redundant), so this also
    checks containment from either box's perspective.
    """
    if _iou(candidate, kept) > IOU_MERGE_THRESHOLD:
        return True
    inter_area = _intersection_area(candidate, kept)
    cand_area = candidate[2] * candidate[3]
    kept_area = kept[2] * kept[3]
    if cand_area and inter_area / cand_area > CONTAINMENT_THRESHOLD:
        return True
    if kept_area and inter_area / kept_area > CONTAINMENT_THRESHOLD:
        return True
    return False


def _find_candidate_boxes(cv_img: np.ndarray) -> list[tuple[int, int, int, int]]:
    h, w = cv_img.shape[:2]
    image_area = h * w

    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blurred, 40, 120)
    edges = cv2.dilate(edges, np.ones((7, 7), np.uint8), iterations=2)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA_FRACTION * image_area or area > MAX_AREA_FRACTION * image_area:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        boxes.append((x, y, bw, bh))

    if not boxes:
        # Fall back to treating the whole image as a single item.
        boxes = [(0, 0, w, h)]

    return boxes


def _find_candidate_boxes_yolo(model, rgb: Image.Image) -> list[tuple[int, int, int, int]] | None:
    """Return YOLO-localized boxes, or None if YOLO found nothing usable."""
    results = model.predict(rgb, conf=YOLO_CONFIDENCE_THRESHOLD, verbose=False)
    if not results:
        return None

    result = results[0]
    boxes = []
    for box in result.boxes:
        class_name = result.names[int(box.cls[0])]
        if class_name in YOLO_EXCLUDED_CLASSES:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        boxes.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))

    return boxes or None


def detect_and_classify(image: Image.Image, classifier) -> list[Detection]:
    """Locate candidate objects in `image` and classify each with `classifier`.

    Candidate regions are found liberally (including overlapping/nested ones),
    classified individually, then reduced via confidence-based suppression —
    analogous to non-max suppression in a trained object detector, but scored
    by the classifier's confidence rather than an objectness score. This
    correctly resolves cases like a loose background-including box vs. a tight
    box around the same object: the tighter crop usually classifies with
    higher confidence and wins.
    """
    rgb = image.convert("RGB")
    w, h = rgb.size

    # Union both sources of candidate regions rather than preferring one:
    # YOLO's learned priors catch upright, COCO-familiar objects (bottles,
    # books) that classical CV can miss amid background clutter, while
    # classical CV's contrast-based contours catch shapes YOLO has no COCO
    # class for (a can lying on its side, an unfamiliar box) — combining both
    # covers more real cases than either alone. The final confidence-based
    # suppression step (scored by our own classifier) resolves any overlap.
    cv_img = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
    boxes = list(_find_candidate_boxes(cv_img))

    yolo_model = _get_yolo_model()
    if yolo_model is not None:
        yolo_boxes = _find_candidate_boxes_yolo(yolo_model, rgb)
        if yolo_boxes:
            boxes.extend(yolo_boxes)

    candidates: list[Detection] = []
    for x, y, bw, bh in boxes:
        pad_x, pad_y = int(bw * PADDING_FRACTION), int(bh * PADDING_FRACTION)
        x0, y0 = max(0, x - pad_x), max(0, y - pad_y)
        x1, y1 = min(w, x + bw + pad_x), min(h, y + bh + pad_y)

        crop = rgb.crop((x0, y0, x1, y1))
        result = classifier.predict(crop)
        margin, _, _ = top2_margin_and_runnerup(result.probabilities)

        candidates.append(
            Detection(
                box=(x0, y0, x1 - x0, y1 - y0),
                label=result.label,
                confidence=result.confidence,
                recyclable=result.recyclable,
                is_out_of_distribution=is_out_of_distribution(result.probabilities),
                is_ambiguous=margin < TOP2_MARGIN_THRESHOLD,
            )
        )

    candidates.sort(key=lambda d: d.confidence, reverse=True)
    kept: list[Detection] = []
    for det in candidates:
        if all(not _is_covered(det.box, k.box) for k in kept):
            kept.append(det)

    return kept


def draw_detections(image: Image.Image, detections: list[Detection]) -> Image.Image:
    """Return a copy of `image` annotated with bounding boxes + labels."""
    annotated = image.convert("RGB").copy()
    draw = ImageDraw.Draw(annotated)

    try:
        font = ImageFont.truetype("arial.ttf", size=max(14, annotated.width // 40))
    except OSError:
        font = ImageFont.load_default()

    for i, det in enumerate(detections):
        color = _PALETTE[i % len(_PALETTE)]
        x, y, bw, bh = det.box
        draw.rectangle([x, y, x + bw, y + bh], outline=color, width=3)

        label_text = f"{det.label} {det.confidence:.0f}%"
        text_bbox = draw.textbbox((0, 0), label_text, font=font)
        text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        label_y = max(0, y - text_h - 6)
        draw.rectangle([x, label_y, x + text_w + 10, label_y + text_h + 6], fill=color)
        draw.text((x + 5, label_y + 2), label_text, fill="white", font=font)

    return annotated
