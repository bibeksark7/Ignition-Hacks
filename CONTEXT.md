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
  "imagery_date": null,
  "imagery_date_known": false,
  "zoom": 19,
  "roof_area_m2": 187.4,
  "roof_material": "asphalt_shingle",
  "roof_damage_score": 0.23,
  "canopy_overlap_pct": 31.5,
  "canopy_within_5m_pct": 48.0,
  "impervious_pct": 42.8,
  "lot_area_m2": 604.0,
  "nearest_structure_m": 8.4,
  "address_precision": "house",
  "roof_segmentation_plausible": true,
  "confidence": 0.75,
  "estimated_value": 742000,
  "value_basis": "heuristic: footprint x neighborhood $/m2, condition-adjusted",
  "value_confidence": "low"
}
```

> **`imagery_date` is genuinely unknown, not a bug.** Mapbox's Static Images
> API exposes no per-tile capture/vintage date anywhere (checked response
> headers directly - nothing there). An earlier version of this pipeline
> filled in today's date, which looked precise but was fabricated - fixed
> to return `null` + `imagery_date_known: false` instead. Workstream 03
> should render this as "capture date unknown" rather than hiding the
> field, per the brief's own honesty section ("show capture date, flag
> stale tiles" only works if the date shown is real).

> **Resolved conflict (do not re-litigate without both owners in the room):**
> Workstream 01 does **not** ship a `risk_score` field. Early in the build,
> Workstream 01 computed its own rough risk score directly from raw features,
> independently of Workstream 02's pricing multiplier. The two scores
> diverged (68 vs. 59 for the same house) because they were two separately
> invented weighted formulas with no shared source of truth. **Workstream 02
> owns the one risk score that reaches the UI**, because it's derived from
> the same multiplier that produces the premium — score and price can never
> contradict each other. Workstream 01 keeps a rough score internally
> (`vision/scoring.py`) purely as a dev-time sanity check; it is never
> merged into this contract's output. Confirmed working end-to-end
> 2026-08-21.

**Real bugs found and fixed since the initial build (2026-08-22), in case
anyone rediscovers the symptom:**
- SAM point-prompted alone repeatedly segmented one roof plane, a shadow
  patch, or the front lawn instead of the whole roof. Fixed: when an OSM
  building footprint exists at that point, its bounding box (padded 8m —
  SAM treats a box as a fairly hard spatial constraint, tested down to 3m
  and it clipped roofs) is passed to SAM alongside the centroid point.
  Fallback stays point-only when OSM has no coverage there (common —
  residential coverage is genuinely spotty).
- SAM's raw roof mask has small interior holes (vents, ridge lines,
  shadows) — morphological closing fixes it, kernel tuned to 27x27
  (15x15 was too small, only bridged ~7px gaps).
- `lot_area_m2` (a heuristic: OSM footprint × 2.4) can come out smaller
  than a correctly-measured roof when OSM's footprint is outdated (e.g.
  a since-built addition). Fixed by flooring the lot estimate at
  `roof_area_m2 / 0.55` rather than rejecting a correct roof measurement.
- Mask PNGs sent to the frontend must have the mask in the **alpha
  channel**, not plain grayscale — some browsers treat an opaque
  (no-alpha) image as "fully revealed" under CSS `mask-image`, ignoring
  the black/white content entirely. See `api.py`'s `_mask_png_data_uri`.
- Pools read as impervious under naive grey-threshold pavement detection —
  has its own saturated-blue-to-pale-cyan HSV range now, excluded from
  the impervious mask.
- `address_precision` flags when geocoding only matched a street, not a
  specific house; `roof_segmentation_plausible` + `confidence` cross-check
  the segmented roof area against the real OSM footprint and flag low
  confidence when they disagree by more than ~4.5x — Workstream 03 should
  surface a pin-confirm prompt when `confidence` is low.

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
  "risk_score": {
    "overall": 59.1,
    "grade": "D",
    "perils": {"fire": 60.1, "water": 53.4, "wind_hail": 67.0}
  },
  "risk_score_if_all_actions": {
    "overall": 74.8,
    "grade": "C",
    "perils": {"fire": 78.2, "water": 71.0, "wind_hail": 75.3}
  },
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

**`risk_score` rules, agreed between Workstream 01 and 02 (2026-08-21):**
- `risk_score` is the one canonical score — nested object, not a bare number.
- Scale: 0–100 float, 1 decimal, **higher = safer** (opposite direction from
  the internal risk multiplier — Workstream 03 should not invert it).
- `grade`: letter A–F (A≥90, B≥80, C≥65, D≥50, F<50).
- `perils` keys match the premium breakdown exactly: `fire`, `water`, `wind_hail`.
- `risk_score_if_all_actions` is the same shape, projected if every
  mitigation were applied — pairs with `premium_if_all_actions` for the
  before/after slider.

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

**Actual architecture (not the single-merged-endpoint plan originally
sketched here) — two separate servers, frontend calls both and merges
client-side:**
```
GET  http://<vision-host>:8010/analyze?address=...  (or &lat=&lon=)
  -> Contract A fields + imagery_png + roof_mask_png +
     canopy_mask_png + impervious_mask_png (all base64 data URIs)

POST http://<pricing-host>:8001/price   (body: the Contract A response above)
  -> Contract B fields
```
`src/api.js`'s `fetchAnalysis()` calls vision then pricing and spreads
both into one object. See §14 below for how to actually get both servers
running locally — this tripped up cross-machine testing more than once.

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
| Mapbox Static Images API | Aerial imagery | Free tier. Esri backup was never needed - Mapbox coverage was fine |
| OSM Nominatim | Geocoding | Free, no key. Residential precision is spotty - see gotchas above |
| OSM Overpass API | Building footprints | Used for SAM prompting, neighbor exclusion, lot estimate - not just a sanity check as originally planned |
| SAM / SAM 2 (Ultralytics) | Roof segmentation | Zero-shot, point + OSM-bbox prompted, no training |
| OpenCV, HSV thresholding | Canopy/pavement/pool | Classical, instant, tunable |
| Hardcoded hotspot/region table | Flood/wildfire/wind hazard | Workstream 02's own curated table, not a live feed from CWFIS/Flood Map Inventory as originally planned - see `pricing/hazards.py` |
| FastAPI | Backend | Two separate services (vision + pricing), no database - `data/cache/` is flat JSON files |
| React + Vite + Leaflet | Frontend | See `src/` |

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

## 14. Running this locally (three servers, three terminals)

```bash
# Terminal 1 - vision (needs MAPBOX_TOKEN in .env - ask Workstream 01 for
# theirs, or get your own free one; paste into your own .env, gitignored)
.venv\Scripts\python.exe -m uvicorn api:app --port 8010 --host 0.0.0.0

# Terminal 2 - pricing (no token needed)
.venv\Scripts\python.exe -m uvicorn pricing.api:app --port 8001

# Terminal 3 - frontend
npm run dev
```
Open `http://localhost:5173`.

- `--host 0.0.0.0` on the vision server matters if a teammate on the same
  WiFi needs to reach your machine (found the hard way — without it,
  the server only accepts connections from itself).
- Point a teammate's frontend at your servers instead of running your own:
  create `.env.local` (gitignored, per-machine) with
  `VITE_VISION_API_BASE=http://<their-LAN-IP>:8010` and
  `VITE_PRICING_API_BASE=http://<their-LAN-IP>:8001`. Use the raw IP
  (`192.168.x.x`), not `localhost` — hit a real IPv4/IPv6 resolution
  mismatch using `localhost` across machines.
- `uvicorn --reload` has been unreliable this session (silently served
  stale code after a file change more than once) — if a fix doesn't seem
  to be taking effect, kill the server fully and restart it plain
  (without `--reload`) rather than trusting a hot-reload happened.
- Demo-address cache lives in `data/cache/` (gitignored, per-machine).
  `GET /analyze?...&fresh=true` bypasses it for a live re-run.
