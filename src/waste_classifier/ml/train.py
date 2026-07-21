"""Train the waste classifier: MobileNetV2 transfer learning + fine-tuning.

Two-stage training:
  1. Feature extraction — MobileNetV2 base frozen, train only the new head.
  2. Fine-tuning — unfreeze the top of the base and train with a low
     learning rate to squeeze out extra accuracy.

Both stages use:
  - Class weighting, since TrashNet is imbalanced (the "trash" class has ~3-4x
    fewer images than the others) — without this the model is implicitly
    penalized less for misclassifying rare classes.
  - EarlyStopping(restore_best_weights=True), so the saved model is whichever
    epoch had the best validation accuracy, not just whatever the last epoch
    happened to be (which can be a worse, overfit epoch).

Usage:
    python -m waste_classifier.ml.train
"""

from __future__ import annotations

import json

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2

from waste_classifier import config

BATCH = 32
HEAD_EPOCHS = 20
FINE_TUNE_EPOCHS = 20
FINE_TUNE_AT = 60  # unfreeze layers from this index onward (more of the base than before)
FINE_TUNE_LR = 1e-5
EARLY_STOP_PATIENCE = 5


def build_datasets():
    train_ds = tf.keras.utils.image_dataset_from_directory(
        config.DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=config.IMG_SIZE,
        batch_size=BATCH,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        config.DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=config.IMG_SIZE,
        batch_size=BATCH,
    )

    class_names = train_ds.class_names

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=autotune)
    val_ds = val_ds.cache().prefetch(buffer_size=autotune)
    return train_ds, val_ds, class_names


def compute_class_weights(class_names: list[str]) -> dict[int, float]:
    """Inverse-frequency class weights from on-disk file counts per class.

    TrashNet is imbalanced (e.g. "trash" has ~137 images vs. ~400-600 for
    other classes), which otherwise biases the model toward the majority
    classes and away from correctly learning the rare ones.
    """
    counts = np.array(
        [len(list((config.DATASET_DIR / name).glob("*"))) for name in class_names],
        dtype=np.float64,
    )
    total = counts.sum()
    num_classes = len(class_names)
    weights = total / (num_classes * counts)
    return {i: float(w) for i, w in enumerate(weights)}


def build_model(num_classes: int, base: MobileNetV2):
    data_augmentation = models.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.15),
            layers.RandomZoom(0.15),
            layers.RandomContrast(0.1),
            layers.RandomTranslation(0.1, 0.1),
        ],
        name="augmentation",
    )

    model = models.Sequential(
        [
            data_augmentation,
            layers.Rescaling(1.0 / 255),
            base,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(num_classes, activation="softmax"),
        ]
    )
    return model


def main() -> None:
    train_ds, val_ds, class_names = build_datasets()
    print(f"Classes: {class_names}")

    class_weight = compute_class_weights(class_names)
    print(f"Class weights (inverse-frequency, to correct for dataset imbalance): {class_weight}")

    base = MobileNetV2(
        input_shape=config.IMG_SIZE + (3,), include_top=False, weights="imagenet"
    )
    base.trainable = False

    model = build_model(len(class_names), base)
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=EARLY_STOP_PATIENCE,
        restore_best_weights=True,
    )

    print(f"\n[Stage 1/2] Training classifier head (up to {HEAD_EPOCHS} epochs, base frozen)...")
    history_head = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=HEAD_EPOCHS,
        class_weight=class_weight,
        callbacks=[early_stop],
    )

    print(f"\n[Stage 2/2] Fine-tuning top layers (up to {FINE_TUNE_EPOCHS} epochs)...")
    base.trainable = True
    for layer in base.layers[:FINE_TUNE_AT]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    fine_tune_early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=EARLY_STOP_PATIENCE,
        restore_best_weights=True,
    )
    history_fine = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=FINE_TUNE_EPOCHS,
        class_weight=class_weight,
        callbacks=[fine_tune_early_stop],
    )

    config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(config.MODEL_PATH)
    with open(config.CLASS_NAMES_PATH, "w") as f:
        json.dump(class_names, f)

    combined_history = {
        "head": {k: [float(v) for v in vs] for k, vs in history_head.history.items()},
        "fine_tune": {k: [float(v) for v in vs] for k, vs in history_fine.history.items()},
        "class_weight": class_weight,
    }
    config.METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.METRICS_DIR / "training_history.json", "w") as f:
        json.dump(combined_history, f, indent=2)

    best_val_acc = max(history_fine.history["val_accuracy"])
    print(f"\nDone. Best validation accuracy (restored): {best_val_acc:.2%}")
    print(f"Model saved to {config.MODEL_PATH}")
    print("Run 'python -m waste_classifier.ml.evaluate' to generate metrics + a confusion matrix.")


if __name__ == "__main__":
    main()
