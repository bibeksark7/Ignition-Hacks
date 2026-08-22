import numpy as np

from . import geocode, imagery, segmentation, features, footprints, valuation

# NOTE: vision/scoring.py computes a rough risk score independently and is
# kept only as an internal sanity-check tool (see debug_visualize.py) - it
# is NOT part of this contract. Workstream 02 owns the official risk_score,
# since it's derived from the same multiplier that drives the price, which
# guarantees the score and the premium can never contradict each other.


def _confidence(is_precise_match: bool, roof_plausible: bool, roof_matches_footprint: bool) -> float:
    if not roof_plausible or not roof_matches_footprint:
        return 0.15
    return 0.75 if is_precise_match else 0.35


def analyze(address: str, region_key: str = None) -> dict:
    """Address -> full Contract A payload."""
    loc = geocode.geocode(address)
    return analyze_at(
        loc["lat"], loc["lon"],
        region_key=region_key or loc["region_key"],
        address_precision=loc["address_precision"],
        is_precise_match=loc["is_precise_match"],
    )


def analyze_with_images(address: str, region_key: str = None) -> tuple:
    """Address -> (Contract A payload, images dict). See analyze_at_with_images."""
    loc = geocode.geocode(address)
    return analyze_at_with_images(
        loc["lat"], loc["lon"],
        region_key=region_key or loc["region_key"],
        address_precision=loc["address_precision"],
        is_precise_match=loc["is_precise_match"],
    )


def analyze_at(
    lat: float, lon: float, region_key: str = "default",
    address_precision: str = "point", is_precise_match: bool = True,
) -> dict:
    """(lat, lon) -> Contract A payload only (no images). Used directly
    after a pin-confirm step, where the user-corrected coordinates are
    already trusted and shouldn't be re-geocoded."""
    result, _images = analyze_at_with_images(
        lat, lon, region_key=region_key,
        address_precision=address_precision, is_precise_match=is_precise_match,
    )
    return result


def analyze_at_with_images(
    lat: float, lon: float, region_key: str = "default",
    address_precision: str = "point", is_precise_match: bool = True,
) -> tuple:
    """Same as analyze_at, but also returns the raw tile image and masks
    for the API layer to encode as PNGs - kept separate from Contract A
    itself, which only Workstream 02 consumes and has no use for pixels."""
    tile = imagery.fetch_tile(lat, lon)
    osm = footprints.query_buildings(lat, lon)

    image = np.array(tile["image"])
    center = (image.shape[1] // 2, image.shape[0] // 2)
    m_per_px = features.meters_per_pixel(lat, tile["zoom"], tile["retina"])

    # Prefer the real OSM building centroid over the raw geocoded point as
    # SAM's prompt point, when available: a geocoder's address point often
    # lands on the yard/driveway/street rather than the structure itself
    # (confirmed in testing - a "place" node landed squarely on a front
    # lawn), while an OSM building footprint is real surveyed geometry.
    # Falls back to the tile centre when OSM has no coverage here.
    prompt_point = center
    prompt_bbox = None
    if osm["target_centroid_m"] is not None:
        cx_m, cy_m = osm["target_centroid_m"]
        px = int(round(center[0] + cx_m / m_per_px))
        py = int(round(center[1] - cy_m / m_per_px))
        if 0 <= px < image.shape[1] and 0 <= py < image.shape[0]:
            prompt_point = (px, py)

    if osm["target_bbox_m"] is not None:
        # SAM treats the box as a fairly hard spatial constraint (confirmed
        # in testing - it clipped a roof exactly at the box edge), so the
        # pad needs to be generous enough to survive an outdated/undersized
        # OSM footprint (seen directly: one property's real roof was ~3.7x
        # OSM's mapped area, presumably a since-built addition), not just
        # normal eave overhang.
        pad_m = 8.0
        min_x, min_y, max_x, max_y = osm["target_bbox_m"]
        x1 = int(round(center[0] + (min_x - pad_m) / m_per_px))
        y1 = int(round(center[1] - (max_y + pad_m) / m_per_px))
        x2 = int(round(center[0] + (max_x + pad_m) / m_per_px))
        y2 = int(round(center[1] - (min_y - pad_m) / m_per_px))
        x1, x2 = max(0, min(x1, x2)), min(image.shape[1], max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(image.shape[0], max(y1, y2))
        if x2 > x1 and y2 > y1:
            prompt_bbox = (x1, y1, x2, y2)

    roof_mask = segmentation.segment_roof(image, prompt_point, prompt_bbox)
    canopy_mask = segmentation.segment_canopy(image)
    roof_plausible = features.roof_segmentation_is_plausible(roof_mask)

    neighbor_buildings_mask = features.rasterize_local_polygons(
        osm["other_building_polygons_m"], image.shape, m_per_px
    )
    impervious_mask = segmentation.segment_impervious(
        image, exclude_mask=roof_mask | neighbor_buildings_mask, m_per_px=m_per_px
    )

    roof_area_m2 = features.mask_area_m2(roof_mask, m_per_px)
    lot_area_m2 = features.lot_area_m2(osm["target_area_m2"], roof_area_m2)
    roof_matches_footprint = features.roof_matches_footprint(roof_area_m2, osm["target_area_m2"])

    lot_mask = features.lot_region_mask(roof_mask, lot_area_m2, m_per_px)
    five_m_ring = features.within_distance_ring(roof_mask, 5.0, m_per_px)
    canopy_within_5m_pct = features.pct_within_region(canopy_mask, five_m_ring)
    impervious_pct = features.pct_within_region(impervious_mask, lot_mask)

    feature_dict = {
        "lat": lat,
        "lon": lon,
        "imagery_date": tile["imagery_date"],
        "imagery_date_known": tile["imagery_date"] is not None,
        "zoom": tile["zoom"],
        "roof_area_m2": round(roof_area_m2, 1),
        "roof_material": features.guess_roof_material(image, roof_mask),
        "roof_damage_score": features.roof_damage_score(image, roof_mask),
        "canopy_overlap_pct": round(features.mask_overlap_pct(roof_mask, canopy_mask), 1),
        "canopy_within_5m_pct": round(canopy_within_5m_pct, 1),
        "impervious_pct": round(impervious_pct, 1),
        "lot_area_m2": lot_area_m2,
        "nearest_structure_m": features.nearest_structure_m(osm["nearest_structure_m"]),
        "address_precision": address_precision,
        "roof_segmentation_plausible": roof_plausible and roof_matches_footprint,
        "confidence": _confidence(is_precise_match, roof_plausible, roof_matches_footprint),
    }

    value = valuation.estimate_value(
        feature_dict["roof_area_m2"], feature_dict["roof_damage_score"], region_key
    )

    result = {**feature_dict, **value}
    # Display masks are clipped to the property, because that's what the
    # numbers above actually measure: impervious_pct is the paved share of
    # THIS lot, not of the whole tile, and canopy is scored over/near THIS
    # structure. Shipping the raw whole-tile masks meant the UI painted the
    # public road and the neighbours' yards - showing the user something
    # the pipeline never counted, which read as "the CV is wrong" when the
    # measurements were fine. Keep display and measurement on the same
    # region so the overlay is an honest picture of the analysis.
    images = {
        "tile": image,
        "roof_mask": roof_mask,
        "canopy_mask": canopy_mask & lot_mask,
        "impervious_mask": impervious_mask & lot_mask,
    }
    return result, images
