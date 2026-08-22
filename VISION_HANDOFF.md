# Vision segmentation — handoff brief

Everything here is about `vision/segmentation.py` and `vision/pipeline.py`.
Read this before changing either. It exists because several of these
problems were already solved once, and re-solving them from scratch is how
they get re-broken.

## How to verify your work (do this every time)

```bash
.venv\Scripts\python.exe check_demo_addresses.py
```

Runs all 8 demo addresses, prints their numbers, flags anything outside
sane ranges, and writes an overlay image per address to `debug_demo/`.
**Look at the overlays.** The numbers alone will not tell you the mask is
painting a neighbour's roof.

Tuning against one address is exactly how a threshold gets fixed for house
A and silently broken for house B — that happened repeatedly. The demo set
is small and fixed on purpose; verify against all of it.

Note: the first run of a new address takes ~15-20s (SAM inference), and
results are cached in `data/cache/`. **Clear that cache after changing
segmentation code** or you'll be looking at stale masks and concluding your
fix did nothing:

```bash
rm -f data/cache/*.json
```

## Already fixed — please don't undo these

Each of these cost real debugging time. If your change reverts one, the
regression script should catch it.

1. **Display masks are clipped to the property** (`pipeline.py`, where the
   `images` dict is built: `canopy_mask & lot_mask`). The measurements were
   always scoped to the lot; the *displayed* masks weren't, so the UI painted
   the public road and neighbours' yards. This looked like "the CV is broken"
   when the numbers were fine. Keep display and measurement on the same region.
2. **Roof uses an OSM footprint bounding box + centroid point as the SAM
   prompt**, not the raw geocoded point. Geocoded address points frequently
   land on the lawn or driveway. Box pad is 8m — tested at 3m and it clipped
   real roofs, because SAM treats the box as a near-hard constraint.
3. **Roof plausibility tolerance is 0.25x–6.5x** vs the OSM footprint.
   It has been tightened and loosened several times. Mismatches of 3.6x,
   3.8x and 5.6x were all verified against real imagery as *correct*
   segmentations — OSM footprints are frequently outdated/undersized
   (additions not re-surveyed). Tighten this and you will start rejecting
   good results. The check only needs to catch gross failures (~32x).
4. **Overpass (OSM) lookups retry 3x.** Without it the same address
   intermittently returned wildly different results (3.6 m² one run, 428 m²
   the next) because a silent API failure downgraded SAM to weak point-only
   prompting.
5. **Mask PNGs encode the mask in the alpha channel**, not greyscale
   (`api.py`, `_mask_png_data_uri`). Opaque greyscale PNGs are treated by
   some browsers as "fully visible" under CSS `mask-image`, which tinted
   the entire photo.
6. **Pools are excluded from impervious** (`segment_pool`), and **lawn is
   excluded from canopy** via a local-variance texture filter (tree crowns
   have leaf/shadow variance, mown grass doesn't).

## What's actually left

### Task A — impervious surface still catches some neighbouring roof
**Best fit: Workstream 02** (Python, and you've already been reading this
code successfully).

Grey asphalt and a grey shingle roof are near-identical in colour, so
colour thresholding alone cannot separate them. Current approach in
`_drop_building_width_regions()`: a driveway is narrow (~3-4m across) no
matter how long it runs, a house is wide in both directions — so a
morphological opening with a 6m disc finds "too wide to be paving" regions
and subtracts them.

It works partially. On `9 Roblin Ave` the lower neighbour's roof is
correctly cleared and the driveway is preserved, but grey area near the
upper neighbour still comes through.

Ideas worth trying, roughly in order of effort:
- Tune `_MIN_BUILDING_SHORT_SIDE_M` (currently 6.0). Watch both failure
  directions: too high leaves roofs in, too low eats the driveway.
- Shrink the lot region. `features.lot_region_mask()` approximates the lot
  as a circle around the roof, which reaches well into neighbouring
  properties. Real lots are narrow and deep — an oriented rectangle
  aligned to the building would overlap neighbours far less.
- Use SAM (already loaded) to segment neighbouring structures directly
  rather than relying on OSM footprints, which are often missing. More
  robust, but costs inference time per request.

### Task B — canopy quality pass
**Best fit: whoever has time; it's more bounded than Task A.**

Canopy is much better since the display clipping (contiguous shapes on the
property rather than specks across the whole tile). Remaining work is a
quality pass rather than a bug hunt:
- `segment_canopy()` closes with a 31x31 kernel to merge leaf clusters into
  crowns. Check it holds across all 8 addresses, not just one.
- The texture threshold (`local_var > 25.0`) is what separates tree from
  lawn. Verify it behaves on the shaded addresses in the set.
- Sanity-check `canopy_overlap_pct` — several demo addresses report 0.0,
  which may be correct (no overhang) or may be too strict.

## Ground rules

- Run `check_demo_addresses.py` before pushing. Look at the overlays.
- If you change a threshold, say in the commit message which addresses you
  verified it against.
- If a fix seems to have no effect, clear `data/cache/` and restart the
  server without `--reload` — hot reload has silently served stale code
  more than once in this project.
