// Mock of the merged GET /analyze?address=... response (Contract A + Contract B).
// Swap this for the real fetch once Workstream 01 / 02 have a live endpoint.
export const mockAnalysis = {
  address: '42 Maple Grove, Milton, ON',
  lat: 43.5183,
  lon: -79.8774,
  imagery_date: '2024-05-11',
  zoom: 19,

  roof_area_m2: 187.4,
  roof_material: 'asphalt_shingle',
  roof_damage_score: 0.23,
  canopy_overlap_pct: 31.5,
  canopy_within_5m_pct: 48.0,
  impervious_pct: 42.8,
  lot_area_m2: 604.0,
  nearest_structure_m: 8.4,
  confidence: 0.81,

  risk_score: 68,
  risk_score_breakdown: [
    { peril: 'fire', score: 61, top_driver: 'canopy_overlap_pct' },
    { peril: 'water', score: 74, top_driver: 'impervious_pct' },
    { peril: 'wind_hail', score: 55, top_driver: 'roof_damage_score' },
  ],

  estimated_value: 742000,
  value_basis: 'heuristic: footprint x neighborhood $/m2, condition-adjusted',
  value_confidence: 'low',

  annual_premium: 2140.0,
  coverage_amount: 650000,
  perils: [
    {
      name: 'fire',
      premium: 712.0,
      multiplier: 1.34,
      drivers: [
        { feature: 'canopy_overlap_pct', effect: 0.21 },
        { feature: 'nearest_structure_m', effect: 0.09 },
      ],
    },
    {
      name: 'water',
      premium: 905.0,
      multiplier: 1.52,
      drivers: [{ feature: 'impervious_pct', effect: 0.31 }],
    },
    {
      name: 'wind_hail',
      premium: 523.0,
      multiplier: 1.08,
      drivers: [{ feature: 'roof_damage_score', effect: 0.08 }],
    },
  ],
  mitigations: [
    {
      action: 'Remove limbs overhanging roof',
      cost: 800,
      annual_saving: 190,
      payback_years: 4.2,
      peril: 'fire',
      co_benefit: 'Reduces ignition pathway to structure',
    },
    {
      action: 'Convert driveway to permeable pavers',
      cost: 3200,
      annual_saving: 260,
      payback_years: 12.3,
      peril: 'water',
      co_benefit: 'Reduces stormwater runoff and urban flooding load',
    },
    {
      action: 'Replace roof with Class-A fire-rated shingles',
      cost: 9500,
      annual_saving: 340,
      payback_years: 27.9,
      peril: 'wind_hail',
      co_benefit: 'Survives more hail, reduces ember ignition risk',
    },
  ],
  premium_if_all_actions: 1585.0,
  disclaimer: 'Demonstration model - not an actuarial quote.',

  masks: {
    roof: null,
    canopy: null,
    impervious: null,
  },
}
