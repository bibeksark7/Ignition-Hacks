"""Location hazard lookup.

Placeholder implementation using known catastrophe-history hotspots (named
after the events cited in the pitch) plus coarse provincial bounding boxes as
a fallback — a stand-in for the real Canada Flood Map Inventory and CWFIS
wildfire datamart. The function signature is the stable contract — swap the
body for real dataset lookups without touching any caller.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class HazardFactors:
    flood: float      # 0-1, higher = more flood-prone
    wildfire: float    # 0-1, higher = more wildfire-prone
    wind_hail: float   # 0-1, higher = more storm-prone


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r_km * math.asin(math.sqrt(a))


# Named after the catastrophe events cited in the pitch — checked first, by
# distance, so a demo address near one of these gets a realistic sharp signal
# instead of the coarse provincial average. (name, lat, lon, radius_km, factors)
_HOTSPOTS: List[Tuple[str, float, float, float, HazardFactors]] = [
    ("Jasper, AB — 2024 wildfire", 52.8734, -118.0814, 60, HazardFactors(flood=0.15, wildfire=0.90, wind_hail=0.20)),
    ("Fort McMurray, AB — 2016 wildfire", 56.7264, -111.3803, 60, HazardFactors(flood=0.20, wildfire=0.92, wind_hail=0.20)),
    ("BC Interior wildfire belt (Kelowna/Kamloops)", 50.2, -119.5, 120, HazardFactors(flood=0.20, wildfire=0.80, wind_hail=0.20)),
    ("Calgary, AB — hail alley", 51.0447, -114.0719, 40, HazardFactors(flood=0.30, wildfire=0.30, wind_hail=0.75)),
    ("Greater Toronto Area — flood-prone", 43.6532, -79.3832, 60, HazardFactors(flood=0.65, wildfire=0.10, wind_hail=0.35)),
    ("Metro Vancouver — coastal flood", 49.2827, -123.1207, 50, HazardFactors(flood=0.55, wildfire=0.20, wind_hail=0.25)),
    ("Maritimes — hurricane exposure", 44.65, -63.57, 200, HazardFactors(flood=0.40, wildfire=0.15, wind_hail=0.60)),
    ("Winnipeg / Red River Valley, MB — flood-prone", 49.895, -97.138, 80, HazardFactors(flood=0.60, wildfire=0.15, wind_hail=0.45)),
]

# Coarse provincial fallback for anywhere not near a named hotspot.
# (min_lat, max_lat, min_lon, max_lon, factors) — first match wins.
_REGIONS = [
    (49.0, 60.0, -139.0, -114.0, HazardFactors(flood=0.35, wildfire=0.75, wind_hail=0.25)),  # BC interior/north
    (48.0, 60.0, -120.0, -110.0, HazardFactors(flood=0.30, wildfire=0.70, wind_hail=0.30)),  # Alberta
    (41.0, 47.0, -84.0, -74.0, HazardFactors(flood=0.55, wildfire=0.15, wind_hail=0.40)),    # Southern Ontario / GTA
    (44.5, 47.5, -80.0, -74.0, HazardFactors(flood=0.30, wildfire=0.20, wind_hail=0.35)),    # Southern Quebec
    (49.0, 60.0, -110.0, -95.0, HazardFactors(flood=0.35, wildfire=0.35, wind_hail=0.45)),   # Saskatchewan / Manitoba - tornado/hail belt extends here, boreal wildfire fringe
    (43.0, 52.0, -68.0, -52.0, HazardFactors(flood=0.35, wildfire=0.15, wind_hail=0.55)),    # Atlantic Canada (NB/NS/PEI/NL) - hurricane/nor'easter exposure
]

_DEFAULT = HazardFactors(flood=0.30, wildfire=0.25, wind_hail=0.30)


def lookup_hazards(lat: float, lon: float) -> HazardFactors:
    for _name, hlat, hlon, radius_km, factors in _HOTSPOTS:
        if _haversine_km(lat, lon, hlat, hlon) <= radius_km:
            return factors
    for min_lat, max_lat, min_lon, max_lon, factors in _REGIONS:
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return factors
    return _DEFAULT
