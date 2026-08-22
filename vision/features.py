import math

import numpy as np
import cv2

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
    footprint at this point, when one is available. A roof many times
    larger or smaller than the actual building here means the prompt point
    almost certainly landed on the wrong surface (lawn, road, neighbour's
    lot) rather than the roof - this is a much stronger signal than mask
    shape alone.

    Bounds are loose (0.25x-6.5x) on purpose: OSM building outlines are
    crowdsourced and often significantly undersized relative to the true
    roof (eave overhang, additions not re-surveyed). Confirmed directly
    against real imagery across multiple demo addresses: 3.6x, 3.8x, and
    5.6x mismatches were all genuinely correct, tightly-bounded roof
    segmentations, not bugs - OSM was just outdated. This only needs to
    catch gross errors (seen in practice: a lawn mis-segmented at ~32x)."""
    if osm_target_area_m2 is None or osm_target_area_m2 <= 0:
        return True
    ratio = roof_area_m2 / osm_target_area_m2
    return 0.25 <= ratio <= 6.5


def nearest_structure_m(osm_value: float = None) -> float:
    """Distance to nearest structure, from OSM footprints when available."""
    return osm_value if osm_value is not None else config.DEFAULT_NEAREST_STRUCTURE_M


_MAX_ROOF_TO_LOT_RATIO = 0.55  # a roof rarely covers more than ~55% of a suburban lot


def lot_area_m2(osm_target_area_m2: float = None, roof_area_m2: float = None) -> float:
    """Lot size estimate. OSM has no cadastral parcel data, so this is a
    footprint-based heuristic even when the building footprint itself is
    real - and that footprint can be outdated/undersized (a since-built
    addition not yet re-surveyed, confirmed directly in testing). When a
    confidently-measured roof would exceed this estimate, that's a sign
    the lot estimate is too small, not that the roof is wrong - floor the
    lot estimate at a plausible minimum for that roof instead of silently
    presenting a lot smaller than the house sitting on it."""
    if osm_target_area_m2 is not None:
        estimate = osm_target_area_m2 * _LOT_TO_FOOTPRINT_RATIO
    else:
        estimate = config.DEFAULT_LOT_AREA_M2

    if roof_area_m2 is not None:
        estimate = max(estimate, roof_area_m2 / _MAX_ROOF_TO_LOT_RATIO)

    return round(estimate, 1)


def _dilate_by_radius_m(mask: np.ndarray, radius_m: float, m_per_px: float) -> np.ndarray:
    radius_px = max(1, int(round(radius_m / m_per_px)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius_px + 1, 2 * radius_px + 1))
    return cv2.dilate(mask.astype(np.uint8), kernel).astype(bool)


# Suburban lots are narrow and deep, not round. Side yards are genuinely
# tight - nearest_structure_m across the demo set comes back 1.3-4.1m - so
# the region should barely clear the house sideways, while front and back
# yards absorb most of the lot's area. 3m sideways is chosen to still
# contain a driveway running alongside the house (driveways are ~3-4m
# wide); the front/back cap keeps a large lot-area estimate from pushing
# the region out into the public road, where the asphalt would read as
# this property's impervious surface.
_LOT_SIDE_MARGIN_M = 3.0
_LOT_END_MARGIN_M = 12.0


def lot_region_mask(roof_mask: np.ndarray, lot_area_m2_val: float, m_per_px: float) -> np.ndarray:
    """Approximate the lot as an oriented rectangle around the house.

    There's no real parcel polygon available (OSM has no cadastral data),
    so this is a heuristic either way - but the shape of the heuristic
    matters. A circle sized to match the lot area has to reach a long way
    in *every* direction to cover that area, which pushes it deep into the
    neighbours on both sides; their grey roofs then land inside "this
    property" and get counted as its impervious surface, which is exactly
    the failure this replaces.

    Real suburban lots are narrow across the frontage and deep front to
    back, and the house is aligned to them. So take the roof's own
    orientation (via its minimum-area rectangle), clear it only narrowly
    on the sides, and extend front-to-back to make up the lot area. That
    keeps the region on this property instead of the neighbours'.

    Falls back to the circular buffer when there's no roof mask to take an
    orientation from."""
    mask_u8 = roof_mask.astype(np.uint8)
    if not roof_mask.any():
        return _dilate_by_radius_m(roof_mask, math.sqrt(lot_area_m2_val / math.pi), m_per_px)

    contours = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    largest = max(contours, key=cv2.contourArea)
    centre, (w_px, h_px), angle = cv2.minAreaRect(largest)

    short_m, long_m = sorted((w_px * m_per_px, h_px * m_per_px))
    lot_short_m = short_m + 2 * _LOT_SIDE_MARGIN_M
    # Depth makes up whatever area is left, but never less than the house
    # itself and never more than a plausible front+back yard beyond it.
    lot_long_m = min(max(lot_area_m2_val / lot_short_m, long_m), long_m + 2 * _LOT_END_MARGIN_M)

    # Map the short/long pair back onto the rect's own (width, height) axes.
    if w_px <= h_px:
        size_px = (lot_short_m / m_per_px, lot_long_m / m_per_px)
    else:
        size_px = (lot_long_m / m_per_px, lot_short_m / m_per_px)

    lot = np.zeros(roof_mask.shape[:2], dtype=np.uint8)
    box = cv2.boxPoints((centre, size_px, angle)).astype(np.int32)
    cv2.fillPoly(lot, [box], 1)
    # The rectangle is built around the roof's minAreaRect, which a concave
    # or L-shaped roof can poke outside of - union it back in so the lot
    # always contains the whole house.
    return lot.astype(bool) | roof_mask


def within_distance_ring(roof_mask: np.ndarray, distance_m: float, m_per_px: float) -> np.ndarray:
    """Ring-shaped region within `distance_m` of the roof edge, excluding
    the roof itself. Used for e.g. 'canopy within 5m of the structure'."""
    buffered = _dilate_by_radius_m(roof_mask, distance_m, m_per_px)
    return buffered & ~roof_mask


def rasterize_local_polygons(polygons_m: list, image_shape: tuple, m_per_px: float) -> np.ndarray:
    """Neighbouring buildings' OSM footprints (local metre coords, origin at
    the query point) -> a pixel mask, so they can be excluded from the
    impervious-surface mask. Without this, a neighbour's grey rooftop reads
    as pavement under the HSV threshold, the same colour confusion problem
    canopy-vs-lawn had."""
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    if not polygons_m:
        return mask.astype(bool)

    cy, cx = image_shape[0] / 2.0, image_shape[1] / 2.0
    for poly in polygons_m:
        pts = np.array(
            [[cx + x / m_per_px, cy - y / m_per_px] for x, y in poly],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, [pts], 1)
    return mask.astype(bool)


def pct_within_region(feature_mask: np.ndarray, region_mask: np.ndarray) -> float:
    region_px = region_mask.sum()
    if region_px == 0:
        return 0.0
    overlap = np.logical_and(feature_mask, region_mask).sum()
    return 100.0 * float(overlap) / float(region_px)
