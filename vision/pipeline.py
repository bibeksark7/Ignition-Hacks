import numpy as np

from . import geocode, imagery, segmentation, features, footprints, scoring, valuation


def analyze(address: str, region_key: str = None) -> dict:
    """Address -> full Contract A payload."""
    loc = geocode.geocode(address)
    region_key = region_key or loc["region_key"]
    tile = imagery.fetch_tile(loc["lat"], loc["lon"])
    osm = footprints.query_buildings(loc["lat"], loc["lon"])

    image = np.array(tile["image"])
    center = (image.shape[1] // 2, image.shape[0] // 2)

    roof_mask = segmentation.segment_roof(image, center)
    canopy_mask = segmentation.segment_canopy(image)
    impervious_mask = segmentation.segment_impervious(image, exclude_mask=roof_mask)

    m_per_px = features.meters_per_pixel(loc["lat"], tile["zoom"], tile["retina"])

    roof_area_m2 = features.mask_area_m2(roof_mask, m_per_px)
    lot_area_m2 = features.lot_area_m2(osm["target_area_m2"])
    total_px = image.shape[0] * image.shape[1]
    canopy_pct = 100.0 * float(canopy_mask.sum()) / total_px
    impervious_pct = 100.0 * float(impervious_mask.sum()) / total_px

    feature_dict = {
        "lat": loc["lat"],
        "lon": loc["lon"],
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
        "address_precision": loc["address_precision"],
        "confidence": 0.75 if loc["is_precise_match"] else 0.35,
    }

    risk = scoring.compute_risk_score(feature_dict)
    value = valuation.estimate_value(
        feature_dict["roof_area_m2"], feature_dict["roof_damage_score"], region_key
    )

    return {**feature_dict, **risk, **value}
