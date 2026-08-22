"""Tunable constants for the pricing engine. Retune numbers here, not in the logic files.

Every dollar figure below is anchored to a real published source (cited inline),
not invented. They're still averages/estimates standing in for a real actuarial
rate table, so keep the "demonstration model" framing regardless.
"""

# Base rate per $100 of coverage, per peril. Calibrated so a low-risk baseline
# house (multiplier ~= 1.0) lands near the published Canadian national average
# home insurance premium: ~$1,200/yr (Insurance Bureau of Canada) to ~$1,340/yr
# (Ratehub/BlueCouch, 2026). At $650k coverage that's ~$1,270/yr at baseline;
# a moderately-at-risk house (multiplier ~1.3-1.5) lands higher, consistent
# with e.g. Alberta's ~$1,800-2,000/yr average amid +11.9% YoY increases.
BASE_RATES = {
    "fire": 0.059,
    "water": 0.067,
    "wind_hail": 0.055,
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

# Below this, Workstream 01's confidence score means the segmentation likely
# missed the roof or landed on the wrong structure (their _confidence()
# returns 0.15 for implausible/mismatched masks, 0.35 for an imprecise
# geocode match, 0.75 for a clean match) - surface a warning rather than
# presenting the number as reliable.
LOW_CONFIDENCE_THRESHOLD = 0.5

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
# Every cost is anchored to a 2025/2026 Canadian pricing source (cited per
# entry) rather than an invented round number.
MITIGATION_CATALOGUE = [
    {
        # "cap" reflects what this specific fix actually achieves: trimming
        # overhanging limbs clears the roof overlap down near zero regardless
        # of the starting percentage, rather than removing a fixed amount.
        # Cost: tree limb removal runs $75-400/limb (HomeStars, Omar Tree
        # Service); a full overhanging section is typically several limbs.
        "action": "Remove limbs overhanging roof",
        "mode": "feature",
        "feature": "canopy_overlap_pct",
        "cap": 5.0,
        "cost": 500,
        "peril": "fire",
        "co_benefit": "Reduces ignition pathway to structure",
    },
    {
        # Cost: professional vegetation management in Canada runs $800-12,000
        # depending on property size (The Goat Land Clearing, BC); this is a
        # 5m-perimeter job, the low end of that range.
        "action": "Clear vegetation within 5m of structure",
        "mode": "feature",
        "feature": "canopy_within_5m_pct",
        "cap": 10.0,
        "cost": 1200,
        "peril": "fire",
        "co_benefit": "Removes the primary ember-ignition pathway (a standard WUI mitigation)",
    },
    {
        # Cost: mesh retrofit materials run $200-800 for a typical home
        # (US Made Supply); full intumescent-vent professional installs run
        # $2,500-4,000 (Headwaters Economics) - this sits at the materials
        # end with modest labour.
        "action": "Install ember-resistant vents",
        "mode": "direct_effect",
        "peril": "fire",
        "multiplier_delta": -0.07,
        "cost": 700,
        "co_benefit": "Stops wind-blown embers from entering the attic during a nearby fire",
    },
    {
        # Cost: metal roofing runs $13-30/sqft installed in Canada in 2026
        # (RenoQuotes, Professional Metal Roofing); a ~2,000 sqft roof at the
        # lower-mid end of that range is ~$32,000, consistent with total
        # project quotes of $15,000-36,000. Intentionally the longest-payback
        # item in the catalogue - a resilience investment, not a quick ROI.
        "action": "Upgrade to a Class-A fire-rated metal roof",
        "mode": "feature",
        "feature": "roof_material",
        "set_value": "metal",
        "cost": 32000,
        "peril": "fire",
        "co_benefit": "Non-combustible roofing survives ember exposure and radiant heat, and holds up to hail",
    },
    {
        # Cap, not a flat delta: converting the driveway/patio realistically
        # gets a lot bounded to a low residual imperviousness, not a fixed
        # percentage-point cut, since the fix targets the whole paved area.
        # Cost: permeable pavers run $10-38/sqft installed in Canada
        # (Toronto $24-38, Quebec $15-35, HomeGuide $10-30); a ~500 sqft
        # driveway at the blended mid-range lands around $9,000.
        "action": "Convert driveway to permeable pavers",
        "mode": "feature",
        "feature": "impervious_pct",
        "cap": 20.0,
        "cost": 9000,
        "peril": "water",
        "co_benefit": "Lets stormwater infiltrate instead of overloading storm sewers",
    },
    {
        # Cost: Ontario backwater valve installs run $1,800-4,500
        # (avg. ~$2,400 interior basement, PlumbingQuotes/Premier Plumbing);
        # Quebec accessible installs run $800-4,500 depending on access.
        "action": "Install a backwater valve",
        "mode": "direct_effect",
        "peril": "water",
        "multiplier_delta": -0.08,
        "cost": 2500,
        "co_benefit": "Stops sewer backup into the home during heavy rainfall events",
    },
    {
        # Cost: Canadian roof repair averages ~$1,000/job, range $500-1,800
        # (HomeStars); this is a fuller reseal beyond simple flashing so
        # sits toward the upper end.
        "action": "Repair and reseal roof",
        "mode": "feature",
        "feature": "roof_damage_score",
        "cap": 0.05,
        "cost": 1400,
        "peril": "wind_hail",
        "co_benefit": "A sound roof surface sheds water and survives hail impact better",
    },
    {
        # Cost: average Canadian gutter guard project runs ~$1,050
        # (lfbuilders, SRS Roofing); a typical 200ft home runs $1,400-2,200.
        "action": "Install gutter guards",
        "mode": "direct_effect",
        "peril": "wind_hail",
        "multiplier_delta": -0.04,
        "cost": 1100,
        "co_benefit": "Prevents debris backup that contributes to water intrusion during storms",
    },
]
