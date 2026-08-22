from . import config

_LIVABLE_AREA_MULTIPLIER = 1.6  # rough footprint->livable-area factor for a 2-storey home


def estimate_value(roof_area_m2: float, roof_damage_score: float, region_key: str = "default") -> dict:
    """Rough heuristic: footprint size x neighborhood $/m2, condition-adjusted.

    Explicitly low-confidence - not an appraisal or AVM. Disclosed as such
    in the returned payload so the frontend can label it accordingly.
    """
    price_per_m2 = config.NEIGHBORHOOD_PRICE_PER_M2.get(
        region_key, config.NEIGHBORHOOD_PRICE_PER_M2["default"]
    )
    livable_area_m2 = roof_area_m2 * _LIVABLE_AREA_MULTIPLIER
    condition_adjustment = 1.0 - (0.15 * roof_damage_score)

    value = livable_area_m2 * price_per_m2 * condition_adjustment

    return {
        "estimated_value": round(value, -3),  # round to nearest $1,000
        "value_basis": "heuristic: footprint x neighborhood $/m2, condition-adjusted",
        "value_confidence": "low",
    }
