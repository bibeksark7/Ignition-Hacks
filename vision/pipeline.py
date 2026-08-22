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


def analyze_at(
    lat: float, lon: float, region_key: str = "default",
    address_precision: str = "point", is_precise_match: bool = True,
) -> dict:
    """(lat, lon) -> full Contract A payload. Used directly after a
    pin-confirm step, where the user-corrected coordinates are already
    trusted and shouldn't be re-geocoded."""
    tile = imagery.fetch_tile(lat, lon)
    osm = footprints.query_buildings(lat, lon)

    image = np.array(tile["image"])
    center = (image.shape[1] // 2, image.shape[0] // 2)

    roof_mask = segmentation.segment_roof(image, center)
    canopy_mask = segmentation.segment_canopy(image)
    impervious_mask = segmentation.segment_impervious(image, exclude_mask=roof_mask)
    roof_plausible = features.roof_segmentation_is_plausible(roof_mask)

    m_per_px = features.meters_per_pixel(lat, tile["zoom"], tile["retina"])

    roof_area_m2 = features.mask_area_m2(roof_mask, m_per_px)
    lot_area_m2 = features.lot_area_m2(osm["target_area_m2"])
    roof_matches_footprint = features.roof_matches_footprint(roof_area_m2, osm["target_area_m2"])
    total_px = image.shape[0] * image.shape[1]
    canopy_pct = 100.0 * float(canopy_mask.sum()) / total_px
    impervious_pct = 100.0 * float(impervious_mask.sum()) / total_px

    feature_dict = {
        "lat": lat,
        "lon": lon,
        "imagery_date": tile["imagery_date"],
        "zoom": tile["zoom"],
        "roof_area_m2": round(roof_area_m2, 1),
        "roof_material": features.guess_roof_material(image, roof_mask),
        "roof_damage_score": features.roof_damage_score(image, roof_mask),
        "canopy_overlap_pct": round(features.mask_overlap_pct(roof_mask, canopy_mask), 1),
        "canopy_within_5m_pct": round(canopy_pct, 1),
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

    return {**feature_dict, **value}
