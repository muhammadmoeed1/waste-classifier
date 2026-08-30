"""Evaluate the trained model on the validation split and record real metrics.

Produces:
  - artifacts/metrics/metrics.json          (accuracy, per-class precision/recall/F1)
  - artifacts/metrics/confusion_matrix.png  (plot)

Usage:
    python -m waste_classifier.ml.evaluate
"""

from __future__ import annotations

import json

import numpy as np
import tensorflow as tf

from waste_classifier import config


def compute_metrics(model, val_ds, class_names: list[str]) -> dict:
    """Real accuracy + per-class precision/recall/F1/support + confusion
    matrix for `model` against `val_ds`. Shared with scripts/retrain.py so
    every model version (production or retrained) reports metrics the same
    way and stays genuinely comparable on /dashboard/models."""
    y_true, y_pred = [], []
    for images, labels in val_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy().tolist())
        y_pred.extend(np.argmax(preds, axis=1).tolist())

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        precision_recall_fscore_support,
    )

    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=range(len(class_names)), zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=range(len(class_names)))

    per_class = {
        class_names[i]: {
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(support[i]),
        }
        for i in range(len(class_names))
    }

    return {
        "accuracy": round(float(accuracy), 4),
        "num_validation_samples": int(len(y_true)),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "class_names": class_names,
    }


def main() -> None:
    # NOTE: shuffle must stay True (the default) here, matching train.py exactly.
    # image_dataset_from_directory determines the validation_split slice from a
    # seeded shuffle of the file list; passing shuffle=False disables that
    # shuffle and instead takes a contiguous alphabetical tail-slice of files,
    # which (since files are listed one class-directory at a time) silently
    # drops entire classes from the "validation" set instead of reproducing
    # the same stratified split used during training.
    val_ds = tf.keras.utils.image_dataset_from_directory(
        config.DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=config.IMG_SIZE,
        batch_size=32,
    )
    class_names = val_ds.class_names

    model = tf.keras.models.load_model(config.MODEL_PATH)
    metrics = compute_metrics(model, val_ds, class_names)
    cm = metrics["confusion_matrix"]

    config.METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.METRICS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    _plot_confusion_matrix(np.array(cm), class_names, config.METRICS_DIR / "confusion_matrix.png")

    print(f"Overall accuracy: {metrics['accuracy']:.2%}")
    print(json.dumps(metrics["per_class"], indent=2))
    print(f"\nSaved metrics.json and confusion_matrix.png to {config.METRICS_DIR}")


def _plot_confusion_matrix(cm, class_names, out_path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap="Greens")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title("Confusion Matrix — Waste Classifier")

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                int(cm[i, j]),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
            )

    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
