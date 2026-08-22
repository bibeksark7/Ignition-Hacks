# Sightline — 3-minute demo script

~450 words at a normal speaking pace. Timings are targets, not gospel —
if you run long, cut from §4, never from §3.

Numbers below are the real output for 9 Roblin Ave, Toronto. If you
re-run and they shift, update them here rather than reading stale figures.

---

## §1 — The hook (0:00–0:30)

> In 1875, a surveyor named Charles Goad started walking Canadian cities
> block by block, drawing every single building to scale and colour-coding
> it by what it was made of. Red for brick. Blue for stone. Yellow for
> wood frame. Insurance underwriters used those plans to price a house
> without ever visiting it.
>
> The industry stopped doing it, because keeping it current by hand got
> too expensive. Not because it was the wrong idea.
>
> This is Sightline. We rebuilt Goad's fire insurance plan — from a
> satellite photo, automatically.

*On screen: the Goad-style overlay on 9 Roblin. Let the red/green/blue
masks sit on screen while you say the colour line — it lands visually.*

---

## §2 — The problem (0:30–1:00)

> Canadian insurers paid out nine point four billion dollars in
> catastrophe claims in 2024. That gets spread across everybody's
> premiums, including people who never filed a claim.
>
> And the homeowner paying it has no idea why. Your bill goes up, nobody
> tells you which part of your property caused it, and nobody tells you
> what to do about it. An inspector could tell you — but that costs
> hundreds of dollars a visit, so it basically never happens.
>
> Every fact you'd need is already sitting in a free aerial photo.

---

## §3 — The demo (1:00–2:10) — **the part that matters, do not cut**

*Type the address live. Let the pipeline steps show.*

> I type in an address. We pull the aerial tile, and segment it.
>
> Roof — four hundred and nineteen square metres, asphalt shingle.
> Vegetation — none overhanging the roof, but eighteen percent of the
> five-metre ring around the house. Paved surface — eight percent of
> the lot, the driveway and the back patio. Nearest building — two point
> three metres away.
>
> Those four measurements are the whole input. Everything after this is
> arithmetic on them.
>
> Safety score: sixty-five out of a hundred. Grade D. Driven mostly by
> regional flood exposure. That prices out to six thousand two hundred
> and thirteen dollars a year.
>
> And here's the screen we actually built this for.

*Scroll to mitigations.*

> Every fix, ranked by payback. What it costs, what it saves per year,
> how long until it pays for itself — and what it does for the climate,
> not just your wallet. Clear the vegetation within five metres: that's
> the single biggest ember-ignition pathway to your house.
>
> That's the difference between a risk score and something you'd
> actually act on.

---

## §4 — How it works + both tracks (2:10–2:40)

> Roof segmentation is Segment Anything, prompted with the building
> footprint from OpenStreetMap — zero-shot, no training data. Vegetation
> and paving are classical computer vision. Pricing is real actuarial
> structure: rate times units, per peril, summed.
>
> Fintech, because it's a pricing engine off a novel data source.
> Environmental, because every single recommendation is a climate
> adaptation measure — and insurance is one of the few levers that
> actually changes behaviour, because the number arrives attached to
> your own money.

---

## §5 — Honest limits + close (2:40–3:00)

> What we won't claim: these are demonstration prices, calibrated to
> published Canadian averages, not an actuarial quote. We can't read the
> photo's capture date, so we say so on screen instead of hiding it. And
> we can't reliably separate a tree crown from a lawn at this resolution
> — so we call it vegetation, which is what we actually measure.
>
> Goad's surveyors did this by hand for a hundred years. We just made it
> an API call.

---

## Delivery notes

- **Record §3 first**, while you're fresh. It's the segment that decides this.
- Say the numbers **as words**, not digits — "four hundred and nineteen",
  not "419". Reads far better in a voiceover.
- §5 is a strength, not an apology. Judges mark honesty up, and every
  limitation named there is one they'd otherwise catch themselves.
- If you overrun, cut §4 down to its first and last sentence.
