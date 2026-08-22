import numpy as np

from . import geocode, imagery, segmentation, features, footprints, valuation

# NOTE: vision/scoring.py computes a rough risk score independently and is
# kept only as an internal sanity-check tool (see debug_visualize.py) - it
# is NOT part of this contract. Workstream 02 owns the official risk_score,
# since it's derived from the same multiplier that drives the price, which
# guarantees the score and the premium can never contradict each other.


def _confidence(
    is_precise_match: bool,
    roof_plausible: bool,
    roof_matches_footprint: bool,
    footprint_available: bool = True,
) -> float:
    """Confidence in this analysis, 0-1.

    `footprint_available` matters more than it looks. When OSM has no
    footprint here, roof_matches_footprint() has nothing to compare against
    and returns True - so the cross-check silently passes at exactly the
    moment it can't actually check anything. That combination has already
    reported a 3.6 sq m mask (a rooftop vent, segmented from a bare point
    prompt after the Overpass lookup failed) at full 0.75 confidence, with
    nothing downstream aware the number was meaningless. Missing footprint
    data is genuinely less certain, so it caps out below the pricing
    engine's low-confidence threshold and surfaces a warning in the UI
    rather than passing as a solid result.
    """
    if not roof_plausible or not roof_matches_footprint:
        return 0.15
    if not footprint_available:
        return 0.35
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

    roof_mask = segmentation.segment_roof(image, prompt_point, prompt_bbox, m_per_px=m_per_px)
    canopy_mask = segmentation.segment_canopy(image)
    roof_plausible = features.roof_segmentation_is_plausible(roof_mask)

    # Every building OSM knows about here, the target included. Subtracting
    # the target's own surveyed outline as well as SAM's roof mask matters:
    # SAM regularly catches only part of a roof, and the part it misses is
    # grey, so it reads as pavement. Dilated slightly to swallow the eave
    # shadow that rings most roofs and would otherwise survive as a halo of
    # thin "paving" fragments.
    building_polygons = list(osm["other_building_polygons_m"])
    if osm["target_polygon_m"] is not None:
        building_polygons.append(osm["target_polygon_m"])
    buildings_mask = features.rasterize_local_polygons(building_polygons, image.shape, m_per_px)
    if buildings_mask.any():
        buildings_mask = features._dilate_by_radius_m(buildings_mask, 1.0, m_per_px)
    neighbor_buildings_mask = buildings_mask
    have_surveyed_buildings = osm["target_polygon_m"] is not None

    # The lot region is derived from the roof alone, so it can be built
    # before segmenting paving - and it needs to be, because the paving
    # step uses it to tell "our wide patio" from "the neighbour's roof".
    roof_area_m2 = features.mask_area_m2(roof_mask, m_per_px)
    lot_area_m2 = features.lot_area_m2(osm["target_area_m2"], roof_area_m2)
    roof_matches_footprint = features.roof_matches_footprint(roof_area_m2, osm["target_area_m2"])
    lot_mask = features.lot_region_mask(roof_mask, lot_area_m2, m_per_px)

    impervious_mask = segmentation.segment_impervious(
        image,
        exclude_mask=roof_mask | neighbor_buildings_mask,
        m_per_px=m_per_px,
        # Always on. Subtracting the surveyed outlines was supposed to make
        # this redundant, but OSM footprints are not registered tightly
        # enough to the imagery to rely on - measured centroid offsets of
        # 2.4m to 7.6m across the demo set - so the outlines routinely miss
        # the roof they are meant to remove. With the filter off, those
        # uncovered roof slabs read as asphalt: 68A Bexhill reported 45.6%
        # impervious with blue painted across a flat grey roof, and it
        # drops to 8.4% with the filter restored.
        use_width_filter=True,
    )
    five_m_ring = features.within_distance_ring(roof_mask, 5.0, m_per_px)
    canopy_within_5m_pct = features.pct_within_region(canopy_mask, five_m_ring)
    # Fragments are dropped before measuring, not just before drawing:
    # grey confetti isn't paving, so it shouldn't inflate impervious_pct
    # any more than it should show up on the overlay.
    impervious_mask = features.drop_small_paving_fragments(impervious_mask & lot_mask, m_per_px)
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
        "confidence": _confidence(
            is_precise_match,
            roof_plausible,
            roof_matches_footprint,
            footprint_available=osm["target_area_m2"] is not None,
        ),
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
        # Crisp vegetation on the lot, not a distance-graded halo. The
        # graded version faded out to near-invisible at the edges and read
        # as a smear around the house rather than a shape you could point
        # at - in a demo the viewer has to be able to see what was
        # detected. Severity still comes through in the numbers
        # (canopy_overlap_pct vs canopy_within_5m_pct), which is where it
        # belongs, rather than being encoded as opacity nobody can read.
        "canopy_mask": features.drop_thin_vegetation(canopy_mask & lot_mask, m_per_px),
        "impervious_mask": impervious_mask,
    }
    return result, images
