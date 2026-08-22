"""Contract A (input, from Workstream 01) validation."""

from typing import Any, Dict, List

REQUIRED_CONTRACT_A_FIELDS: List[str] = [
    "lat",
    "lon",
    "roof_area_m2",
    "roof_material",
    "roof_damage_score",
    "canopy_overlap_pct",
    "canopy_within_5m_pct",
    "impervious_pct",
    "lot_area_m2",
    "nearest_structure_m",
]


def validate_contract_a(data: Dict[str, Any]) -> None:
    missing = [f for f in REQUIRED_CONTRACT_A_FIELDS if f not in data]
    if missing:
        raise ValueError(f"Contract A missing required fields: {missing}")
