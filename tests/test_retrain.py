"""Phase 3.1: scripts/retrain.py's pure-logic helpers.

Doesn't exercise the actual fine-tuning loop (covered by manual smoke-testing
against the real TrashNet data + a real base model, which isn't available in
CI) -- just the two correctness-critical, cheap-to-test pieces: version
numbering, and that correction images get labeled with their ORIGINAL class
index rather than whatever order tf.keras.utils.image_dataset_from_directory
would infer from a possibly-incomplete set of class folders.
"""

from __future__ import annotations

from PIL import Image

from scripts import retrain


def test_next_version_starts_at_v1_with_no_existing_versions(tmp_path, monkeypatch):
    from waste_classifier import config

    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    assert retrain._next_version() == "v1"


def test_next_version_increments_past_the_highest_existing(tmp_path, monkeypatch):
    from waste_classifier import config

    models_dir = tmp_path / "models"
    (models_dir / "v1").mkdir(parents=True)
    (models_dir / "v3").mkdir(parents=True)  # gap is fine -- next is max+1, not fill-the-gap
    monkeypatch.setattr(config, "MODELS_DIR", models_dir)

    assert retrain._next_version() == "v4"


def test_next_version_ignores_non_version_directories(tmp_path, monkeypatch):
    from waste_classifier import config

    models_dir = tmp_path / "models"
    (models_dir / "v2").mkdir(parents=True)
    (models_dir / "scratch").mkdir(parents=True)
    monkeypatch.setattr(config, "MODELS_DIR", models_dir)

    assert retrain._next_version() == "v3"


def test_load_corrections_labels_by_original_class_index_not_directory_order(tmp_path):
    """The corrections set here only has 'metal' and 'cardboard' -- if labels
    were assigned by the order folders happen to be found (as
    image_dataset_from_directory would do), metal would incorrectly get index
    0 and cardboard index 1. They must instead get their TRUE indices (2 and
    0) from the base model's real 6-class ordering, or fine-tuning would
    silently train the softmax head against the wrong classes."""
    class_names = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

    (tmp_path / "metal").mkdir()
    Image.new("RGB", (224, 224), color=(120, 120, 120)).save(tmp_path / "metal" / "a.jpg")
    (tmp_path / "cardboard").mkdir()
    Image.new("RGB", (224, 224), color=(150, 100, 50)).save(tmp_path / "cardboard" / "b.jpg")

    xs, ys = retrain._load_corrections_as_arrays(tmp_path, class_names)

    assert xs.shape[0] == 2
    labels = sorted(ys.tolist())
    assert labels == [0, 2]  # cardboard=0, metal=2 -- not [0, 1]


def test_load_corrections_with_no_images_returns_none(tmp_path):
    class_names = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
    xs, ys = retrain._load_corrections_as_arrays(tmp_path, class_names)
    assert xs is None
    assert ys is None
