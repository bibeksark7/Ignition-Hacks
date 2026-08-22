import copy

import pytest

from pricing import config
from pricing.engine import analyze
from pricing.hazards import HazardFactors, lookup_hazards
from pricing.risk_model import compute_multipliers, score_from_multiplier

SAMPLE_CONTRACT_A = {
    "lat": 43.5183,
    "lon": -79.8774,
    "imagery_date": "2024-05-11",
    "zoom": 19,
    "roof_area_m2": 187.4,
    "roof_material": "asphalt_shingle",
    "roof_damage_score": 0.23,
    "canopy_overlap_pct": 31.5,
    "canopy_within_5m_pct": 48.0,
    "impervious_pct": 42.8,
    "lot_area_m2": 604.0,
    "nearest_structure_m": 8.4,
    "confidence": 0.81,
    "estimated_value": 742000,
    "value_basis": "heuristic: footprint x neighborhood $/m2, condition-adjusted",
    "value_confidence": "low",
}


def test_hazards_lookup_known_region_gta():
    factors = lookup_hazards(43.5183, -79.8774)
    assert factors.flood > factors.wildfire  # GTA: flood-dominant, not wildfire-dominant


def test_hazards_lookup_falls_back_to_default_outside_known_regions():
    factors = lookup_hazards(0.0, 0.0)
    assert isinstance(factors, HazardFactors)


def test_hazards_hotspots_jasper_is_wildfire_dominant():
    factors = lookup_hazards(52.8734, -118.0814)
    assert factors.wildfire > 0.8
    assert factors.wildfire > factors.flood


def test_hazards_hotspots_calgary_is_hail_dominant():
    factors = lookup_hazards(51.0447, -114.0719)
    assert factors.wind_hail > 0.7
    assert factors.wind_hail > factors.wildfire


def test_hazards_demo_contrast_jasper_vs_gta_diverges_sharply():
    jasper_house = dict(SAMPLE_CONTRACT_A, lat=52.8734, lon=-118.0814)
    gta_house = dict(SAMPLE_CONTRACT_A, lat=43.6532, lon=-79.3832)

    jasper_result = analyze(copy.deepcopy(jasper_house))
    gta_result = analyze(copy.deepcopy(gta_house))

    # Same physical measurements, different location -> fire risk should
    # clearly favour the GTA house over the Jasper house.
    assert jasper_result["risk_score"]["perils"]["fire"] < gta_result["risk_score"]["perils"]["fire"]


# Must match vision/features.py's _ROOF_MATERIAL_CLASSES on Workstream 01's
# branch - if their classifier can produce a value that isn't a real key in
# our risk tables, it silently falls back to DEFAULT_ROOF_MATERIAL_RISK
# instead of erroring, which is exactly the kind of contract drift that's
# already bitten us once (risk_score). This test forces the two lists to be
# checked by hand whenever either side changes.
WORKSTREAM_01_ROOF_MATERIAL_CLASSES = ["asphalt_shingle", "metal", "tile", "flat_gravel"]


def test_every_workstream_01_roof_material_has_a_real_risk_entry():
    for material in WORKSTREAM_01_ROOF_MATERIAL_CLASSES:
        assert material in config.ROOF_MATERIAL_FIRE_RISK, f"{material} missing from ROOF_MATERIAL_FIRE_RISK"
        assert material in config.ROOF_MATERIAL_WIND_RISK, f"{material} missing from ROOF_MATERIAL_WIND_RISK"


def test_multiplier_increases_with_more_canopy_overlap():
    low = dict(SAMPLE_CONTRACT_A, canopy_overlap_pct=5.0)
    high = dict(SAMPLE_CONTRACT_A, canopy_overlap_pct=80.0)
    hazards = lookup_hazards(low["lat"], low["lon"])
    assert compute_multipliers(high, hazards)["fire"] > compute_multipliers(low, hazards)["fire"]


def test_multiplier_increases_with_more_impervious_surface():
    low = dict(SAMPLE_CONTRACT_A, impervious_pct=5.0)
    high = dict(SAMPLE_CONTRACT_A, impervious_pct=90.0)
    hazards = lookup_hazards(low["lat"], low["lon"])
    assert compute_multipliers(high, hazards)["water"] > compute_multipliers(low, hazards)["water"]


def test_score_from_multiplier_is_monotonic_and_bounded():
    assert score_from_multiplier(0.5) == pytest.approx(100.0, abs=0.01) or score_from_multiplier(0.5) <= 100
    assert 0.0 <= score_from_multiplier(0.9) <= 100.0
    assert 0.0 <= score_from_multiplier(2.2) <= 100.0
    assert score_from_multiplier(0.9) > score_from_multiplier(2.2)


def test_end_to_end_sample_contract_produces_valid_contract_b():
    result = analyze(copy.deepcopy(SAMPLE_CONTRACT_A))

    assert 0 <= result["risk_score"]["overall"] <= 100
    assert result["risk_score"]["grade"] in {"A", "B", "C", "D", "F"}
    assert set(result["risk_score"]["perils"]) == {"fire", "water", "wind_hail"}

    assert result["annual_premium"] > 0
    assert result["coverage_amount"] == SAMPLE_CONTRACT_A["estimated_value"]

    peril_names = {p["name"] for p in result["perils"]}
    assert peril_names == {"fire", "water", "wind_hail"}
    for peril in result["perils"]:
        assert peril["premium"] > 0
        assert len(peril["drivers"]) > 0

    assert result["home_value_estimate"] == SAMPLE_CONTRACT_A["estimated_value"]
    assert 0 < result["premium_pct_of_value"] < 0.05  # sanity: premium shouldn't be a wild % of home value

    assert len(result["mitigations"]) == len(result["mitigations"])  # non-empty, see below
    assert len(result["mitigations"]) > 0


def test_mitigations_sorted_by_payback_ascending():
    result = analyze(copy.deepcopy(SAMPLE_CONTRACT_A))
    paybacks = [m["payback_years"] for m in result["mitigations"] if m["payback_years"] is not None]
    assert paybacks == sorted(paybacks)


def test_mitigations_reduce_premium_and_report_score_delta():
    result = analyze(copy.deepcopy(SAMPLE_CONTRACT_A))
    for m in result["mitigations"]:
        assert m["annual_saving"] >= 0
        assert m["cost"] > 0
        assert "co_benefit" in m and m["co_benefit"]

    assert result["premium_if_all_actions"] < result["annual_premium"]
    assert result["risk_score_if_all_actions"]["overall"] >= result["risk_score"]["overall"]


def test_missing_required_field_raises():
    bad = dict(SAMPLE_CONTRACT_A)
    del bad["roof_area_m2"]
    with pytest.raises(ValueError):
        analyze(bad)


def test_no_estimated_value_falls_back_to_default_coverage():
    no_value = dict(SAMPLE_CONTRACT_A)
    del no_value["estimated_value"]
    result = analyze(no_value)

    assert result["coverage_amount"] == config.DEFAULT_COVERAGE_AMOUNT
    assert "home_value_estimate" not in result


def test_low_confidence_flag_set_when_segmentation_unreliable():
    bad_segmentation = dict(SAMPLE_CONTRACT_A, confidence=0.15)  # Workstream 01's "implausible mask" value
    result = analyze(bad_segmentation)

    assert result["measurement_confidence"] == 0.15
    assert result["low_confidence_warning"] is True
    assert "low_confidence_reason" in result


def test_low_confidence_flag_not_set_for_clean_match():
    clean_match = dict(SAMPLE_CONTRACT_A, confidence=0.75)  # Workstream 01's "precise match" value
    result = analyze(clean_match)

    assert result["measurement_confidence"] == 0.75
    assert result["low_confidence_warning"] is False
    assert "low_confidence_reason" not in result


def test_low_confidence_flag_defaults_safely_when_confidence_absent():
    no_confidence = dict(SAMPLE_CONTRACT_A)
    del no_confidence["confidence"]
    result = analyze(no_confidence)

    assert result["measurement_confidence"] is None
    assert result["low_confidence_warning"] is False
