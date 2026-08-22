# Impervious surface — handoff

Everything here is `segment_impervious()` in `vision/segmentation.py` plus
`lot_region_mask()` in `vision/features.py`. Read this before changing
either. It exists because most of these problems were solved once already,
and three of them got re-broken by re-solving them from scratch.

## How to verify (do this every time)

```bash
rm -f data/cache/*.json
python check_demo_addresses.py
```

Runs all 8 demo addresses and writes an overlay per address to
`debug_demo/`. **Look at the overlays.** Every single regression in this
area passed the numeric range check — 68A Bexhill reported "ok" at 45.6%
while painting a flat grey roof solid blue. The numbers cannot tell you
the mask is on the wrong surface.

Clear `data/cache/` first or you will be looking at stale masks and
concluding your change did nothing.

## Current state

| Address | impervious % |
|---|---|
| 85 Pitt | 18.8 |
| 149A Pitt | 3.5 |
| 149B Pitt | 3.3 |
| 68A Bexhill | 8.4 |
| 68B Bexhill | 4.0 |
| 84 Bexhill | 29.2 |
| 440 Pharmacy | 12.4 |
| 9 Roblin | 14.8 |

All 8 within range, all at confidence 0.75, 28 pricing tests pass.

## The core difficulty

A shingle roof and asphalt are the same grey. The raw HSV threshold
matches **~49% of the whole tile** — every roof, the road, the sidewalks.
Everything after that is an attempt to carve the paving back out of that,
and every stage is a trade between leaving roof in and cutting driveway
out. There is no threshold that separates the two by colour, because
there is no colour difference. Keep that in mind before reaching for a
threshold tweak.

## Already fixed — please don't undo these

Each cost real debugging time, and the first three were each re-broken
once by someone reasoning from first principles without the evidence.

1. **The width filter is unconditional.** `_drop_building_width_regions`
   removes grey regions wide in both directions. It was tried as
   "skip it when OSM gives us surveyed building outlines, since the
   buildings are then already subtracted". That fails: **OSM footprints
   sit 2.4–7.6 m off the Mapbox imagery** (measured centroid offsets —
   68A 7.6 m, 440 Pharmacy 5.5 m, 85 Pitt 5.8 m, 9 Roblin 2.4 m), so the
   outlines miss the roofs they are meant to remove. With the filter off,
   68A reported 45.6% with blue across a flat grey roof; with it on, 8.4%.
   The threshold matters too — 6 m clears the leak, 8 m does not.
2. **Vegetation is excluded by excess-green, not HSV saturation.**
   Saturation is chroma relative to brightness, so grass in shade scores
   as low-saturation "grey" and lands in the paving mask — this is why
   blue was appearing on lawns. `_vegetation()` uses
   `G - (R+B)/2 > 6`, which is brightness-independent.
3. **The lot region is an oriented rectangle, not a circle.** A circle
   sized to match lot area has to reach far in every direction, which
   pushes it deep into both neighbours, and their grey roofs then count as
   this property's paving. The rectangle takes the roof's own orientation,
   clears ~3 m sideways, and extends front-to-back.
4. **The lot rectangle extends at least 10 m past each end of the house.**
   The displayed masks are clipped to this region (`impervious_mask &
   lot_mask` in `pipeline.py`). A shorter rectangle crops the driveway
   half-way along and leaves a halo of paving around the house, which
   reads as "the CV is broken" even when the numbers are fine.
5. **Degenerate roof masks fall back to the circular buffer.**
   `_MIN_ROOF_SHARE_OF_LOT` in `features.py`. A 3.6 m² roof mask (a vent,
   segmented when the footprint lookup failed) produced a sliver rectangle
   and `impervious_pct` became a ratio against almost no area.
6. **Mask edges are simplified to polygons** (`approxPolyDP`, ~0.5 m
   tolerance). Pixel-wise boundaries wobble around every shadow and tyre
   mark and look like noise beside SAM's clean roof outline.

## What was tried and did not work

- **Protecting wide grey inside our own lot** (on the reasoning that the
  roof is already excluded, so wide grey inside the lot must be a patio).
  The roof mask is frequently incomplete — SAM catches part of a roof, or
  falls back to a box prompt — and the uncaught part is grey and inside
  the lot. Painted the un-segmented half of a townhouse roof solid blue
  (440 Pharmacy, 70.4%).
- **SAM building-subtraction.** Prompt SAM at each large grey blob, keep
  the building-shaped masks, subtract them. Better on 9 Roblin (11.0% →
  31.7%) but much worse on 440 Pharmacy (9.1% → 71.2%) — SAM found only 2
  buildings from 5 prompts on a townhouse row. Prototype is not in the
  repo; it was not reliable enough to ship.

## What is actually left

### The parking pad problem (the real one)
The width filter removes anything wide in both directions. A parking pad
*is* wide in both directions. So pads are still partially cut. This is the
central unresolved tension: the same test that stops roof leakage removes
large paved areas. Any fix has to distinguish roof from pavement by
something other than width or colour.

Directions worth trying, roughly by effort:
- **Correct the OSM offset before subtracting.** The footprints are the
  right shapes, just misregistered. Aligning the target polygon to SAM's
  roof mask (both describe the same building) gives a per-tile offset that
  could be applied to all polygons. If that lands, the outline subtraction
  becomes trustworthy and the width filter can genuinely go, which is what
  unlocks the pads.
- **Shadow/height cues.** Buildings cast shadows with a consistent
  direction and offset; flat paving does not. Expensive to get right.
- **A pretrained aerial land-cover model.** Correct answer, wrong week —
  needs weights that classify impervious surface directly. Training from
  scratch is not viable here.

### Smaller items
- **84 Bexhill sits at 29.2%**, the highest of the set. Not obviously
  wrong, but it is the one to look at first.
- **Semi-detached pairs (68A/68B)** — SAM segments one unit and the other
  half of the same building can read as paving. Currently held in check by
  the width filter rather than solved.

## Contract note

`impervious_pct` feeds Workstream 02's water risk multiplier and, through
it, the premium. It does not need to be perfect, but it must not be
*confidently* wrong — a plausible number over a mask sitting on a roof is
worse than an obviously odd one, because nothing downstream can catch it.
The mask is also shown to judges, so a visibly wrong overlay costs more
than a few percentage points of accuracy.
