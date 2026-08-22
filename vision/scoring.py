def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def fire_score(features: dict) -> float:
    """Higher = riskier. Driven by canopy over/near roof and structure spacing."""
    canopy_overlap = features["canopy_overlap_pct"]
    canopy_near = features["canopy_within_5m_pct"]
    spacing = features["nearest_structure_m"]
    damage = features["roof_damage_score"] * 100

    spacing_risk = _clip(100 - spacing * 6)  # closer neighbours = higher risk

    score = (
        0.35 * canopy_overlap
        + 0.25 * canopy_near
        + 0.25 * spacing_risk
        + 0.15 * damage
    )
    return round(_clip(score), 1)


def water_score(features: dict) -> float:
    """Higher = riskier. Driven by impervious surface ratio and roof condition."""
    impervious = features["impervious_pct"]
    damage = features["roof_damage_score"] * 100

    score = 0.75 * impervious + 0.25 * damage
    return round(_clip(score), 1)


def wind_hail_score(features: dict) -> float:
    """Higher = riskier. Roof material and condition are the main levers here."""
    material_risk = {
        "metal": 15,
        "tile": 35,
        "asphalt_shingle": 55,
        "flat_gravel": 65,
    }.get(features["roof_material"], 50)
    damage = features["roof_damage_score"] * 100

    score = 0.6 * material_risk + 0.4 * damage
    return round(_clip(score), 1)


def top_driver(features: dict, peril: str) -> str:
    drivers = {
        "fire": ["canopy_overlap_pct", "canopy_within_5m_pct", "nearest_structure_m"],
        "water": ["impervious_pct"],
        "wind_hail": ["roof_material", "roof_damage_score"],
    }[peril]
    return drivers[0]


def compute_risk_score(features: dict) -> dict:
    perils = {
        "fire": fire_score(features),
        "water": water_score(features),
        "wind_hail": wind_hail_score(features),
    }
    overall = round(sum(perils.values()) / len(perils), 1)

    breakdown = [
        {"peril": peril, "score": score, "top_driver": top_driver(features, peril)}
        for peril, score in perils.items()
    ]
    return {"risk_score": overall, "risk_score_breakdown": breakdown}
