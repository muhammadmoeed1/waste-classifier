"""Phase 3.1: scripts/build_correction_set.py.

Validates data/corrections/<class>/ against the model's known classes and
copies real, openable images into data/corrections_processed/<class>/ --
this is a human-curated set (raw uploaded images are never stored, per
db/models.py's image_hash), so there is nothing to auto-export from the DB.
"""

from __future__ import annotations

import pytest
from PIL import Image
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from scripts import build_correction_set


@pytest.fixture
def isolated_db(monkeypatch):
    import waste_classifier.db.session as db_session

    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(test_engine)
    monkeypatch.setattr(db_session, "engine", test_engine)
    yield test_engine


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    corrections_dir = tmp_path / "corrections"
    output_dir = tmp_path / "corrections_processed"
    monkeypatch.setattr(build_correction_set, "CORRECTIONS_DIR", corrections_dir)
    monkeypatch.setattr(build_correction_set, "OUTPUT_DIR", output_dir)
    return corrections_dir, output_dir


def _write_valid_image(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (32, 32), color=(10, 200, 30))
    img.save(path, format="PNG")


def test_report_pending_corrections_counts_feedback_labels(isolated_db):
    from waste_classifier.db.models import Scan

    known_classes = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
    with Session(isolated_db) as session:
        session.add(
            Scan(
                session_id="s1",
                mode="upload",
                predicted_label="glass",
                confidence=55.0,
                all_probabilities="{}",
                latency_ms=100,
                image_hash="a" * 64,
                feedback_label="plastic",
            )
        )
        session.add(
            Scan(
                session_id="s2",
                mode="upload",
                predicted_label="metal",
                confidence=90.0,
                all_probabilities="{}",
                latency_ms=100,
                image_hash="b" * 64,
                # no feedback_label -- must not be counted
            )
        )
        session.commit()

    counts = build_correction_set.report_pending_corrections(known_classes)
    assert counts["plastic"] == 1
    assert counts["glass"] == 0
    assert counts["metal"] == 0


def test_validate_and_copy_accepts_valid_images_and_skips_invalid(isolated_dirs):
    corrections_dir, output_dir = isolated_dirs
    known_classes = ["glass", "metal"]

    _write_valid_image(corrections_dir / "glass" / "good.png")
    (corrections_dir / "glass" / "bad.png").parent.mkdir(parents=True, exist_ok=True)
    (corrections_dir / "glass" / "bad.png").write_bytes(b"not an image")

    copied = build_correction_set.validate_and_copy(known_classes)

    assert copied == {"glass": 1, "metal": 0}
    assert (output_dir / "glass" / "good.png").exists()
    assert not (output_dir / "glass" / "bad.png").exists()


def test_validate_and_copy_skips_unknown_class_folders(isolated_dirs):
    corrections_dir, output_dir = isolated_dirs
    _write_valid_image(corrections_dir / "not_a_real_class" / "img.png")

    copied = build_correction_set.validate_and_copy(["glass", "metal"])

    assert copied == {"glass": 0, "metal": 0}
    assert not (output_dir / "not_a_real_class").exists()


def test_validate_and_copy_with_no_corrections_dir_returns_zero_counts(isolated_dirs):
    known_classes = ["glass", "metal"]
    copied = build_correction_set.validate_and_copy(known_classes)
    assert copied == {"glass": 0, "metal": 0}
