"""Validate a human-curated data/corrections/ directory against pending
feedback corrections in the database, and prepare it for retrain.py.

Raw uploaded images are never stored (see db/models.py: Scan.image_hash is a
SHA-256 hash, not the image itself -- a deliberate privacy/storage decision
from Phase 1). That means this script cannot auto-export training images
from past corrections the way it could if images were retained. Instead:

  1. It reports which classes have pending corrections recorded via the
     app's "Wrong? Tap the right category" control, so you know what to go
     collect real example photos for.
  2. It validates a human-curated data/corrections/<class>/*.jpg directory
     (you supply the actual images) against the model's known class names,
     opens every file to confirm it's a real, undamaged image, and copies
     the valid ones into data/corrections_processed/<class>/ -- the layout
     scripts/retrain.py expects, matching data/dataset/'s existing structure.

Usage:
    PYTHONPATH=src python scripts/build_correction_set.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from sqlmodel import Session, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import waste_classifier.db.session as db_session  # noqa: E402
from waste_classifier import config  # noqa: E402
from waste_classifier.db.models import Scan  # noqa: E402

CORRECTIONS_DIR = config.ROOT_DIR / "data" / "corrections"
OUTPUT_DIR = config.ROOT_DIR / "data" / "corrections_processed"


def report_pending_corrections(known_classes: list[str]) -> dict[str, int]:
    """Count corrections recorded in the DB, grouped by the corrected
    (feedback_label) class -- i.e. what the model got wrong, by what a human
    said it actually was."""
    db_session.init_db()  # runs standalone, outside the FastAPI lifespan that normally does this
    with Session(db_session.engine) as session:
        scans = session.exec(select(Scan).where(Scan.feedback_label.is_not(None))).all()

    counts: dict[str, int] = dict.fromkeys(known_classes, 0)
    for scan in scans:
        if scan.feedback_label in counts:
            counts[scan.feedback_label] += 1
    return counts


def validate_and_copy(known_classes: list[str]) -> dict[str, int]:
    """Validate data/corrections/<class>/* against known_classes, copying
    every real, openable image into data/corrections_processed/<class>/.
    Returns a count of valid images copied per class."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    copied: dict[str, int] = dict.fromkeys(known_classes, 0)

    if not CORRECTIONS_DIR.exists():
        return copied

    for class_dir in sorted(CORRECTIONS_DIR.iterdir()):
        if not class_dir.is_dir():
            continue
        if class_dir.name not in known_classes:
            print(f"[build_correction_set] WARNING: unknown class folder '{class_dir.name}'")
            continue

        dest_dir = OUTPUT_DIR / class_dir.name
        dest_dir.mkdir(parents=True, exist_ok=True)

        for image_path in sorted(class_dir.iterdir()):
            if not image_path.is_file():
                continue
            try:
                with Image.open(image_path) as img:
                    img.verify()
            except (UnidentifiedImageError, OSError):
                print(f"[build_correction_set] WARNING: {image_path} is not a valid image")
                continue

            shutil.copy2(image_path, dest_dir / image_path.name)
            copied[class_dir.name] += 1

    return copied


def main() -> None:
    known_classes = sorted(config.RECYCLABLE_CLASSES | {"trash"})

    pending = report_pending_corrections(known_classes)
    print("Pending corrections recorded in the app (feedback_label counts):")
    for name, count in pending.items():
        print(f"  {name}: {count}")

    copied = validate_and_copy(known_classes)
    total_copied = sum(copied.values())
    print(f"\nValidated and copied {total_copied} image(s) from {CORRECTIONS_DIR} to {OUTPUT_DIR}:")
    for name, count in copied.items():
        needs_examples = pending[name] > 0 and count == 0
        flag = " <- has pending corrections but no example images yet" if needs_examples else ""
        print(f"  {name}: {count}{flag}")

    if total_copied == 0:
        print(
            f"\nNo corrections to train on yet. Add real example photos under "
            f"{CORRECTIONS_DIR}/<class_name>/ (using the class names above) and rerun."
        )


if __name__ == "__main__":
    main()
