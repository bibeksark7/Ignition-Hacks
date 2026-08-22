# Devpost submission copy

## Tagline

Insurance pricing from what a satellite can actually see.

## Inspiration

In 1875 a surveyor named Charles E. Goad began producing fire insurance plans
of Canadian cities — every building drawn to scale and colour-coded by what it
was built of: red for brick, blue for stone, yellow for wood frame. An
underwriter could price a whole block without leaving their desk. The industry
abandoned the practice because maintaining it by hand became too expensive.
Not because it was the wrong idea.

Meanwhile Canadian insurers paid $9.4B in catastrophe claims in 2024. Those
losses get spread across everyone's premiums, including people who never filed
a claim — and the homeowner paying the bill is told neither which feature of
their property drove it nor what to do about it. A physical inspection could
answer both, at hundreds of dollars a visit, so it effectively never happens.

Every fact you'd need is already sitting in a free aerial photograph. We
rebuilt Goad's plan, automatically.

## What it does

You type an address. Sightline pulls the aerial tile and measures four things
from the pixels: the roof (area and material), vegetation over and around the
structure, how much of the lot is paved, and the distance to the nearest
building. Those four numbers feed a transparent actuarial model that returns a
safety score, a yearly cost of that risk, and — the screen we actually built
this for — a ranked list of fixes, each with its cost, its annual saving, its
payback period, and its climate co-benefit.

Detection → measurement → risk → dollars → a decision someone would act on.

## How we built it

- **Roof**: Segment Anything (SAM), prompted with the building footprint from
  OpenStreetMap rather than the raw geocoded point — address points routinely
  land on the lawn or the driveway. Zero-shot, no training data.
- **Vegetation and paving**: classical computer vision. Pools excluded,
  surveyed building outlines subtracted, thin lawn strips and sub-15m² grey
  fragments filtered out by geometry.
- **Pricing**: `rate × units` per peril, summed, plus expense loading. The risk
  multiplier is a transparent weighted config, so every dollar on screen
  attributes back to a specific measurement.
- **Mitigations**: change one measured feature, re-price, take the difference.
  That's the annual saving. Cost ÷ saving = payback. Sort ascending.

Python, FastAPI, OpenCV, Ultralytics SAM, React, Vite, Leaflet, Mapbox.

## Challenges we ran into

The honest one: separating a tree crown from a lawn at this resolution doesn't
work. We tested brightness, texture, local contrast, and SAM seeding, and
measured that on our test property the crown is actually *brighter* than the
lawn. There is no signal to threshold on. Rather than ship a number we
couldn't stand behind, we relabelled it **vegetation** — which is what the
detector genuinely measures, and which is the right variable for ember-ignition
risk anyway.

We also found the display and the measurement had drifted apart: the numbers
were correctly scoped to the property while the overlay was painting the whole
tile, including the public road. That mismatch looked like broken computer
vision when the vision was fine — a good reminder that what you show and what
you compute have to be the same thing.

## Accomplishments we're proud of

Every figure traces to a measurement, and every limitation is surfaced in the
product rather than buried. The app tells you when it can't read the imagery's
capture date, when geocoding only resolved to street level, and when the
segmented roof disagrees with the surveyed footprint.

## What we learned

Classical thresholding can't do semantic segmentation — it can only do colour.
Every reliable win came from bringing in a second, independent signal:
geometry, surveyed footprints, or a real segmentation model.

## What's next

Real cadastral parcel boundaries instead of an estimated lot rectangle;
Microsoft Building Footprints for the many addresses OpenStreetMap hasn't
mapped; and per-parcel canopy and impervious figures exported for municipal
stormwater and heat-island planning, which is a by-product this pipeline
already produces.

## Built with

python, fastapi, opencv, segment-anything, ultralytics, react, vite, leaflet,
mapbox, openstreetmap
