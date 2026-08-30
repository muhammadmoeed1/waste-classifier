from waste_classifier.genai.tools import (
    TOOL_REGISTRY,
    TOOL_SCHEMAS,
    check_recyclability,
    estimate_environmental_impact,
    estimate_resale_value,
    execute_tool,
    lookup_recycling_guide,
)


def test_lookup_recycling_guide_returns_content_for_valid_material():
    result = lookup_recycling_guide("plastic")
    assert "guide" in result
    assert "plastic" in result["guide"].lower()


def test_lookup_recycling_guide_errors_on_unknown_material():
    result = lookup_recycling_guide("banana")
    assert "error" in result


def test_estimate_environmental_impact_computes_expected_co2():
    result = estimate_environmental_impact("metal", 2)
    assert result["co2_saved_kg"] == 18.0  # 9.0 kg CO2/kg * 2kg, matches impact.py


def test_estimate_environmental_impact_handles_trash_with_no_co2_data():
    result = estimate_environmental_impact("trash", 1)
    assert result["co2_saved_kg"] is None
    assert "note" in result


def test_estimate_environmental_impact_rejects_bad_weight():
    result = estimate_environmental_impact("metal", "not-a-number")
    assert "error" in result


def test_check_recyclability_true_and_false_cases():
    assert check_recyclability("glass")["recyclable"] is True
    assert check_recyclability("trash")["recyclable"] is False


def test_estimate_resale_value_computes_expected_pkr():
    result = estimate_resale_value("metal", 2)
    assert result["resale_value_pkr"] == 300.0  # 150.0 PKR/kg * 2kg, matches impact.py
    assert result["rate_pkr_per_kg"] == 150.0


def test_estimate_resale_value_handles_glass_with_no_local_market():
    result = estimate_resale_value("glass", 1)
    assert result["resale_value_pkr"] is None
    assert "note" in result


def test_estimate_resale_value_rejects_bad_weight():
    result = estimate_resale_value("metal", "not-a-number")
    assert "error" in result


def test_estimate_resale_value_errors_on_unknown_material():
    result = estimate_resale_value("banana", 1)
    assert "error" in result


def test_execute_tool_dispatches_by_name_with_json_string_args():
    result = execute_tool("check_recyclability", '{"material": "cardboard"}')
    assert result["recyclable"] is True


def test_execute_tool_unknown_name_returns_error():
    result = execute_tool("not_a_real_tool", "{}")
    assert "error" in result


def test_every_registered_tool_has_a_matching_schema():
    schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    assert schema_names == set(TOOL_REGISTRY.keys())
