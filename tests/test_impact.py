from waste_classifier.ml.impact import IMPACT_FACTS, get_impact


def test_every_class_has_an_impact_fact():
    for label in ["cardboard", "glass", "metal", "paper", "plastic", "trash"]:
        fact = get_impact(label)
        assert fact is not None
        assert fact.headline
        assert fact.fact


def test_unknown_label_returns_none():
    assert get_impact("not-a-real-class") is None


def test_trash_has_no_co2_savings_but_has_a_fact():
    trash = IMPACT_FACTS["trash"]
    assert trash.co2_saved_per_kg is None
    assert trash.energy_saved_pct is None
    assert trash.fact
