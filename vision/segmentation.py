import numpy as np
import cv2

_sam_model = None


def _get_sam():
    global _sam_model
    if _sam_model is None:
        from ultralytics import SAM

        _sam_model = SAM("sam_b.pt")
    return _sam_model


# Smaller than any real house, so a mask under this came from a rooftop
# vent, a skylight or a shadow patch rather than a roof.
_DEGENERATE_ROOF_M2 = 25.0
# Half-width of the fallback prompt box. Covers a typical detached or
# semi-detached footprint (the demo set's real OSM footprints run 92-146
# sq m) without reaching so far that SAM prefers the whole terrace.
_FALLBACK_BOX_HALF_M = 10.0


def _mask_from(results) -> np.ndarray:
    return results[0].masks.data[0].cpu().numpy().astype(np.uint8)


def segment_roof(
    image: np.ndarray, point_xy: tuple, bbox_xyxy: tuple = None, m_per_px: float = None
) -> np.ndarray:
    """Roof mask from SAM. A single point prompt is ambiguous for a complex
    multi-plane roof - SAM will happily segment just the one plane or
    shadow patch touching that pixel instead of the whole structure. When
    a real OSM building footprint is available, its bounding box (padded
    for eave overhang) is passed alongside the point - a box prompt biases
    SAM strongly toward "the whole object filling this region" rather than
    a sub-part, which the point prompt alone repeatedly failed at in
    testing. Falls back to point-only when no footprint data exists.

    SAM's raw output also often has small holes around roof vents, ridge
    lines, and shadowed patches - real gaps in an otherwise coherent roof,
    not signal. A morphological close (dilate then erode) bridges those
    without growing the mask's actual outer boundary."""
    model = _get_sam()
    kwargs = {"points": [list(point_xy)], "labels": [1], "verbose": False}
    if bbox_xyxy is not None:
        kwargs["bboxes"] = [list(bbox_xyxy)]
    mask = _mask_from(model(image, **kwargs))

    # With no OSM footprint there's no box to prompt with, and a bare point
    # is weak enough that SAM regularly returns a single roof feature
    # instead of the roof (observed: 3.6 sq m from a point that landed on a
    # vent, on an address that returns 428 sq m when the footprint lookup
    # succeeds). Retrying with a house-sized box around the same point
    # gives SAM the "whole object filling this region" bias the OSM bbox
    # normally provides. Only runs when there was no box and the result is
    # already degenerate, so it cannot change a healthy segmentation.
    if bbox_xyxy is None and m_per_px is not None:
        if mask.sum() * (m_per_px ** 2) < _DEGENERATE_ROOF_M2:
            half_px = _FALLBACK_BOX_HALF_M / m_per_px
            x, y = point_xy
            h, w = image.shape[:2]
            fallback_box = [
                max(0.0, x - half_px), max(0.0, y - half_px),
                min(float(w), x + half_px), min(float(h), y + half_px),
            ]
            retry = _mask_from(model(image, bboxes=[fallback_box],
                                     points=[list(point_xy)], labels=[1], verbose=False))
            if retry.sum() > mask.sum():
                mask = retry

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return closed.astype(bool)


def segment_canopy(image: np.ndarray) -> np.ndarray:
    """Tree canopy via HSV thresholding, distinguished from flat lawn by
    local texture: tree cover has leaf/shadow variance that mowed grass
    doesn't, so a low-variance green region is classified as lawn, not
    canopy - the two carry very different fire risk.

    The raw texture filter fires on individual leaf clusters/shadow gaps,
    which reads as sparse speckles rather than a canopy shape - a real
    tree crown has small gaps in it too, they just shouldn't visually
    fragment the whole thing. A morphological close merges nearby
    speckles into the contiguous canopy patches they're actually part of,
    without touching well-separated trees or expanding onto the lawn.

    Grayscale local variance alone missed large, densely-shaded canopy
    (confirmed on 68A/68B Bexhill Ave: a big uniformly-dark tree mass
    measured local_var ~7, well under the 25.0 threshold, because a dense
    crown in even shade is smoother pixel-to-pixel than a sunlit one -
    despite clearly reading as foliage by hue/saturation/value). A plain
    OR with saturation-channel variance catches it, but also raises the
    false-positive rate on sunlit lawn (mowing-stripe edges have some
    saturation variance too) - confirmed on 84 Bexhill Ave's front lawn.
    Gating that second signal to only fire where brightness (V) is below
    70 fixes this cleanly: the missed tree mass is dim (V ~73, self-shaded
    crown), while every false-positive lawn sample was bright, sunlit
    grass (V ~105-111) that the gate excludes outright. Verified against
    all 8 demo addresses - the gate holds the lawn false-positive rate at
    its original baseline (~26%, effectively unchanged) while recovering
    the previously-missed tree mass (2.5% -> ~26% textured coverage)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([25, 40, 30])
    upper = np.array([95, 255, 255])
    green_mask = cv2.inRange(hsv, lower, upper).astype(bool)

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gray_mean = cv2.blur(gray, (9, 9))
    gray_var = cv2.blur((gray - gray_mean) ** 2, (9, 9))

    value = hsv[:, :, 2].astype(np.float32)
    sat = hsv[:, :, 1].astype(np.float32)
    sat_mean = cv2.blur(sat, (9, 9))
    sat_var = cv2.blur((sat - sat_mean) ** 2, (9, 9))

    shaded_texture = (sat_var > 12.0) & (value < 70.0)
    textured = (gray_var > 25.0) | shaded_texture

    canopy = (green_mask & textured).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    closed = cv2.morphologyEx(canopy, cv2.MORPH_CLOSE, kernel)
    return closed.astype(bool)


def segment_pool(image: np.ndarray) -> np.ndarray:
    """Swimming pool water: saturated blue/turquoise, distinct from the
    low-saturation grey of pavement/concrete. Called out explicitly in
    the project brief as a naive-thresholding trap - without this, pale
    or sun-glared pool water reads as impervious pavement."""
    # Saturation bound is lower than a strict "pool blue" to also catch
    # pale/sun-glared water (chlorine-blue lap pools often wash out nearly
    # white) - hue stays tightly bounded to cyan/blue since that's what
    # keeps this from also matching grey pavement.
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([85, 20, 120])
    upper = np.array([130, 255, 255])
    return cv2.inRange(hsv, lower, upper).astype(bool)


_MIN_BUILDING_SHORT_SIDE_M = 6.0  # driveways/walkways are narrower than this


def _drop_building_width_regions(mask: np.ndarray, m_per_px: float) -> np.ndarray:
    """Remove parts of the paving mask that are too wide to be paving.

    A grey roof and grey asphalt are nearly identical in colour, so colour
    alone can't separate them - which is why neighbouring houses were being
    painted as impervious surface. Geometry can: a driveway or walkway is
    narrow (~3-4m across) however long it runs, while a house is wide in
    both directions. This needs no OSM footprint for the neighbour, which
    matters because OSM often hasn't mapped them.

    Judged locally by width rather than per connected blob: the driveway
    usually touches the neighbouring roof through a shared grey edge, so
    the whole neighbourhood's paving is often one connected component -
    scoring that component as a unit threw the driveway away along with
    the roofs. A morphological opening keeps only the parts of the mask
    wide enough to contain a building-sized disc, which is exactly the
    "too wide to be paving" test, applied per-region instead of per-blob.
    """
    width_px = max(1, int(round(_MIN_BUILDING_SHORT_SIDE_M / m_per_px)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (width_px, width_px))
    mask_u8 = mask.astype(np.uint8)

    # Opening keeps only what's wide enough to hold the disc, but that's the
    # eroded *core* of each wide region - left alone it strips the middle of
    # a neighbour's roof and leaves its rim behind. Dilating the core back
    # out and re-intersecting with the original mask recovers the whole
    # region without spilling onto anything that wasn't grey to begin with.
    core = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
    building_width_regions = cv2.bitwise_and(cv2.dilate(core, kernel), mask_u8).astype(bool)
    return mask & ~building_width_regions


_SMOOTH_CLOSE_M = 0.8   # bridge shadow lines, tyre marks, sealant seams
_SMOOTH_OPEN_M = 0.5    # drop isolated speckle
_MIN_PAVING_PATCH_M2 = 2.0  # smaller than any real paved feature


def _smooth(mask: np.ndarray, m_per_px: float) -> np.ndarray:
    """Turn per-pixel colour hits into contiguous paved shapes.

    HSV thresholding classifies each pixel independently, so a driveway
    comes back stippled - shadows, tyre marks, sealant seams and gravel
    texture all punch holes in what a person sees as one flat surface, and
    stray grey pixels scatter across the lawn. Closing bridges the holes,
    opening drops the scatter, and anything left that is smaller than a
    real paved feature is discarded outright.
    """
    def disc(metres):
        px = max(1, int(round(metres / m_per_px)))
        return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))

    m = mask.astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disc(_SMOOTH_CLOSE_M))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, disc(_SMOOTH_OPEN_M))

    min_px = int(round(_MIN_PAVING_PATCH_M2 / (m_per_px ** 2)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros_like(m, dtype=bool)
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] >= min_px:
            keep |= labels == i
    return keep


def segment_impervious(
    image: np.ndarray,
    exclude_mask: np.ndarray = None,
    m_per_px: float = None,
    use_width_filter: bool = True,
) -> np.ndarray:
    """Grey asphalt/concrete via HSV thresholding (low saturation, mid-high
    value). Pools are excluded - see segment_pool - since a pool is not
    pavement, even though naive thresholding often confuses the two.

    Note on the width filter: it was tried as "only apply outside our own
    lot", on the reasoning that the roof is already excluded and the lot
    region no longer reaches next door, so wide grey inside the lot must
    be a patio or parking pad. That is wrong in practice, because the roof
    mask is often incomplete - when SAM catches only part of a roof, or
    the footprint lookup fails and it falls back to a box prompt, the rest
    of the roof is grey, inside the lot, and no longer removed. It painted
    the un-segmented half of a townhouse roof solid blue (440 Pharmacy,
    70.4% impervious) and roof-edge shadow on 84 Bexhill. The width test
    is the only backstop against an incomplete roof mask, so it stays
    unconditional.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([0, 0, 60])
    upper = np.array([180, 40, 210])
    mask = cv2.inRange(hsv, lower, upper).astype(bool)
    mask &= ~segment_pool(image)
    if exclude_mask is not None:
        mask &= ~exclude_mask
    if m_per_px is not None:
        # The width filter is a last resort for when we don't know where the
        # buildings are: it throws away every wide grey region, which takes
        # driveways and parking pads with it and leaves only a halo of thin
        # fragments around the house. When OSM has given us surveyed
        # outlines, the buildings are already excluded properly and this
        # does far more harm than good.
        if use_width_filter:
            mask = _drop_building_width_regions(mask, m_per_px)
        mask = _smooth(mask, m_per_px)
    return mask
