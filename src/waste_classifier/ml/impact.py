"""Approximate environmental impact facts per waste category.

Figures are illustrative, rounded, industry-ballpark estimates commonly cited by
recycling/environmental organizations (EPA, WRAP, industry LCA studies) — they are
meant to give the user a sense of *why* recycling a category matters, not to serve
as precise or authoritative per-item measurements.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImpactFact:
    headline: str
    co2_saved_per_kg: float | None  # kg CO2e saved per kg recycled vs. virgin production
    energy_saved_pct: int | None  # % energy saved vs. producing from raw material
    fact: str


IMPACT_FACTS: dict[str, ImpactFact] = {
    "cardboard": ImpactFact(
        headline="Saves trees and landfill space",
        co2_saved_per_kg=0.7,
        energy_saved_pct=24,
        fact="Recycling cardboard uses about a quarter less energy than making it "
        "from raw wood pulp, and keeps bulky material out of landfills.",
    ),
    "glass": ImpactFact(
        headline="Infinitely recyclable, no quality loss",
        co2_saved_per_kg=0.3,
        energy_saved_pct=30,
        fact="Glass can be recycled endlessly without degrading — recycled glass "
        "('cullet') melts at a lower temperature, cutting furnace energy use by "
        "around 30%.",
    ),
    "metal": ImpactFact(
        headline="One of the biggest energy savers",
        co2_saved_per_kg=9.0,
        energy_saved_pct=95,
        fact="Recycling aluminum uses about 95% less energy than producing it from "
        "raw bauxite ore — one of the largest environmental wins of any household "
        "recyclable.",
    ),
    "paper": ImpactFact(
        headline="Saves water, trees, and landfill space",
        co2_saved_per_kg=1.0,
        energy_saved_pct=60,
        fact="Recycling paper uses roughly 60% less energy and significantly less "
        "water than producing new paper from raw timber.",
    ),
    "plastic": ImpactFact(
        headline="Cuts fossil-fuel demand",
        co2_saved_per_kg=1.5,
        energy_saved_pct=66,
        fact="Recycled plastic (rPET) requires around two-thirds less energy to "
        "produce than virgin plastic made from crude oil.",
    ),
    "trash": ImpactFact(
        headline="Headed for landfill or incineration",
        co2_saved_per_kg=None,
        energy_saved_pct=None,
        fact="This item isn't accepted by standard recycling streams. Some "
        "materials (like plastic) can take hundreds of years to decompose in a "
        "landfill — check if it qualifies for a special disposal stream (e-waste, "
        "batteries, hazardous waste) before binning it as general trash.",
    ),
}


def get_impact(label: str) -> ImpactFact | None:
    return IMPACT_FACTS.get(label)
