"""Tunable constants for the pricing engine. Retune numbers here, not in the logic files.

Every constant below is a modelling assumption, not a measured fact — flag any of
these that need a real citation to Workstream 04 before the pitch.
"""

# Base rate per $100 of coverage, per peril. Chosen so a moderately-at-risk
# suburban home (multiplier ~1.3-1.5) lands near published Canadian average
# home insurance premiums. TODO(workstream-04): confirm against IBC/Ratehub
# figures before quoting this in the pitch.
BASE_RATES = {
    "fire": 0.075,
    "water": 0.085,
    "wind_hail": 0.070,
}

EXPENSE_LOAD = 0.08  # insurer overhead/admin loading applied to the summed peril premiums

DEFAULT_COVERAGE_AMOUNT = 650_000  # fallback if Contract A has no estimated_value

# --- Risk multiplier model ---------------------------------------------------
# multiplier = 1.0 + sum(weight * normalized_risk_factor), clamped to this range.
MULTIPLIER_MIN = 0.5
MULTIPLIER_MAX = 2.2

# feature/hazard key -> weight, applied to that factor's normalized 0-1 "riskiness".
RISK_WEIGHTS = {
    "fire": {
        "canopy_overlap_pct": 0.45,
        "canopy_within_5m_pct": 0.25,
        "nearest_structure_spacing": 0.20,  # closer neighbour = riskier
        "roof_material_fire_risk": 0.15,
        "hazard_wildfire": 0.35,
    },
    "water": {
        "impervious_pct": 0.55,
        "roof_damage_score": 0.10,
        "hazard_flood": 0.45,
    },
    "wind_hail": {
        "roof_damage_score": 0.30,
        "roof_material_wind_risk": 0.20,
        "hazard_wind_hail": 0.40,
    },
}

ROOF_MATERIAL_FIRE_RISK = {
    "asphalt_shingle": 0.3,
    "wood_shake": 0.9,
    "metal": 0.1,
    "tile": 0.15,
    "flat_membrane": 0.4,
    "flat_gravel": 0.25,  # Workstream 01's classifier's actual label for flat roofs
}

ROOF_MATERIAL_WIND_RISK = {
    "asphalt_shingle": 0.5,
    "wood_shake": 0.6,
    "metal": 0.2,
    "tile": 0.35,
    "flat_membrane": 0.55,
    "flat_gravel": 0.6,  # gravel ballast scours and membrane lifts at high wind speeds
}

DEFAULT_ROOF_MATERIAL_RISK = 0.4  # used if roof_material isn't in the tables above

SPACING_RISK_THRESHOLD_M = 12.0  # beyond this distance, spacing risk is treated as ~0

# --- Risk score (0-100, higher = safer) --------------------------------------
# Linear map from a peril's multiplier to its score. Bounds are set near the
# practically-achievable multiplier range (not the hard clamp range above) so
# scores actually spread out across 0-100 instead of clustering.
SCORE_SAFE_MULTIPLIER = 0.9    # maps to score 100
SCORE_RISKY_MULTIPLIER = MULTIPLIER_MAX  # maps to score 0

# Combine per-peril scores into one overall score, weighted by each peril's
# rough share of a typical premium.
OVERALL_SCORE_WEIGHTS = {"fire": 0.35, "water": 0.40, "wind_hail": 0.25}

GRADE_THRESHOLDS = [(90, "A"), (80, "B"), (65, "C"), (50, "D"), (0, "F")]

# --- Mitigation catalogue -----------------------------------------------------
# Two entry shapes:
#   "feature"        -> change one measured feature, re-run the full pricing
#                        function, take the difference (per CONTEXT.md formula).
#   "direct_effect"   -> for fixes not tied to a vision-measured feature
#                        (e.g. backwater valve), apply a fixed multiplier
#                        reduction to one peril directly.
# Costs are illustrative round numbers. TODO(workstream-04): source real
# Canadian costs before the pitch.
MITIGATION_CATALOGUE = [
    {
        # "cap" reflects what this specific fix actually achieves: trimming
        # overhanging limbs clears the roof overlap down near zero regardless
        # of the starting percentage, rather than removing a fixed amount.
        "action": "Remove limbs overhanging roof",
        "mode": "feature",
        "feature": "canopy_overlap_pct",
        "cap": 5.0,
        "cost": 800,
        "peril": "fire",
        "co_benefit": "Reduces ignition pathway to structure",
    },
    {
        "action": "Clear vegetation within 5m of structure",
        "mode": "feature",
        "feature": "canopy_within_5m_pct",
        "cap": 10.0,
        "cost": 650,
        "peril": "fire",
        "co_benefit": "Removes the primary ember-ignition pathway (a standard WUI mitigation)",
    },
    {
        "action": "Install ember-resistant vents",
        "mode": "direct_effect",
        "peril": "fire",
        "multiplier_delta": -0.07,
        "cost": 1200,
        "co_benefit": "Stops wind-blown embers from entering the attic during a nearby fire",
    },
    {
        "action": "Upgrade to a Class-A fire-rated metal roof",
        "mode": "feature",
        "feature": "roof_material",
        "set_value": "metal",
        "cost": 14000,
        "peril": "fire",
        "co_benefit": "Non-combustible roofing survives ember exposure and radiant heat, and holds up to hail",
    },
    {
        # Cap, not a flat delta: converting the driveway/patio realistically
        # gets a lot bounded to a low residual imperviousness, not a fixed
        # percentage-point cut, since the fix targets the whole paved area.
        "action": "Convert driveway to permeable pavers",
        "mode": "feature",
        "feature": "impervious_pct",
        "cap": 20.0,
        "cost": 4500,
        "peril": "water",
        "co_benefit": "Lets stormwater infiltrate instead of overloading storm sewers",
    },
    {
        "action": "Install a backwater valve",
        "mode": "direct_effect",
        "peril": "water",
        "multiplier_delta": -0.08,
        "cost": 2500,
        "co_benefit": "Stops sewer backup into the home during heavy rainfall events",
    },
    {
        "action": "Repair and reseal roof",
        "mode": "feature",
        "feature": "roof_damage_score",
        "cap": 0.05,
        "cost": 2200,
        "peril": "wind_hail",
        "co_benefit": "A sound roof surface sheds water and survives hail impact better",
    },
    {
        "action": "Install gutter guards",
        "mode": "direct_effect",
        "peril": "wind_hail",
        "multiplier_delta": -0.04,
        "cost": 350,
        "co_benefit": "Prevents debris backup that contributes to water intrusion during storms",
    },
]
