"""Confidence-aware signals layered on top of a raw softmax prediction:
out-of-distribution (OOD) detection and top-2 ambiguity.

The model only knows six classes and, like any softmax classifier, will
happily assign a confident-looking label to something it has never seen
(a phone, a shoe) rather than expressing uncertainty. Two complementary
signals address this:

- Shannon entropy over the softmax output: near-uniform output (no real
  "opinion") suggests the input doesn't resemble any learned class well.
  This is a real, but limited, heuristic -- a model can also be
  *confidently wrong* on an OOD input (empirically, random-noise images
  fed to this model sometimes score LOWER entropy than confused-but-real
  photos), so it will not catch every OOD case. It's kept deliberately
  conservative (see OOD_ENTROPY_THRESHOLD below) so it rarely misfires on
  real in-distribution photos, at the cost of missing some genuine OOD
  inputs -- a false "I don't know" is a worse experience than an
  occasional missed one.
- Top-2 margin: how far the top prediction is from the runner-up. This is
  the stronger, empirically-validated signal here (see below) and directly
  targets the documented glass<->plastic confusion.

Thresholds were derived empirically against this model's real TrashNet
validation split (505 images, scripts/tune_ood_threshold.py), not guessed:

  Entropy percentiles (all 505 predictions):      p50=0.55  p90=1.41  p95=1.63  p99=2.11
  Entropy percentiles (correct predictions only):  p50=0.39            p95=1.48
  Entropy percentiles (wrong predictions only):    p50=1.06            p95=2.00
  Margin: 6.9% of predictions have margin < 0.15; their accuracy is 40%,
          vs. 86% for predictions at or above that margin -- a real, sizeable
          split, not a rule of thumb.

OOD_ENTROPY_THRESHOLD=2.1 sits at the 99th percentile of real (in-distribution)
predictions -- i.e. flagging as OOD is a rare event on genuine TrashNet-like
photos, deliberately erring toward under-triggering. TOP2_MARGIN_THRESHOLD
matches the brief's brief and the empirical accuracy cliff above.
"""

from __future__ import annotations

import math

OOD_ENTROPY_THRESHOLD = 2.1
TOP2_MARGIN_THRESHOLD = 0.15


def shannon_entropy(probabilities: dict[str, float]) -> float:
    """Shannon entropy, in bits, of a softmax output given as percentages
    (0-100, as classifier.Prediction.probabilities already is)."""
    total = sum(probabilities.values()) or 1.0
    entropy = 0.0
    for pct in probabilities.values():
        p = pct / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def is_out_of_distribution(probabilities: dict[str, float]) -> bool:
    return shannon_entropy(probabilities) >= OOD_ENTROPY_THRESHOLD


def top2_margin_and_runnerup(probabilities: dict[str, float]) -> tuple[float, str | None, float]:
    """Returns (margin as a 0-1 fraction, runner-up label, runner-up
    confidence as a percentage). Margin is 1.0 and there's no runner-up when
    fewer than 2 classes are present."""
    ranked = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)
    if len(ranked) < 2:
        return 1.0, None, 0.0
    (_, top_pct), (runner_up_label, runner_up_pct) = ranked[0], ranked[1]
    margin = (top_pct - runner_up_pct) / 100.0
    return margin, runner_up_label, runner_up_pct


def is_ambiguous(probabilities: dict[str, float]) -> bool:
    margin, _, _ = top2_margin_and_runnerup(probabilities)
    return margin < TOP2_MARGIN_THRESHOLD
