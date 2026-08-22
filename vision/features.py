import math

import numpy as np

from . import config

_ROOF_MATERIAL_CLASSES = ["asphalt_shingle", "metal", "tile", "flat_gravel"]


def meters_per_pixel(lat: float, zoom: int, retina: bool) -> float:
    m_per_px = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
    return m_per_px / 2 if retina else m_per_px


def mask_area_m2(mask: np.ndarray, m_per_px: float) -> float:
    return float(mask.sum()) * (m_per_px ** 2)


def mask_overlap_pct(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    if mask_a.sum() == 0:
        return 0.0
    overlap = np.logical_and(mask_a, mask_b).sum()
    return 100.0 * float(overlap) / float(mask_a.sum())


def guess_roof_material(image: np.ndarray, roof_mask: np.ndarray) -> str:
    pixels = image[roof_mask]
    if pixels.size == 0:
        return _ROOF_MATERIAL_CLASSES[0]

    mean_rgb = pixels.mean(axis=0)
    brightness = mean_rgb.mean()
    saturation = mean_rgb.max() - mean_rgb.min()

    if brightness > 170 and saturation < 20:
        return "metal"
    if brightness < 90:
        return "flat_gravel"
    if saturation > 45:
        return "tile"
    return "asphalt_shingle"


def roof_damage_score(image: np.ndarray, roof_mask: np.ndarray) -> float:
    """0 (pristine) to 1 (heavily damaged) from colour variance/discolouration."""
    pixels = image[roof_mask].astype(np.float32)
    if pixels.shape[0] < 10:
        return 0.0

    std = pixels.std(axis=0).mean()
    score = min(1.0, std / 60.0)
    return round(float(score), 3)


_LOT_TO_FOOTPRINT_RATIO = 2.4  # typical suburban lot / building footprint ratio
_MAX_PLAUSIBLE_ROOF_FRACTION = 0.35  # a discrete roof rarely fills more of the tile than this


def roof_segmentation_is_plausible(mask: np.ndarray) -> bool:
    """A mask covering an implausibly large share of the tile, or touching
    all four edges, is more likely a road/field/lawn the prompt point
    landed on than an actual discrete roof."""
    total_px = mask.shape[0] * mask.shape[1]
    fraction = mask.sum() / total_px
    if fraction > _MAX_PLAUSIBLE_ROOF_FRACTION:
        return False

    touches_top = mask[0, :].any()
    touches_bottom = mask[-1, :].any()
    touches_left = mask[:, 0].any()
    touches_right = mask[:, -1].any()
    if touches_top and touches_bottom and touches_left and touches_right:
        return False

    return True


def roof_matches_footprint(roof_area_m2: float, osm_target_area_m2: float = None) -> bool:
    """Cross-check the segmented roof area against the real OSM building
    footprint at this point, when one is available. A roof several times
    larger or smaller than the actual building here means the prompt point
    almost certainly landed on the wrong surface (lawn, road, neighbour's
    lot) rather than the roof - this is a much stronger signal than mask
    shape alone."""
    if osm_target_area_m2 is None or osm_target_area_m2 <= 0:
        return True
    ratio = roof_area_m2 / osm_target_area_m2
    return 0.3 <= ratio <= 3.0


def nearest_structure_m(osm_value: float = None) -> float:
    """Distance to nearest structure, from OSM footprints when available."""
    return osm_value if osm_value is not None else config.DEFAULT_NEAREST_STRUCTURE_M


def lot_area_m2(osm_target_area_m2: float = None) -> float:
    """Lot size estimate. OSM has no cadastral parcel data, so this is a
    footprint-based heuristic even when the building footprint itself is real."""
    if osm_target_area_m2 is not None:
        return round(osm_target_area_m2 * _LOT_TO_FOOTPRINT_RATIO, 1)
    return config.DEFAULT_LOT_AREA_M2
