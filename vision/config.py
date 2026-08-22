import os
from dotenv import load_dotenv

load_dotenv()

MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")

DEFAULT_ZOOM = 19
TILE_SIZE = 512  # @2x retina tile from Mapbox
RETINA = True

# Fallback lot area (m^2) used when a parcel boundary isn't available.
DEFAULT_LOT_AREA_M2 = 600.0

# Fallback distance to nearest structure (m) when no building footprint
# dataset is wired up. Used to keep the pipeline runnable end-to-end.
DEFAULT_NEAREST_STRUCTURE_M = 9.0

# Very rough $/m2 benchmarks for the value heuristic, keyed by a coarse
# region string. Replace/extend with real comps if time allows.
NEIGHBORHOOD_PRICE_PER_M2 = {
    "default": 3800.0,
    "toronto_on": 6200.0,
    "ottawa_on": 4100.0,
    "milton_on": 4600.0,
}
