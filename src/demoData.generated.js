// GENERATED FILE. Do not hand-edit.
// Rebuilt from pricing/demo_cache/*.json, which the pricing engine itself
// produced. Every figure below came out of engine.py, none of it is invented.
// Regenerate after changing the fixtures:  npm run build:demo

export const DEMO_FIXTURES = [
  {
    "key": "jasper",
    "address": "Jasper, Alberta",
    "displayAddress": "Jasper, Alberta",
    "source": "high_risk_wildfire_house.json",
    "lat": 52.8734,
    "lon": -118.0814,
    "imagery_date": "2024-05-11",
    "zoom": 19,
    "roof_area_m2": 210,
    "roof_material": "wood_shake",
    "roof_damage_score": 0.55,
    "canopy_overlap_pct": 78,
    "canopy_within_5m_pct": 85,
    "impervious_pct": 18,
    "lot_area_m2": 950,
    "nearest_structure_m": 4.2,
    "confidence": 0.77,
    "estimated_value": 610000,
    "value_basis": "synthetic fixture — not a real estimate",
    "value_confidence": "low",
    "risk_score": {
      "overall": 47.7,
      "grade": "F",
      "perils": {
        "fire": 4.3,
        "water": 75.3,
        "wind_hail": 64.2
      }
    },
    "annual_premium": 1866.93,
    "coverage_amount": 610000,
    "perils": [
      {
        "name": "fire",
        "premium": 771.45,
        "multiplier": 2.143,
        "drivers": [
          {
            "feature": "canopy_overlap_pct",
            "effect": 0.351,
            "plain_language": "Trees cover about 78% of your roof, raising fire risk"
          },
          {
            "feature": "hazard_wildfire",
            "effect": 0.315,
            "plain_language": "Your area has elevated regional wildfire exposure"
          },
          {
            "feature": "canopy_within_5m_pct",
            "effect": 0.2125,
            "plain_language": "85% of the area within 5m of your home has vegetation, a wildfire ember risk"
          }
        ]
      },
      {
        "name": "water",
        "premium": 499.23,
        "multiplier": 1.222,
        "drivers": [
          {
            "feature": "impervious_pct",
            "effect": 0.099,
            "plain_language": "About 18% of your lot is paved, so stormwater has nowhere to soak in"
          },
          {
            "feature": "hazard_flood",
            "effect": 0.0675,
            "plain_language": "Your area has elevated regional flood exposure"
          },
          {
            "feature": "roof_damage_score",
            "effect": 0.055,
            "plain_language": "Visible roof wear increases water and wind/hail risk"
          }
        ]
      },
      {
        "name": "wind_hail",
        "premium": 457.96,
        "multiplier": 1.365,
        "drivers": [
          {
            "feature": "roof_damage_score",
            "effect": 0.165,
            "plain_language": "Visible roof wear increases water and wind/hail risk"
          },
          {
            "feature": "roof_material_wind_risk",
            "effect": 0.12,
            "plain_language": "Your wood shake roof is more vulnerable to wind and hail"
          },
          {
            "feature": "hazard_wind_hail",
            "effect": 0.08,
            "plain_language": "Your area has elevated regional wind/hail exposure"
          }
        ]
      }
    ],
    "mitigations": [
      {
        "action": "Remove limbs overhanging roof",
        "cost": 500,
        "annual_saving": 127.68,
        "payback_years": 3.9,
        "peril": "fire",
        "risk_score_delta": 8.8,
        "co_benefit": "Reduces ignition pathway to structure"
      },
      {
        "action": "Clear vegetation within 5m of structure",
        "cost": 1200,
        "annual_saving": 72.88,
        "payback_years": 16.5,
        "peril": "fire",
        "risk_score_delta": 5,
        "co_benefit": "Removes the primary ember-ignition pathway (a standard WUI mitigation)"
      },
      {
        "action": "Repair and reseal roof",
        "cost": 1400,
        "annual_saving": 76.42,
        "payback_years": 18.3,
        "peril": "wind_hail",
        "risk_score_delta": 4.4,
        "co_benefit": "A sound roof surface sheds water and survives hail impact better"
      },
      {
        "action": "Install ember-resistant vents",
        "cost": 700,
        "annual_saving": 27.21,
        "payback_years": 25.7,
        "peril": "fire",
        "risk_score_delta": 1.9,
        "co_benefit": "Stops wind-blown embers from entering the attic during a nearby fire"
      },
      {
        "action": "Install a backwater valve",
        "cost": 2500,
        "annual_saving": 35.31,
        "payback_years": 70.8,
        "peril": "water",
        "risk_score_delta": 2.4,
        "co_benefit": "Stops sewer backup into the home during heavy rainfall events"
      },
      {
        "action": "Install gutter guards",
        "cost": 1100,
        "annual_saving": 14.49,
        "payback_years": 75.9,
        "peril": "wind_hail",
        "risk_score_delta": 0.8,
        "co_benefit": "Prevents debris backup that contributes to water intrusion during storms"
      },
      {
        "action": "Upgrade to a Class-A fire-rated metal roof",
        "cost": 32000,
        "annual_saving": 75.63,
        "payback_years": 423.1,
        "peril": "fire",
        "risk_score_delta": 4.8,
        "co_benefit": "Non-combustible roofing survives ember exposure and radiant heat, and holds up to hail"
      },
      {
        "action": "Convert driveway to permeable pavers",
        "cost": 9000,
        "annual_saving": 0,
        "payback_years": null,
        "peril": "water",
        "risk_score_delta": 0,
        "co_benefit": "Lets stormwater infiltrate instead of overloading storm sewers"
      }
    ],
    "premium_if_all_actions": 1437.29,
    "risk_score_if_all_actions": {
      "overall": 75.9,
      "grade": "C",
      "perils": {
        "fire": 58.7,
        "water": 85.3,
        "wind_hail": 85
      }
    },
    "disclaimer": "Demonstration model — not an actuarial quote or a property appraisal.",
    "home_value_estimate": 610000,
    "home_value_basis": "synthetic fixture — not a real estimate",
    "home_value_confidence": "low",
    "premium_pct_of_value": 0.0031,
    "measurement_confidence": 0.77,
    "low_confidence_warning": false
  },
  {
    "key": "toronto",
    "address": "Downtown Toronto, Ontario",
    "displayAddress": "Downtown Toronto, Ontario",
    "source": "moderate_flood_house.json",
    "lat": 43.6532,
    "lon": -79.3832,
    "imagery_date": "2024-04-18",
    "zoom": 19,
    "roof_area_m2": 145,
    "roof_material": "asphalt_shingle",
    "roof_damage_score": 0.3,
    "canopy_overlap_pct": 12,
    "canopy_within_5m_pct": 15,
    "impervious_pct": 71,
    "lot_area_m2": 380,
    "nearest_structure_m": 6.5,
    "confidence": 0.85,
    "estimated_value": 1150000,
    "value_basis": "synthetic fixture — not a real estimate",
    "value_confidence": "low",
    "risk_score": {
      "overall": 56.9,
      "grade": "D",
      "perils": {
        "fire": 72.1,
        "water": 37.5,
        "wind_hail": 66.9
      }
    },
    "annual_premium": 3259.61,
    "coverage_amount": 1150000,
    "perils": [
      {
        "name": "fire",
        "premium": 857.06,
        "multiplier": 1.263,
        "drivers": [
          {
            "feature": "nearest_structure_spacing",
            "effect": 0.0917,
            "plain_language": "Your home is only 6.5m from the nearest structure, which lets fire spread more easily"
          },
          {
            "feature": "canopy_overlap_pct",
            "effect": 0.054,
            "plain_language": "Trees cover about 12% of your roof, raising fire risk"
          },
          {
            "feature": "roof_material_fire_risk",
            "effect": 0.045,
            "plain_language": "Your asphalt shingle roof is more flammable than average"
          }
        ]
      },
      {
        "name": "water",
        "premium": 1319.87,
        "multiplier": 1.713,
        "drivers": [
          {
            "feature": "impervious_pct",
            "effect": 0.3905,
            "plain_language": "About 71% of your lot is paved, so stormwater has nowhere to soak in"
          },
          {
            "feature": "hazard_flood",
            "effect": 0.2925,
            "plain_language": "Your area has elevated regional flood exposure"
          },
          {
            "feature": "roof_damage_score",
            "effect": 0.03,
            "plain_language": "Visible roof wear increases water and wind/hail risk"
          }
        ]
      },
      {
        "name": "wind_hail",
        "premium": 841.23,
        "multiplier": 1.33,
        "drivers": [
          {
            "feature": "hazard_wind_hail",
            "effect": 0.14,
            "plain_language": "Your area has elevated regional wind/hail exposure"
          },
          {
            "feature": "roof_material_wind_risk",
            "effect": 0.1,
            "plain_language": "Your asphalt shingle roof is more vulnerable to wind and hail"
          },
          {
            "feature": "roof_damage_score",
            "effect": 0.09,
            "plain_language": "Visible roof wear increases water and wind/hail risk"
          }
        ]
      }
    ],
    "mitigations": [
      {
        "action": "Install ember-resistant vents",
        "cost": 700,
        "annual_saving": 51.29,
        "payback_years": 13.6,
        "peril": "fire",
        "risk_score_delta": 1.9,
        "co_benefit": "Stops wind-blown embers from entering the attic during a nearby fire"
      },
      {
        "action": "Repair and reseal roof",
        "cost": 1400,
        "annual_saving": 72.03,
        "payback_years": 19.4,
        "peril": "wind_hail",
        "risk_score_delta": 2.2,
        "co_benefit": "A sound roof surface sheds water and survives hail impact better"
      },
      {
        "action": "Remove limbs overhanging roof",
        "cost": 500,
        "annual_saving": 23.08,
        "payback_years": 21.7,
        "peril": "fire",
        "risk_score_delta": 0.9,
        "co_benefit": "Reduces ignition pathway to structure"
      },
      {
        "action": "Install a backwater valve",
        "cost": 2500,
        "annual_saving": 66.57,
        "payback_years": 37.6,
        "peril": "water",
        "risk_score_delta": 2.5,
        "co_benefit": "Stops sewer backup into the home during heavy rainfall events"
      },
      {
        "action": "Convert driveway to permeable pavers",
        "cost": 9000,
        "annual_saving": 233.41,
        "payback_years": 38.6,
        "peril": "water",
        "risk_score_delta": 8.7,
        "co_benefit": "Lets stormwater infiltrate instead of overloading storm sewers"
      },
      {
        "action": "Install gutter guards",
        "cost": 1100,
        "annual_saving": 27.32,
        "payback_years": 40.3,
        "peril": "wind_hail",
        "risk_score_delta": 0.8,
        "co_benefit": "Prevents debris backup that contributes to water intrusion during storms"
      },
      {
        "action": "Clear vegetation within 5m of structure",
        "cost": 1200,
        "annual_saving": 9.16,
        "payback_years": 131,
        "peril": "fire",
        "risk_score_delta": 0.4,
        "co_benefit": "Removes the primary ember-ignition pathway (a standard WUI mitigation)"
      },
      {
        "action": "Upgrade to a Class-A fire-rated metal roof",
        "cost": 32000,
        "annual_saving": 62.97,
        "payback_years": 508.2,
        "peril": "fire",
        "risk_score_delta": 2,
        "co_benefit": "Non-combustible roofing survives ember exposure and radiant heat, and holds up to hail"
      }
    ],
    "premium_if_all_actions": 2713.75,
    "risk_score_if_all_actions": {
      "overall": 76,
      "grade": "C",
      "perils": {
        "fire": 83.1,
        "water": 67.1,
        "wind_hail": 80.4
      }
    },
    "disclaimer": "Demonstration model — not an actuarial quote or a property appraisal.",
    "home_value_estimate": 1150000,
    "home_value_basis": "synthetic fixture — not a real estimate",
    "home_value_confidence": "low",
    "premium_pct_of_value": 0.0028,
    "measurement_confidence": 0.85,
    "low_confidence_warning": false
  },
  {
    "key": "northyork",
    "address": "North York, Toronto, Ontario",
    "displayAddress": "North York, Toronto, Ontario",
    "source": "low_risk_house.json",
    "lat": 43.7,
    "lon": -79.42,
    "imagery_date": "2024-06-02",
    "zoom": 19,
    "roof_area_m2": 160,
    "roof_material": "metal",
    "roof_damage_score": 0.03,
    "canopy_overlap_pct": 4,
    "canopy_within_5m_pct": 6,
    "impervious_pct": 22,
    "lot_area_m2": 540,
    "nearest_structure_m": 14,
    "confidence": 0.9,
    "estimated_value": 890000,
    "value_basis": "synthetic fixture — not a real estimate",
    "value_confidence": "low",
    "risk_score": {
      "overall": 73.6,
      "grade": "C",
      "perils": {
        "fire": 85.9,
        "water": 60.3,
        "wind_hail": 77.8
      }
    },
    "annual_premium": 2154.99,
    "coverage_amount": 890000,
    "perils": [
      {
        "name": "fire",
        "premium": 568.68,
        "multiplier": 1.083,
        "drivers": [
          {
            "feature": "hazard_wildfire",
            "effect": 0.035,
            "plain_language": "Your area has elevated regional wildfire exposure"
          },
          {
            "feature": "canopy_overlap_pct",
            "effect": 0.018,
            "plain_language": "Trees cover about 4% of your roof, raising fire risk"
          },
          {
            "feature": "canopy_within_5m_pct",
            "effect": 0.015,
            "plain_language": "6% of the area within 5m of your home has vegetation, a wildfire ember risk"
          }
        ]
      },
      {
        "name": "water",
        "premium": 844.66,
        "multiplier": 1.417,
        "drivers": [
          {
            "feature": "hazard_flood",
            "effect": 0.2925,
            "plain_language": "Your area has elevated regional flood exposure"
          },
          {
            "feature": "impervious_pct",
            "effect": 0.121,
            "plain_language": "About 22% of your lot is paved, so stormwater has nowhere to soak in"
          },
          {
            "feature": "roof_damage_score",
            "effect": 0.003,
            "plain_language": "Visible roof wear increases water and wind/hail risk"
          }
        ]
      },
      {
        "name": "wind_hail",
        "premium": 582.02,
        "multiplier": 1.189,
        "drivers": [
          {
            "feature": "hazard_wind_hail",
            "effect": 0.14,
            "plain_language": "Your area has elevated regional wind/hail exposure"
          },
          {
            "feature": "roof_material_wind_risk",
            "effect": 0.04,
            "plain_language": "Your metal roof is more vulnerable to wind and hail"
          },
          {
            "feature": "roof_damage_score",
            "effect": 0.009,
            "plain_language": "Visible roof wear increases water and wind/hail risk"
          }
        ]
      }
    ],
    "mitigations": [
      {
        "action": "Install ember-resistant vents",
        "cost": 700,
        "annual_saving": 39.7,
        "payback_years": 17.6,
        "peril": "fire",
        "risk_score_delta": 1.9,
        "co_benefit": "Stops wind-blown embers from entering the attic during a nearby fire"
      },
      {
        "action": "Install a backwater valve",
        "cost": 2500,
        "annual_saving": 51.52,
        "payback_years": 48.5,
        "peril": "water",
        "risk_score_delta": 2.5,
        "co_benefit": "Stops sewer backup into the home during heavy rainfall events"
      },
      {
        "action": "Install gutter guards",
        "cost": 1100,
        "annual_saving": 21.15,
        "payback_years": 52,
        "peril": "wind_hail",
        "risk_score_delta": 0.8,
        "co_benefit": "Prevents debris backup that contributes to water intrusion during storms"
      },
      {
        "action": "Convert driveway to permeable pavers",
        "cost": 9000,
        "annual_saving": 7.09,
        "payback_years": 1269.4,
        "peril": "water",
        "risk_score_delta": 0.4,
        "co_benefit": "Lets stormwater infiltrate instead of overloading storm sewers"
      },
      {
        "action": "Remove limbs overhanging roof",
        "cost": 500,
        "annual_saving": 0,
        "payback_years": null,
        "peril": "fire",
        "risk_score_delta": 0,
        "co_benefit": "Reduces ignition pathway to structure"
      },
      {
        "action": "Clear vegetation within 5m of structure",
        "cost": 1200,
        "annual_saving": 0,
        "payback_years": null,
        "peril": "fire",
        "risk_score_delta": 0,
        "co_benefit": "Removes the primary ember-ignition pathway (a standard WUI mitigation)"
      },
      {
        "action": "Upgrade to a Class-A fire-rated metal roof",
        "cost": 32000,
        "annual_saving": 0,
        "payback_years": null,
        "peril": "fire",
        "risk_score_delta": 0,
        "co_benefit": "Non-combustible roofing survives ember exposure and radiant heat, and holds up to hail"
      },
      {
        "action": "Repair and reseal roof",
        "cost": 1400,
        "annual_saving": 0,
        "payback_years": null,
        "peril": "wind_hail",
        "risk_score_delta": 0,
        "co_benefit": "A sound roof surface sheds water and survives hail impact better"
      }
    ],
    "premium_if_all_actions": 2035.54,
    "risk_score_if_all_actions": {
      "overall": 79.1,
      "grade": "C",
      "perils": {
        "fire": 91.3,
        "water": 67.3,
        "wind_hail": 80.8
      }
    },
    "disclaimer": "Demonstration model — not an actuarial quote or a property appraisal.",
    "home_value_estimate": 890000,
    "home_value_basis": "synthetic fixture — not a real estimate",
    "home_value_confidence": "low",
    "premium_pct_of_value": 0.0024,
    "measurement_confidence": 0.9,
    "low_confidence_warning": false
  }
]
