"""Location hazard lookup.

Placeholder implementation using coarse regional bounding boxes as a stand-in
for the real Canada Flood Map Inventory and CWFIS wildfire datamart. The
function signature is the stable contract — swap the body for real dataset
lookups without touching any caller.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HazardFactors:
    flood: float      # 0-1, higher = more flood-prone
    wildfire: float    # 0-1, higher = more wildfire-prone
    wind_hail: float   # 0-1, higher = more storm-prone


# (min_lat, max_lat, min_lon, max_lon, factors) — first match wins.
_REGIONS = [
    (49.0, 60.0, -139.0, -114.0, HazardFactors(flood=0.35, wildfire=0.75, wind_hail=0.25)),  # BC interior/north
    (48.0, 60.0, -120.0, -110.0, HazardFactors(flood=0.30, wildfire=0.70, wind_hail=0.30)),  # Alberta
    (41.0, 47.0, -84.0, -74.0, HazardFactors(flood=0.55, wildfire=0.15, wind_hail=0.40)),    # Southern Ontario / GTA
    (44.5, 47.5, -80.0, -74.0, HazardFactors(flood=0.30, wildfire=0.20, wind_hail=0.35)),    # Southern Quebec
]

_DEFAULT = HazardFactors(flood=0.30, wildfire=0.25, wind_hail=0.30)


def lookup_hazards(lat: float, lon: float) -> HazardFactors:
    for min_lat, max_lat, min_lon, max_lon, factors in _REGIONS:
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return factors
    return _DEFAULT
