"""Synthetic Contract A profiles for integration testing before Workstream 01's
real pipeline is wired in. Not real addresses or real measurements — invented
feature values chosen to exercise the high/low ends of the model, so
Workstream 03 has more than one static shape to build against and Workstream 04
has candidate profiles to eventually replace with real analyzed addresses.
"""

from typing import Any, Dict

HIGH_RISK_WILDFIRE_HOUSE: Dict[str, Any] = {
    "lat": 52.8734,
    "lon": -118.0814,  # near Jasper, AB
    "imagery_date": "2024-05-11",
    "zoom": 19,
    "roof_area_m2": 210.0,
    "roof_material": "wood_shake",
    "roof_damage_score": 0.55,
    "canopy_overlap_pct": 78.0,
    "canopy_within_5m_pct": 85.0,
    "impervious_pct": 18.0,
    "lot_area_m2": 950.0,
    "nearest_structure_m": 4.2,
    "confidence": 0.77,
    "estimated_value": 610000,
    "value_basis": "synthetic fixture — not a real estimate",
    "value_confidence": "low",
}

LOW_RISK_HOUSE: Dict[str, Any] = {
    "lat": 43.7,
    "lon": -79.42,  # GTA, but a well-maintained low-risk property
    "imagery_date": "2024-06-02",
    "zoom": 19,
    "roof_area_m2": 160.0,
    "roof_material": "metal",
    "roof_damage_score": 0.03,
    "canopy_overlap_pct": 4.0,
    "canopy_within_5m_pct": 6.0,
    "impervious_pct": 22.0,
    "lot_area_m2": 540.0,
    "nearest_structure_m": 14.0,
    "confidence": 0.9,
    "estimated_value": 890000,
    "value_basis": "synthetic fixture — not a real estimate",
    "value_confidence": "low",
}

MODERATE_FLOOD_HOUSE: Dict[str, Any] = {
    "lat": 43.6532,
    "lon": -79.3832,  # downtown GTA, heavily paved lot
    "imagery_date": "2024-04-18",
    "zoom": 19,
    "roof_area_m2": 145.0,
    "roof_material": "asphalt_shingle",
    "roof_damage_score": 0.30,
    "canopy_overlap_pct": 12.0,
    "canopy_within_5m_pct": 15.0,
    "impervious_pct": 71.0,
    "lot_area_m2": 380.0,
    "nearest_structure_m": 6.5,
    "confidence": 0.85,
    "estimated_value": 1150000,
    "value_basis": "synthetic fixture — not a real estimate",
    "value_confidence": "low",
}

ALL_FIXTURES = {
    "high_risk_wildfire_house": HIGH_RISK_WILDFIRE_HOUSE,
    "low_risk_house": LOW_RISK_HOUSE,
    "moderate_flood_house": MODERATE_FLOOD_HOUSE,
}
