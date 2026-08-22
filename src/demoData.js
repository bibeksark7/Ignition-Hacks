import { DEMO_FIXTURES } from './demoData.generated'

/* ---------------------------------------------------------------------------
   Offline demo mode.

   CONTEXT.md's fallback ladder, rung 4: stored results, real interface, honest
   framing. Add ?demo=1 to the URL and the app stops calling the network and
   serves the cached pricing-engine output for the three sample locations
   instead. Nothing here is hand-written: demoData.generated.js is built from
   pricing/demo_cache/*.json, which engine.py produced.

   Demo mode always paints a banner across the top. Cached numbers must never
   be mistaken for a live run, least of all by us on stage.
--------------------------------------------------------------------------- */

export function isDemoMode() {
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).get('demo') != null
}

// Fixtures are keyed to the sample coordinates in AddressMap. Roughly 300 m of
// tolerance, enough that nudging the pin onto the roof still resolves.
const MATCH_DEGREES = 0.004

export function findDemoFixture({ lat, lon }) {
  if (lat == null || lon == null) return DEMO_FIXTURES[0]
  return (
    DEMO_FIXTURES.find(
      (f) => Math.abs(f.lat - lat) < MATCH_DEGREES && Math.abs(f.lon - lon) < MATCH_DEGREES,
    ) ?? null
  )
}
