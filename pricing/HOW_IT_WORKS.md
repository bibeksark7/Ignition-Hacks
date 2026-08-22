# How the pricing engine works (pitch notes)

Written for whoever presents — answers "how do you know the premiums are right?"
before a judge has to ask it.

## The one-paragraph version

We don't use a black box. The premium is `rate × units × risk_multiplier`, the
same structure every real home insurer uses, with the multiplier built from a
transparent weighted formula instead of a hidden model. Every rate and cost is
anchored to a real published source, not invented. The risk score shown to
the homeowner is calculated from *the same multiplier* that sets the price —
so the score and the price can never contradict each other, which is not
something any real insurer currently guarantees a customer.

## The math, in order

1. **Vision measurements in** (Workstream 01): roof area, canopy overlap,
   impervious surface %, distance to nearest structure, roof material/damage.
2. **Location hazard lookup**: flood/wildfire/wind exposure by coordinate
   (named Canadian catastrophe hotspots + provincial fallback — placeholder
   for the real Canada Flood Map Inventory / CWFIS datasets).
3. **Risk multiplier per peril** (fire, water, wind/hail): `1.0 + Σ(weight ×
   normalized risk factor)`, weights live in one config file, nowhere else.
4. **Risk score (0–100, higher = safer)**: a straight linear rescale of that
   same multiplier. This is the key design choice — the score isn't a
   separate model, it's the price wearing a different unit.
5. **Premium**: `base_rate_peril × multiplier × (coverage / $100)`, summed
   across perils, plus an expense loading — the actual formula real insurers
   use (frequency × severity → rate → premium).
6. **Mitigations**: for each candidate fix, change the one feature it affects,
   re-run steps 3–5, take the difference. Sort by payback. No separate model —
   it's the same pricing function run twice.

## Why the numbers are defensible despite being a "demo"

- **Base rates** are anchored to the Insurance Bureau of Canada's ~$1,200/yr
  and Ratehub/BlueCouch's ~$1,340/yr published national average premium
  (2026), not picked to look good.
- **Every mitigation cost** is sourced from a real Canadian pricing guide
  (HomeStars, RenoQuotes, PlumbingQuotes, etc. — full list below), not a
  round number we liked.
- **We didn't cherry-pick to make paybacks look impressive.** Cheap, targeted
  fixes (tree limb removal) pencil out in single-digit years; big structural
  upgrades (metal roof, permeable driveway) have long, honest paybacks
  because those materials/labour genuinely cost that much in Canada right
  now. A judge who does their own napkin math on our numbers will get
  numbers close to ours.
- **What's actually a demonstration, stated plainly**: the *weights* that
  turn a measurement into a risk multiplier are our own calibration, not a
  real actuarial rate table — because that data is proprietary to insurers
  and doesn't exist publicly. That's the one thing we don't pretend to have.

## The hard questions, answered

| Question | Answer |
|---|---|
| How do you know the premiums are right? | We don't claim they're an actual quote. The rate structure, base rates, and every mitigation cost are real and sourced. The risk weights that connect a measurement to a multiplier are our own calibration — that's the part that would need a real insurer's proprietary loss data to perfect, and we say so. |
| Why should I trust a risk score I've never seen before? | Because it's not a separate opaque score — it's a direct rescaling of the same number that sets the price. If you don't trust the score, you're also not trusting the price, and you can check our math for both from one config file. |
| Isn't this just marketing dressed up as data? | The opposite — no insurer today attributes a premium to specific measured causes for a customer. We do, for every dollar, because a transparent weighted model comes free once you choose not to build a black box. |
| Why do some mitigations have 50+ year paybacks? | Because that's honest. Replacing a roof or a driveway is a resilience investment, not something that pays for itself on insurance savings alone — real contractors will tell you the same thing. We'd rather show that plainly than inflate the numbers to look better. |
| What would it take to make this real? | Real per-peril actuarial loss data from an insurer (replacing our calibrated weights), and the real Canada Flood Map Inventory / CWFIS wildfire datamart (replacing our named-hotspot approximation) — both swappable behind the same function signatures we already have. |

## Sources for every dollar figure

- [Ratehub — inflation & home insurance rates](https://www.ratehub.ca/blog/inflation-home-insurance-rates-canada/)
- [BlueCouch — home insurance cost in Canada 2026](https://bluecouchinsurance.com/blog/home-insurance-cost-canada-2026)
- [HomeStars — tree removal cost guide](https://www.homestars.com/gardening-outdoors/price-guides/tree-removal-cost)
- [Ontario Plumbing Quotes — backwater valve cost](https://plumbingquotes.ca/blog/backwater-valve-cost-ontario)
- [HomeGuide — permeable pavers cost](https://homeguide.com/costs/permeable-pavers-cost)
- [RenoQuotes — metal roof cost per sq ft in Canada 2026](https://renoquotes.com/en/blog/metal-roof-cost-per-square-foot-in-canada-in-2026)
- [HomeStars — roof repair costs](https://www.homestars.com/roofing/price-guides/roof-repair-costs)
- [lfbuilders — gutter guard cost 2025](https://blog.lfbuilders.ca/blog/how-much-does-gutterguard-cost-in-2025/)
- [The Goat Land Clearing — vegetation management costs](https://www.thegoatlandclearing.ca/vegetation-management-chilliwack-abbotsford)
- [US Made Supply — ember-resistant vent guide](https://usmadesupply.com/resources/guides/ember-resistant-vent-guide)

All figures also cited inline as comments in `pricing/config.py`.
