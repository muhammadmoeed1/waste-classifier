"""Phase 3.2: entropy-based OOD gate + top-2 margin ambiguity check.

Thresholds are empirically derived (see ml/confidence.py's docstring and
scripts/tune_ood_threshold.py) against the real validation set -- these tests
cover the pure math, not the specific threshold values themselves.
"""

from __future__ import annotations

import math

from waste_classifier.ml.confidence import (
    OOD_ENTROPY_THRESHOLD,
    TOP2_MARGIN_THRESHOLD,
    is_ambiguous,
    is_out_of_distribution,
    shannon_entropy,
    top2_margin_and_runnerup,
)

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]


def _probs(**overrides: float) -> dict[str, float]:
    """All six classes default to 0, override the ones you care about."""
    base = dict.fromkeys(CLASSES, 0.0)
    base.update(overrides)
    return base


def test_shannon_entropy_is_zero_for_a_fully_confident_prediction():
    assert shannon_entropy(_probs(glass=100.0)) == 0.0


def test_shannon_entropy_is_maximal_for_a_uniform_distribution_over_6_classes():
    uniform = {name: 100.0 / 6 for name in CLASSES}
    assert math.isclose(shannon_entropy(uniform), math.log2(6), rel_tol=1e-6)


def test_is_out_of_distribution_true_above_threshold_false_below():
    # A near-uniform 6-way split has entropy close to log2(6) ~ 2.585, above OOD_ENTROPY_THRESHOLD.
    uniform = {name: 100.0 / 6 for name in CLASSES}
    assert shannon_entropy(uniform) > OOD_ENTROPY_THRESHOLD
    assert is_out_of_distribution(uniform) is True

    confident = _probs(glass=97.0, metal=1.0, paper=0.5, plastic=0.5, cardboard=0.5, trash=0.5)
    assert is_out_of_distribution(confident) is False


def test_top2_margin_and_runnerup_identifies_the_second_place_class():
    probs = _probs(glass=55.0, plastic=40.0, metal=3.0, paper=1.0, cardboard=0.5, trash=0.5)
    margin, runner_up, runner_up_conf = top2_margin_and_runnerup(probs)
    assert runner_up == "plastic"
    assert runner_up_conf == 40.0
    assert margin == (55.0 - 40.0) / 100.0


def test_top2_margin_with_a_single_class_has_no_runnerup():
    margin, runner_up, runner_up_conf = top2_margin_and_runnerup({"glass": 100.0})
    assert margin == 1.0
    assert runner_up is None
    assert runner_up_conf == 0.0


def test_is_ambiguous_matches_the_margin_threshold():
    close_call = _probs(glass=52.0, plastic=45.0, metal=1.0, paper=1.0, cardboard=0.5, trash=0.5)
    margin, _, _ = top2_margin_and_runnerup(close_call)
    assert margin < TOP2_MARGIN_THRESHOLD
    assert is_ambiguous(close_call) is True

    clear_winner = _probs(glass=90.0, plastic=5.0, metal=2.0, paper=1.0, cardboard=1.0, trash=1.0)
    assert is_ambiguous(clear_winner) is False
