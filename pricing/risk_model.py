"""Feature measurements + location hazards -> per-peril risk multiplier and score."""

from typing import Any, Dict, List, Tuple

from . import config
from .hazards import HazardFactors


def _pct_to_frac(value: float) -> float:
    return max(0.0, min(1.0, value / 100.0))


def _spacing_riskiness(nearest_structure_m: float) -> float:
    frac = (config.SPACING_RISK_THRESHOLD_M - nearest_structure_m) / config.SPACING_RISK_THRESHOLD_M
    return max(0.0, min(1.0, frac))


def compute_feature_riskiness(features: Dict[str, Any], hazards: HazardFactors) -> Dict[str, float]:
    """Maps every risk factor referenced in config.RISK_WEIGHTS to a 0-1 riskiness value."""
    material = features["roof_material"]
    return {
        "canopy_overlap_pct": _pct_to_frac(features["canopy_overlap_pct"]),
        "canopy_within_5m_pct": _pct_to_frac(features["canopy_within_5m_pct"]),
        "impervious_pct": _pct_to_frac(features["impervious_pct"]),
        "roof_damage_score": max(0.0, min(1.0, features["roof_damage_score"])),
        "nearest_structure_spacing": _spacing_riskiness(features["nearest_structure_m"]),
        "roof_material_fire_risk": config.ROOF_MATERIAL_FIRE_RISK.get(material, config.DEFAULT_ROOF_MATERIAL_RISK),
        "roof_material_wind_risk": config.ROOF_MATERIAL_WIND_RISK.get(material, config.DEFAULT_ROOF_MATERIAL_RISK),
        "hazard_wildfire": hazards.wildfire,
        "hazard_flood": hazards.flood,
        "hazard_wind_hail": hazards.wind_hail,
    }


def compute_multiplier(peril: str, riskiness: Dict[str, float]) -> float:
    weights = config.RISK_WEIGHTS[peril]
    raw = 1.0 + sum(weight * riskiness[key] for key, weight in weights.items())
    return max(config.MULTIPLIER_MIN, min(config.MULTIPLIER_MAX, raw))


def compute_multipliers(features: Dict[str, Any], hazards: HazardFactors) -> Dict[str, float]:
    riskiness = compute_feature_riskiness(features, hazards)
    return {peril: compute_multiplier(peril, riskiness) for peril in config.RISK_WEIGHTS}


def score_from_multiplier(multiplier: float) -> float:
    safe, risky = config.SCORE_SAFE_MULTIPLIER, config.SCORE_RISKY_MULTIPLIER
    frac = (multiplier - safe) / (risky - safe)
    score = 100.0 - frac * 100.0
    return max(0.0, min(100.0, score))


def grade_from_score(score: float) -> str:
    for threshold, grade in config.GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def compute_risk_scores(multipliers: Dict[str, float]) -> Dict[str, Any]:
    peril_scores = {peril: score_from_multiplier(m) for peril, m in multipliers.items()}
    overall = sum(config.OVERALL_SCORE_WEIGHTS[peril] * s for peril, s in peril_scores.items())
    return {
        "overall": round(overall, 1),
        "grade": grade_from_score(overall),
        "perils": {peril: round(s, 1) for peril, s in peril_scores.items()},
    }


_PLAIN_LANGUAGE = {
    "canopy_overlap_pct": lambda f, h: f"Trees cover about {f['canopy_overlap_pct']:.0f}% of your roof, raising fire risk",
    "canopy_within_5m_pct": lambda f, h: f"{f['canopy_within_5m_pct']:.0f}% of the area within 5m of your home has vegetation, a wildfire ember risk",
    "nearest_structure_spacing": lambda f, h: f"Your home is only {f['nearest_structure_m']:.1f}m from the nearest structure, which lets fire spread more easily",
    "roof_material_fire_risk": lambda f, h: f"Your {f['roof_material'].replace('_', ' ')} roof is more flammable than average",
    "roof_material_wind_risk": lambda f, h: f"Your {f['roof_material'].replace('_', ' ')} roof is more vulnerable to wind and hail",
    "impervious_pct": lambda f, h: f"About {f['impervious_pct']:.0f}% of your lot is paved, so stormwater has nowhere to soak in",
    "roof_damage_score": lambda f, h: "Visible roof wear increases water and wind/hail risk",
    "hazard_wildfire": lambda f, h: "Your area has elevated regional wildfire exposure",
    "hazard_flood": lambda f, h: "Your area has elevated regional flood exposure",
    "hazard_wind_hail": lambda f, h: "Your area has elevated regional wind/hail exposure",
}


def top_drivers(
    peril: str, features: Dict[str, Any], hazards: HazardFactors, riskiness: Dict[str, float], limit: int = 3
) -> List[Dict[str, Any]]:
    weights = config.RISK_WEIGHTS[peril]
    contributions: List[Tuple[str, float]] = [(key, weight * riskiness[key]) for key, weight in weights.items()]
    contributions.sort(key=lambda item: item[1], reverse=True)
    drivers = []
    for key, effect in contributions[:limit]:
        drivers.append(
            {
                "feature": key,
                "effect": round(effect, 4),
                "plain_language": _PLAIN_LANGUAGE[key](features, hazards),
            }
        )
    return drivers
