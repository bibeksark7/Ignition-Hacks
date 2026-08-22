# Sightline — Project Context

Ignition Hacks · Tracks: Fintech + Environmental · Team of 4 · 36 hours

> Insurance pricing from what a satellite can actually see — reframed around the
> homeowner: a consumer-facing home risk score and value estimate, with
> insurance savings as supporting evidence rather than the headline.

Give this file to any AI assistant / teammate working on any branch so everyone
builds against the same shared understanding, even while working in isolation.

---

## 1. The pitch, one sentence

Type in an address. We pull the aerial photo, use computer vision to measure
the roof, the tree canopy over it, and how much of the lot is paved. Those
measurements produce a **consumer risk score** and an **estimated home value**,
feed a real actuarial pricing model for context, and return a ranked list of
fixes — each with what it costs, what it saves per year, and how long it takes
to pay for itself.

**Chain: detection → measurement → risk score + value → dollars → decision.**

## 2. The reframe (read this even if you know the original brief)

The original hackathon brief pitches this as an **insurer's** pricing tool
(input: address, output: a premium quote). We are deliberately shifting the
emphasis to the **consumer**:

- The homeowner's first-class output is a **0–100 risk score** (like a credit
  score) — legible on its own, before any dollar figure exists.
- Alongside it: a **rough estimated home value**, so risk and equity are shown
  together.
- The insurance premium / mitigation savings still exist and still matter —
  they're the "so what" that makes the risk score actionable — but they are
  presented as supporting evidence for the homeowner's decision, not as an
  insurer's internal pricing output.
- None of the underlying technical pipeline changes (imagery → segmentation →
  measurements → risk multipliers → premium → mitigations). Only what's
  foregrounded in the UI and what Workstream 01 additionally computes (risk
  score, value estimate) changes.

## 3. The problem (for the pitch)

Two people are hurt by the same blind spot:

- **The homeowner** — bill goes up, nobody says why, no feedback loop between
  "my roof has a fixable problem" and "this is what it costs me."
- **The insurer** — prices risk off postal code + self-reported questionnaire;
  physical inspection costs hundreds of dollars per property so it rarely
  happens.

Every fact needed (roof condition, overhanging trees, paved lot) already
exists in a free aerial photo.

**Why now:** Canadian insured catastrophe losses have gone vertical
($9.4B in 2024 — Jasper wildfire, Calgary hail, GTA flooding; $6.5B Fort
McMurray 2016; $4.2B Alberta/Ontario flooding 2013). Catastrophe losses get
spread across everyone's premiums, including people who never claimed.

## 4. The hook (use in the pitch)

Since 1875, Charles E. Goad produced hand-drawn, colour-coded fire insurance
plans of Canadian cities (red=brick, blue=stone, yellow=wood frame) so
underwriters could price a block without visiting it. The industry stopped
because keeping it updated by hand became too expensive. **We're automating a
150-year-old practice that was abandoned for cost reasons, not because the
idea was wrong.** Borrow the colour coding for the UI: brick-red = roof,
blue = water/impervious surface, green = canopy.

## 5. Why both tracks, honestly

- **Fintech:** a real pricing engine — frequency/severity actuarial math from
  a novel (imagery) data source, producing a real financial artifact (a
  quote + ROI on each recommended action).
- **Environmental:** (1) every recommendation is a climate adaptation measure
  (less canopy over structure = less ignition risk, permeable surface = less
  urban flooding, better roof = survives more hail); (2) insurance is a
  climate lever that actually changes behaviour, because the number is
  attached to a person's own money; (3) canopy % and impervious % are exactly
  the figures cities need for stormwater/heat-island planning and mostly only
  have as coarse, years-old estimates.

## 6. Product flow (what a user experiences)

1. Type an address or drop a pin (with a pin-confirm step).
2. Geocode → pull aerial imagery tile centred on that point.
3. Vision pipeline segments the image, measures four things (below).
4. Measurements + location hazard data (flood/wildfire) →
   **consumer risk score**, broken down by peril (fire/water/wind).
5. **Estimated home value** shown alongside the risk score.
6. Risk score converts into a premium quote via a transparent actuarial
   structure (context/evidence, not the headline).
7. Ranked mitigation list — the screen that wins: *"Trim the two limbs
   overhanging the north face — ~$800, saves $190/yr, pays back in 4.2 years."*

### The four things the camera measures

| Feature | What it captures |
|---|---|
| Roof | Footprint outline, area (m²), material class, visible damage/staining |
| Canopy | Tree cover overlapping roof + within perimeter (wildfire / falling-limb risk) |
| Impervious surface | Driveway/patio/pavement as % of lot (where water goes) |
| Structure spacing | Distance to nearest neighbouring building (fire spread) |

## 7. The money math (owned by Workstream 02, everyone should understand it)

```
premium_peril = base_rate_peril × risk_multiplier(features, hazards) × (coverage_amount / 100)
total = Σ premium_peril × (1 + expense_load)
```

`risk_multiplier` is a transparent weighted model (config file, not buried in
code) — canopy overlap pushes fire multiplier up, impervious % pushes water
multiplier up, good structure spacing pulls fire down. Transparency is a
product feature: every dollar of premium is attributable to a specific
measured cause, which no insurer currently offers a customer.

**Mitigation engine:** for each candidate fix, change that one feature to its
improved value, re-run pricing, take the difference = annual saving. cost ÷
annual saving = payback period. Sort ascending by payback.

## 8. Honesty constraints (say these out loud, don't hide them)

- Roof condition from overhead is mostly not visible — scope down now.
- No ground truth — don't claim the numbers are real; they're a demonstration
  model calibrated to published averages.
- Home value estimate is a rough heuristic (footprint size × neighborhood
  $/m² benchmark, condition-adjusted), explicitly disclosed as low-confidence
  — not an appraisal or AVM.
- Geocoding can land on the wrong building — hence the pin-confirm step.
- Imagery can be old — show capture date, flag stale tiles.
- Privacy: imagery is already public/already used commercially; what matters
  is who the output serves — this tool is built to show homeowners their own
  risk and how to lower it, not to help insurers surveil them.

**Golden rule for demo day:** pre-cache 5–10 demo addresses (imagery, masks,
results) to disk. Never make a live API call on stage.

## 9. The four workstreams and their contracts

Three people build the machine in parallel against these agreed contracts.
The fourth builds the case for it. Agree contract shapes in hour 0–2, then
build against mocks — nobody waits on anybody.

### Workstream 01 · Imagery & Vision (owner: this branch — `workstream-01-vision`)

Owns: address → measurements → risk score → value estimate.

- Geocoding (address → lat/lon) + pin-confirm step
- Fetch aerial imagery tile (zoom 19–20)
- Roof segmentation via SAM (Segment Anything, zero-shot, point-prompted) —
  no training needed
- Canopy / pavement via classical HSV colour thresholding — no model needed
- Roof material/damage classification (colour/texture heuristics)
- Pixel → m² conversion (`m_per_px = 156543.03392 × cos(lat_rad) / 2^zoom`;
  halve if using @2x/retina 512px tiles)
- **New vs. original brief:** normalize measurements into a 0–100 risk score
  per peril; estimate home value via a heuristic (roof footprint size ×
  neighborhood $/m² lookup, condition-adjusted, explicitly low-confidence)

**Contract A — output, consumed by Workstream 02:**
```json
{
  "lat": 43.5183, "lon": -79.8774,
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
  "risk_score": 68,
  "risk_score_breakdown": [
    {"peril": "fire", "score": 61, "top_driver": "canopy_overlap_pct"},
    {"peril": "water", "score": 74, "top_driver": "impervious_pct"}
  ],
  "estimated_value": 742000,
  "value_basis": "heuristic: footprint x neighborhood $/m2, condition-adjusted",
  "value_confidence": "low"
}
```

Known gotchas: shadows read as dark roof (check a north-facing roof early);
pools read as impervious under naive thresholding; SAM segments the wrong
thing if the prompt point is off by a few metres.

### Workstream 02 · Risk & Pricing Engine

Owns: measurements → premium + ranked mitigation list. Consumes Contract A.

- Location hazard lookups (Canada Flood Map Inventory, CWFIS wildfire datamart)
- Per-peril risk multiplier as a transparent weighted config
- Premium calc: rate × units per peril, summed, + expense loading
- Base rates anchored to published Canadian average premiums (plausibility
  check on an ordinary bungalow)
- Mitigation engine (re-price per candidate fix, sort by payback)
- Mitigation catalogue with realistic Canadian costs
- Full attribution breakdown per peril

**Contract B — output, consumed by Workstream 03:**
```json
{
  "annual_premium": 2140.00,
  "coverage_amount": 650000,
  "perils": [
    {"name": "fire", "premium": 712.00, "multiplier": 1.34,
     "drivers": [{"feature": "canopy_overlap_pct", "effect": 0.21},
                 {"feature": "nearest_structure_m", "effect": 0.09}]},
    {"name": "water", "premium": 905.00, "multiplier": 1.52, "drivers": []},
    {"name": "wind_hail", "premium": 523.00, "multiplier": 1.08, "drivers": []}
  ],
  "mitigations": [
    {"action": "Remove limbs overhanging roof", "cost": 800,
     "annual_saving": 190, "payback_years": 4.2, "peril": "fire",
     "co_benefit": "Reduces ignition pathway to structure"}
  ],
  "premium_if_all_actions": 1585.00,
  "disclaimer": "Demonstration model - not an actuarial quote."
}
```

Include a `co_benefit` string on every mitigation — cheap to add, lets
Workstream 04 show environmental-track judges that every financial
recommendation is also an adaptation measure.

### Workstream 03 · Product & Interface

Owns: the entire visible product. Consumes Contract A + B (merged into one
API response). Consumer-lens change: **risk score + estimated value are the
headline**, above the fold; premium/mitigations follow as supporting detail.

- Address entry + pin-confirm on a real map
- Imagery panel with toggleable coloured mask overlays (brick-red roof,
  green canopy, blue impervious) + visible capture date — build this first,
  it's the single highest-value feature
- Risk score display (prominent, e.g. gauge/number) + estimated value,
  side by side
- Per-peril premium breakdown (bar/stacked chart) as supporting context
- Plain-language attribution ("what pushed this up or down")
- Mitigation cards sorted by payback: cost, annual saving, payback period,
  environmental co-benefit
- Before/after slider: score & premium if every mitigation were done
- Loading state that names each pipeline step as it runs

Endpoint contract:
```
GET /analyze?address=...
  -> Workstream 01 features (Contract A)
   + Workstream 02 pricing (Contract B)
   + mask PNGs (base64 or URL)
   + imagery tile
```
Build against a hardcoded mock of this from hour two — never sit idle
waiting for the backend to exist.

Scope discipline: one page that does the whole flow beautifully beats five
half-finished pages. No login, no accounts, no settings panel.

### Workstream 04 · Pitch, Demo & Integration

Owns: the story, the demo, the submission, and integration testing.

- Sources every figure used in the pitch (loss totals, average premiums,
  mitigation costs, Goad history) and can defend it
- Writes an exact, timed demo script
- Records a backup video of the full working flow by hour 33 (non-negotiable)
- Runs end-to-end integration every 3 hours starting hour 14 — catches
  silent contract breakage (e.g. a renamed field) before it reaches judges
- Picks demo addresses deliberately (one bad-score property, one good one,
  for a five-second visual contrast)
- Builds the deck: problem → Goad hook → live demo → how it works → both
  tracks → honest limitations → what's next
- Writes the submission (Devpost + README + screenshots), submits an hour
  early
- Runs Q&A drills from hour 30

## 10. Timeline (36 hours)

| Block | Focus |
|---|---|
| 0–2 | Agree contracts (above), not code. Repo + API tokens set up. |
| 2–10 | Parallel build against mocks. Target: one working slice each. |
| 10–14 | **First real end-to-end integration, one real address.** Must happen by hour 14 — the most common way strong projects die is leaving this until hour 30. |
| 14–24 | Depth: better masks, mitigation engine, mask overlay, risk score/value polish. Integration check every 3 hours. |
| 24–30 | Feature freeze, then polish only. Cache demo addresses. |
| 30–33 | Record backup video. Submit writeup. |
| 33–36 | Rehearse out loud, standing up, timed, 5+ times. |

## 11. Fallback ladder (agree now, while calm)

1. Everything live — any address judges name, fetched live.
2. Cached imagery, live analysis — 10 pre-fetched addresses, vision/pricing
   run for real.
3. Cached masks, live pricing — segmentation pre-computed, pricing/mitigation
   loop still runs live.
4. Everything pre-computed, interface live — stored results, real interface,
   honest framing ("here's what our pipeline produced for these properties").

Rung 4 still demos well if Workstream 03 did their job — say it plainly if
asked how the numbers were produced.

## 12. Stack & sources

| Piece | Use | Notes |
|---|---|---|
| Mapbox Static Images API | Aerial imagery | Free tier, get token hour one |
| Esri World Imagery | Backup imagery | If Mapbox coverage is poor |
| SAM / SAM 2 (Ultralytics) | Roof segmentation | Zero-shot, point-prompted, no training |
| OpenCV, HSV thresholding | Canopy/pavement | Classical, instant, tunable |
| Canada Flood Map Inventory | Flood hazard | Federal open data portal |
| CWFIS datamart | Wildfire exposure | Canadian Wildland Fire Information System |
| Microsoft Building Footprints | Ground-truth sanity check | Not a replacement for the vision pipeline |
| FastAPI + SQLite | Backend | Or whatever the team already knows |

Figures sourced from Insurance Bureau of Canada catastrophe loss reporting,
Square One insurance pricing documentation, published wildfire mitigation
discount schedules, and the Charles E. Goad fire insurance plan collections
(Archives of Ontario, McMaster University Library). Pricing figures are
illustrative — a demonstration model, not actuarial advice.

## 13. Git workflow

- `main` is the integration branch — always kept in a working/demoable state.
- Each person works on their own branch (`workstream-01-vision`,
  `workstream-02-pricing`, `workstream-03-frontend`) and pushes freely there.
- Merges into `main` happen only at integration checkpoints (hour ~10–14,
  then every 3 hours from hour 14), ideally run by the Workstream 04 owner.
- Before merging into `main`, merge `main` into your own branch first and
  resolve conflicts locally.
