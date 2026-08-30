"""Approximate environmental impact facts per waste category.

Figures are illustrative, rounded, industry-ballpark estimates commonly cited by
recycling/environmental organizations (EPA, WRAP, industry LCA studies) — they are
meant to give the user a sense of *why* recycling a category matters, not to serve
as precise or authoritative per-item measurements.

`resale_pkr_per_kg` / `resale_note` are a second, separate set of illustrative
figures: a rough sense of what a Karachi/Pakistan-area "kabaria" (informal
scrap/waste-material buyer) might pay per kg in that local resale economy, in
Pakistani Rupees. These are ballparks that vary by dealer, city, material
cleanliness, and day-to-day scrap-market conditions — not authoritative pricing.
`None` means there is typically no local resale market for that material at all.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImpactFact:
    headline: str
    co2_saved_per_kg: float | None  # kg CO2e saved per kg recycled vs. virgin production
    energy_saved_pct: int | None  # % energy saved vs. producing from raw material
    fact: str
    resale_pkr_per_kg: float | None = None  # rough kabaria/scrap-dealer rate, PKR/kg
    resale_note: str = ""  # short explanation, especially for materials with no market


IMPACT_FACTS: dict[str, ImpactFact] = {
    "cardboard": ImpactFact(
        headline="Saves trees and landfill space",
        co2_saved_per_kg=0.7,
        energy_saved_pct=24,
        fact="Recycling cardboard uses about a quarter less energy than making it "
        "from raw wood pulp, and keeps bulky material out of landfills.",
        resale_pkr_per_kg=10.0,
        resale_note="Sold as 'raddi' (waste paper) by weight to a kabaria or paper "
        "recycler — one of the more reliably resalable materials locally, provided "
        "it's kept clean and dry.",
    ),
    "glass": ImpactFact(
        headline="Infinitely recyclable, no quality loss",
        co2_saved_per_kg=0.3,
        energy_saved_pct=30,
        fact="Glass can be recycled endlessly without degrading — recycled glass "
        "('cullet') melts at a lower temperature, cutting furnace energy use by "
        "around 30%.",
        resale_pkr_per_kg=None,
        resale_note="Most kabarias won't take glass at all — it's heavy relative to "
        "its value and breaks easily in transport, so there's essentially no local "
        "resale market for it (aside from a few shop-returnable bottle types).",
    ),
    "metal": ImpactFact(
        headline="One of the biggest energy savers",
        co2_saved_per_kg=9.0,
        energy_saved_pct=95,
        fact="Recycling aluminum uses about 95% less energy than producing it from "
        "raw bauxite ore — one of the largest environmental wins of any household "
        "recyclable.",
        resale_pkr_per_kg=150.0,
        resale_note="Usually the most valuable household material to a kabaria. "
        "Aluminum cans alone can fetch roughly 200-350 PKR/kg, while steel/tin cans "
        "are worth much less (roughly 30-60 PKR/kg) — 150 PKR/kg is a rough blended "
        "midpoint across a typical mixed-metal household load.",
    ),
    "paper": ImpactFact(
        headline="Saves water, trees, and landfill space",
        co2_saved_per_kg=1.0,
        energy_saved_pct=60,
        fact="Recycling paper uses roughly 60% less energy and significantly less "
        "water than producing new paper from raw timber.",
        resale_pkr_per_kg=12.0,
        resale_note="Sold as 'raddi' alongside cardboard — newspaper tends to fetch "
        "a slightly better rate than mixed office paper.",
    ),
    "plastic": ImpactFact(
        headline="Cuts fossil-fuel demand",
        co2_saved_per_kg=1.5,
        energy_saved_pct=66,
        fact="Recycled plastic (rPET) requires around two-thirds less energy to "
        "produce than virgin plastic made from crude oil.",
        resale_pkr_per_kg=25.0,
        resale_note="Clean PET bottles are the most reliably resalable plastic "
        "locally; dirty, mixed, or non-PET plastic is often worth much less or has "
        "no buyer at all.",
    ),
    "trash": ImpactFact(
        headline="Headed for landfill or incineration",
        co2_saved_per_kg=None,
        energy_saved_pct=None,
        fact="This item isn't accepted by standard recycling streams. Some "
        "materials (like plastic) can take hundreds of years to decompose in a "
        "landfill — check if it qualifies for a special disposal stream (e-waste, "
        "batteries, hazardous waste) before binning it as general trash.",
        resale_pkr_per_kg=None,
        resale_note="No local resale market — this goes to general waste (or a "
        "special disposal stream for hazardous items like batteries/e-waste).",
    ),
}


def get_impact(label: str) -> ImpactFact | None:
    return IMPACT_FACTS.get(label)
