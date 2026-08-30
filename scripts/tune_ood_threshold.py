"""Empirically derive OOD-entropy / top-2-margin thresholds against the real
TrashNet validation split, instead of guessing them.

Prints entropy and margin percentiles (overall, and split by whether the
prediction was correct), plus the accuracy split above/below the top-2
margin threshold -- the numbers this repo's chosen thresholds
(ml/confidence.py's OOD_ENTROPY_THRESHOLD, TOP2_MARGIN_THRESHOLD) are based
on. Rerun this after retraining to confirm the thresholds still make sense
for a new model version.

Usage:
    PYTHONPATH=src python scripts/tune_ood_threshold.py [--model artifacts/waste_model.keras]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from waste_classifier import config  # noqa: E402
from waste_classifier.ml.confidence import shannon_entropy, top2_margin_and_runnerup  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=config.MODEL_PATH)
    args = parser.parse_args()

    import tensorflow as tf

    val_ds = tf.keras.utils.image_dataset_from_directory(
        config.DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=config.IMG_SIZE,
        batch_size=32,
    )
    class_names = val_ds.class_names
    model = tf.keras.models.load_model(args.model)

    entropies, margins, correct = [], [], []
    for images, labels in val_ds:
        preds = model.predict(images, verbose=0)
        for p, true_label in zip(preds, labels.numpy()):
            probabilities = {name: float(score) * 100 for name, score in zip(class_names, p)}
            entropies.append(shannon_entropy(probabilities))
            margin, _, _ = top2_margin_and_runnerup(probabilities)
            margins.append(margin)
            correct.append(int(np.argmax(p) == true_label))

    entropies = np.array(entropies)
    margins = np.array(margins)
    correct = np.array(correct)
    percentiles = [50, 75, 90, 95, 99]

    print(f"N = {len(entropies)}, overall accuracy = {correct.mean():.2%}\n")

    all_p = np.percentile(entropies, percentiles).round(3)
    correct_p = np.percentile(entropies[correct == 1], percentiles).round(3)
    print(f"Entropy percentiles {percentiles} (all):         {all_p}")
    print(f"Entropy percentiles {percentiles} (correct only): {correct_p}")
    if (correct == 0).sum():
        wrong_p = np.percentile(entropies[correct == 0], percentiles).round(3)
        print(f"Entropy percentiles {percentiles} (wrong only):   {wrong_p}")

    margin_p = np.percentile(margins, percentiles).round(3)
    print(f"\nMargin percentiles {percentiles}: {margin_p}")
    low_margin = margins < 0.15
    print(f"Fraction with margin < 0.15: {low_margin.mean():.2%}")
    if low_margin.sum():
        print(f"Accuracy when margin < 0.15:  {correct[low_margin].mean():.2%}")
    print(f"Accuracy when margin >= 0.15: {correct[~low_margin].mean():.2%}")


if __name__ == "__main__":
    main()
