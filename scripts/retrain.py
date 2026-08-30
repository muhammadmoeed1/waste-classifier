"""Fine-tune a trained waste classifier on human-corrected examples.

Reuses ml/train.py's transfer-learning building blocks (compute_class_weights,
build_model isn't needed here since we're fine-tuning an existing head, not
building a new one) rather than reimplementing training logic. Always writes
a NEW version to artifacts/models/v{n}/ -- it never overwrites the flat
artifacts/waste_model.keras production path (see config.py's MODEL_VERSION).

Because the corrections set is typically tiny (a handful to a few dozen
images) compared to the ~2500-image TrashNet training set, this is a small,
low-learning-rate nudge, not a full retrain -- and it's evaluated against the
*original* TrashNet validation split (same split/seed as ml/train.py) so
metrics.json stays comparable across versions and a regression is visible
immediately rather than hidden by grading on the new, easy-to-overfit
corrections themselves.

Usage:
    PYTHONPATH=src python scripts/retrain.py \
        --base artifacts/waste_model.keras \
        --corrections data/corrections_processed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from waste_classifier import config  # noqa: E402

FINE_TUNE_LR = 1e-6  # lower than ml/train.py's 1e-5 -- this is a small nudge, not a full fine-tune
DEFAULT_EPOCHS = 5


def _load_corrections_as_arrays(corrections_dir: Path, class_names: list[str]):
    """Loads every image under corrections_dir/<class>/ and labels it with
    that class's ORIGINAL index in class_names -- NOT
    tf.keras.utils.image_dataset_from_directory's automatic ordering, which
    would silently relabel classes if the corrections set doesn't happen to
    contain every class (a real, easy-to-miss bug: fine-tuning a softmax head
    against the wrong label indices)."""
    import tensorflow as tf

    xs, ys = [], []
    for idx, name in enumerate(class_names):
        class_dir = corrections_dir / name
        if not class_dir.exists():
            continue
        for image_path in sorted(class_dir.iterdir()):
            if not image_path.is_file():
                continue
            img = tf.keras.utils.load_img(image_path, target_size=config.IMG_SIZE)
            xs.append(tf.keras.utils.img_to_array(img))
            ys.append(idx)

    if not xs:
        return None, None
    return np.stack(xs), np.array(ys)


def _next_version() -> str:
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    existing = [
        int(p.name[1:])
        for p in config.MODELS_DIR.iterdir()
        if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()
    ]
    return f"v{max(existing, default=0) + 1}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base", type=Path, default=config.MODEL_PATH, help="Base Keras model to fine-tune"
    )
    parser.add_argument(
        "--corrections",
        type=Path,
        default=config.ROOT_DIR / "data" / "corrections_processed",
        help="Output of scripts/build_correction_set.py",
    )
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument(
        "--output-version", default=None, help="e.g. 'v2' -- auto-incremented if omitted"
    )
    args = parser.parse_args()

    import tensorflow as tf

    from waste_classifier.ml.evaluate import compute_metrics
    from waste_classifier.ml.train import build_datasets, compute_class_weights

    class_names_path = args.base.parent / "class_names.json"
    with open(class_names_path) as f:
        class_names = json.load(f)

    print(f"Loading base model from {args.base} ({len(class_names)} classes)...")
    model = tf.keras.models.load_model(args.base)

    xs, ys = _load_corrections_as_arrays(args.corrections, class_names)
    if xs is None:
        print(
            f"No correction images found under {args.corrections}. "
            "Run scripts/build_correction_set.py first, after adding real example "
            "photos under data/corrections/<class_name>/."
        )
        return
    num_classes_present = len(set(ys.tolist()))
    print(f"Fine-tuning on {len(xs)} corrected example(s) across {num_classes_present} class(es).")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    class_weight = compute_class_weights(class_names)
    model.fit(xs, ys, epochs=args.epochs, batch_size=min(8, len(xs)), class_weight=class_weight)

    print("\nEvaluating on the original TrashNet validation split for a comparable metric...")
    _, val_ds, val_class_names = build_datasets()
    if val_class_names != class_names:
        print(
            "WARNING: data/dataset/'s class order doesn't match the base model's "
            "class_names.json -- evaluation labels may be misaligned."
        )
    # Same accuracy/per-class-F1/confusion-matrix computation ml/evaluate.py uses
    # for the production model, so versions stay genuinely comparable on
    # /dashboard/models rather than each reporting different metrics.
    metrics = compute_metrics(model, val_ds, class_names)
    metrics["base_model"] = str(args.base)
    metrics["num_correction_examples"] = len(xs)
    metrics["epochs"] = args.epochs
    metrics["learning_rate"] = FINE_TUNE_LR
    print(f"Validation accuracy after fine-tuning: {metrics['accuracy']:.2%}")

    version = args.output_version or _next_version()
    version_dir = config.MODELS_DIR / version
    version_dir.mkdir(parents=True, exist_ok=True)

    model.save(version_dir / "waste_model.keras")
    with open(version_dir / "class_names.json", "w") as f:
        json.dump(class_names, f)
    with open(version_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved retrained model to {version_dir}/")
    print(f"To try it: set MODEL_VERSION={version} and restart the server.")
    print(f"To promote it to production: copy {version_dir}/waste_model.keras over")
    print(f"  {config.MODEL_PATH}.")


if __name__ == "__main__":
    main()
