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


_MIN_PAVING_BLOB_M2 = 15.0


def drop_small_paving_fragments(mask: np.ndarray, m_per_px: float) -> np.ndarray:
    """Keep contiguous paved surfaces, drop grey confetti.

    Real paving on a residential lot is a driveway, a patio, a walkway -
    each a single surface of meaningful size. What the colour threshold
    also picks up is small grey scraps: eave shadow, a strip of concrete
    edging, part of a roof the roof mask missed. On the test property the
    driveway and patio came back as 45 and 49 square metres, while five
    further blobs of 1-12 square metres were all noise.

    Dropping blobs below a floor removes those without touching the
    surfaces that actually shed stormwater - which is what impervious_pct
    is meant to measure.
    """
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    keep = np.zeros_like(mask, dtype=bool)
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] * (m_per_px ** 2) >= _MIN_PAVING_BLOB_M2:
            keep |= labels == i
    return keep


_MIN_VEG_WIDTH_M = 2.5


def drop_thin_vegetation(mask: np.ndarray, m_per_px: float) -> np.ndarray:
    """Keep vegetation thick enough to be a tree crown, drop mown strips.

    Lawn and tree crown are indistinguishable here by colour, brightness,
    texture or local contrast - all four were measured against real
    imagery and none separate them (the crown is actually *brighter* than
    the lawn on the test property). Width does separate them once the lot
    region is tight: the grass left inside it runs as narrow strips down
    the side yards, while a crown is a chunky blob several metres across.
    An opening keeps only what's wide enough to hold the disc.

    This is a display/measurement refinement, not tree detection - a wide
    lawn would still come through, and it should, since vegetation near a
    structure is the ember-ignition risk the mitigation catalogue targets.
    """
    width_px = max(1, int(round(_MIN_VEG_WIDTH_M / m_per_px)))
    if width_px % 2 == 0:
        width_px += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (width_px, width_px))
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel).astype(bool)


_PAVING_REACH_M = 4.0


def paving_connected_to_house(mask: np.ndarray, roof_mask: np.ndarray, m_per_px: float) -> np.ndarray:
    """Keep paved surfaces that belong to this house, drop stranded scraps.

    A driveway runs from the house to the street; a patio abuts the back
    wall; a walkway leads to the door. They are all physically continuous
    with the structure. What isn't continuous with it - a slab of kerb or
    sidewalk caught at the far end of the lot rectangle, a corner of the
    neighbour's pad - isn't this property's paving, however grey it is.

    Extending the lot far enough to capture the whole driveway inevitably
    reaches the street, so this is what keeps the pavement out there from
    being counted as the homeowner's runoff.
    """
    if not roof_mask.any():
        return mask
    near_house = _dilate_by_radius_m(roof_mask, _PAVING_REACH_M, m_per_px)
    count, labels, _, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    keep = np.zeros_like(mask, dtype=bool)
    for i in range(1, count):
        blob = labels == i
        if (blob & near_house).any():
            keep |= blob
    return keep


def dominant_blob(mask: np.ndarray) -> np.ndarray:
    """Keep only the largest contiguous region of a mask.

    Used for the vegetation overlay: within the proximity region around a
    house there is usually one vegetation feature that actually matters -
    the tree beside the structure - plus scraps of lawn. Showing the
    dominant mass makes the overlay point at something, instead of tinting
    every green pixel and leaving the viewer to guess which one is the
    hazard. The measured percentages are unaffected; this is display only.
    """
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    if count <= 1:
        return mask
    biggest = max(range(1, count), key=lambda i: stats[i, cv2.CC_STAT_AREA])
    return labels == biggest


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
_LOT_SIDE_MARGIN_M = 2.0
_LOT_END_MARGIN_M = 14.0
# Always reach at least this far past each end of the house, even when the
# lot-area estimate would suggest a shorter rectangle. A driveway runs from
# the house to the street, and the masks shown in the UI are clipped to this
# region - too short a rectangle crops the driveway off mid-way and leaves
# only a halo of paving around the house, which is what it did before.
_LOT_MIN_END_M = 16.0        # paving: reaches the street, so the driveway counts
_VEG_END_M = 10.0             # vegetation: proximity risk, so a shorter reach

# Below this share of the estimated lot, the roof mask is too small to have
# come from a real house (seen in practice: 3.6 m2, a rooftop vent, when the
# OSM lookup failed and SAM fell back to a bare point prompt). Orientation
# taken from a mask that size is meaningless, and the rectangle built around
# it is a sliver - which would make impervious_pct a ratio against almost no
# area at all. Fall back to the circular buffer there: still only as good as
# the roof mask, but at least a plausibly-sized region rather than a divide
# by a sliver.
_MIN_ROOF_SHARE_OF_LOT = 0.10


def lot_region_mask(
    roof_mask: np.ndarray,
    lot_area_m2_val: float,
    m_per_px: float,
    min_end_m: float = None,
) -> np.ndarray:
    """Approximate the lot as an oriented rectangle around the house.

    `min_end_m` overrides how far the rectangle reaches past each end of
    the house. Paving and vegetation want different reaches, and for a
    real reason rather than convenience: every paved surface on the parcel
    sheds stormwater, including the driveway running out to the street, so
    paving is measured over the full depth. Vegetation risk is proximity
    risk - the mitigation is "clear vegetation within 5m of the structure"
    - so counting a lawn at the far end of the lot as this house's fire
    exposure would overstate it. Vegetation therefore uses a shorter reach.

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
    roof_area = mask_area_m2(roof_mask, m_per_px)
    if not roof_mask.any() or roof_area < _MIN_ROOF_SHARE_OF_LOT * lot_area_m2_val:
        return _dilate_by_radius_m(roof_mask, math.sqrt(lot_area_m2_val / math.pi), m_per_px)

    contours = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    largest = max(contours, key=cv2.contourArea)
    centre, (w_px, h_px), angle = cv2.minAreaRect(largest)

    short_m, long_m = sorted((w_px * m_per_px, h_px * m_per_px))
    lot_short_m = short_m + 2 * _LOT_SIDE_MARGIN_M
    # Depth makes up whatever area is left, but never less than the house
    # itself and never more than a plausible front+back yard beyond it.
    end_m = _LOT_MIN_END_M if min_end_m is None else min_end_m
    lot_long_m = min(
        max(lot_area_m2_val / lot_short_m, long_m + 2 * end_m),
        long_m + 2 * max(_LOT_END_MARGIN_M, end_m + 4.0),
    )

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


# Alpha ramp for the canopy overlay, by distance from the structure. Nearer
# canopy is the more dangerous canopy (a branch on the roof is an ignition
# path; a tree 5m away is not), so the overlay ranks severity visually
# instead of painting one flat colour over everything it found.
_CANOPY_ALPHA_BANDS = ((1.5, 0.85), (3.0, 0.65), (5.0, 0.45))


def canopy_display_alpha(
    canopy_mask: np.ndarray, roof_mask: np.ndarray, m_per_px: float
) -> np.ndarray:
    """Canopy overlay as graduated alpha in [0, 1] rather than a flat mask.

    Scoped to exactly what the pipeline actually measures - canopy on or
    within 5m of the structure - so the overlay stays an honest picture of
    the analysis and never paints canopy that no number accounts for."""
    outside = (~roof_mask).astype(np.uint8)
    dist_m = cv2.distanceTransform(outside, cv2.DIST_L2, 5) * m_per_px

    alpha = np.zeros(canopy_mask.shape[:2], dtype=np.float32)
    for edge_m, level in reversed(_CANOPY_ALPHA_BANDS):
        alpha[dist_m <= edge_m] = level
    alpha[roof_mask] = 1.0  # on the structure itself: highest severity

    return alpha * canopy_mask


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
