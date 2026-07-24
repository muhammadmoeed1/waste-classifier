"""Tools the recycling agent can call, plus their JSON schemas for Groq.

Each tool is a plain Python function returning a JSON-serializable dict. The
`TOOL_SCHEMAS` list describes them to the LLM in OpenAI/Groq function-calling
format, and `TOOL_REGISTRY` maps tool names to their implementations so the
agent loop can dispatch a model-requested call.
"""

from __future__ import annotations

import json

from waste_classifier import config
from waste_classifier.ml.impact import get_impact

RECYCLABLE_CLASSES = config.RECYCLABLE_CLASSES
VALID_MATERIALS = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]


def lookup_recycling_guide(material: str) -> dict:
    """Return the curated recycling knowledge base entry for a material."""
    material = (material or "").lower().strip()
    path = config.KNOWLEDGE_BASE_DIR / f"{material}.md"
    if not path.exists():
        return {
            "error": f"No guide for '{material}'. Valid materials: {', '.join(VALID_MATERIALS)}."
        }
    return {"material": material, "guide": path.read_text(encoding="utf-8")}


def estimate_environmental_impact(material: str, weight_kg: float) -> dict:
    """Estimate CO2 saved by recycling `weight_kg` of `material` vs. landfill/virgin."""
    material = (material or "").lower().strip()
    fact = get_impact(material)
    if fact is None:
        return {"error": f"Unknown material '{material}'. Valid: {', '.join(VALID_MATERIALS)}."}

    try:
        weight = float(weight_kg)
    except (TypeError, ValueError):
        return {"error": "weight_kg must be a number (kilograms)."}

    if fact.co2_saved_per_kg is None:
        return {
            "material": material,
            "recyclable": material in RECYCLABLE_CLASSES,
            "note": fact.fact,
            "co2_saved_kg": None,
        }

    return {
        "material": material,
        "weight_kg": round(weight, 3),
        "co2_saved_kg": round(fact.co2_saved_per_kg * weight, 3),
        "energy_saved_pct": fact.energy_saved_pct,
        "basis": f"{fact.co2_saved_per_kg} kg CO2e saved per kg recycled",
    }


def check_recyclability(material: str) -> dict:
    """Return whether a material is accepted by standard curbside recycling."""
    material = (material or "").lower().strip()
    if material not in VALID_MATERIALS:
        return {"error": f"Unknown material '{material}'. Valid: {', '.join(VALID_MATERIALS)}."}
    return {"material": material, "recyclable": material in RECYCLABLE_CLASSES}


TOOL_REGISTRY = {
    "lookup_recycling_guide": lookup_recycling_guide,
    "estimate_environmental_impact": estimate_environmental_impact,
    "check_recyclability": check_recyclability,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_recycling_guide",
            "description": (
                "Get detailed, curated recycling instructions for a specific waste "
                "material (how to prepare it, common mistakes, what happens to it). "
                "Call this whenever the user asks how to recycle or dispose of a material."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "material": {
                        "type": "string",
                        "enum": VALID_MATERIALS,
                        "description": "The waste material to look up.",
                    }
                },
                "required": ["material"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_environmental_impact",
            "description": (
                "Estimate the CO2 saved by recycling a given weight (in kilograms) of a "
                "material instead of sending it to landfill. Call this when the user asks "
                "about environmental impact, CO2, or 'how much does recycling X help'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "material": {
                        "type": "string",
                        "enum": VALID_MATERIALS,
                        "description": "The waste material.",
                    },
                    "weight_kg": {
                        "type": "number",
                        "description": "Weight in kg. Assume 0.05 if the user doesn't specify.",
                    },
                },
                "required": ["material", "weight_kg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_recyclability",
            "description": (
                "Quickly check whether a material is accepted by standard curbside "
                "recycling (returns true/false)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "material": {
                        "type": "string",
                        "enum": VALID_MATERIALS,
                        "description": "The waste material to check.",
                    }
                },
                "required": ["material"],
            },
        },
    },
]


def execute_tool(name: str, arguments: str | dict) -> dict:
    """Dispatch a tool call by name with JSON (or dict) arguments."""
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'."}

    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON arguments for tool '{name}'."}

    try:
        return fn(**arguments)
    except TypeError as exc:
        return {"error": f"Bad arguments for tool '{name}': {exc}"}
