import { findDemoFixture, isDemoMode } from './demoData'

// Override per-machine in .env.local (gitignored) as VITE_VISION_API_BASE / VITE_PRICING_API_BASE
// so this doesn't need editing every time whoever's running a server changes.
// 8010 matches the vision server command in CONTEXT.md §14. This defaulted to
// 8000, so anyone without a .env.local (i.e. a fresh clone) silently failed to
// reach vision at all.
const VISION_API_BASE = import.meta.env.VITE_VISION_API_BASE || 'http://localhost:8010'
const PRICING_API_BASE = import.meta.env.VITE_PRICING_API_BASE || 'http://localhost:8001'

// Workstream 01's endpoint: address/lat+lon -> Contract A features + imagery/mask PNGs.
async function fetchVision({ address, lat, lon }) {
  const params = new URLSearchParams()
  if (lat != null && lon != null) {
    params.set('lat', lat)
    params.set('lon', lon)
  } else if (address) {
    params.set('address', address)
  }

  const res = await fetch(`${VISION_API_BASE}/analyze?${params.toString()}`)
  if (!res.ok) {
    throw new Error(`Vision request failed (${res.status})`)
  }
  return res.json()
}

// Workstream 02's endpoint: Contract A JSON in -> Contract B pricing out.
async function fetchPricing(contractA) {
  const res = await fetch(`${PRICING_API_BASE}/price`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(contractA),
  })
  if (!res.ok) {
    throw new Error(`Pricing request failed (${res.status})`)
  }
  return res.json()
}

// Chains vision -> pricing since the two services aren't merged behind one
// endpoint yet. Returns { ...contractA fields, ...imagery/mask fields, ...contractB fields }.
//
// With ?demo=1 in the URL this serves cached pricing-engine output instead of
// touching the network (fallback ladder rung 4 in CONTEXT.md). The UI paints a
// banner whenever that mode is on, so cached figures never read as live ones.
// A saved run of the real pipeline over 9 Roblin: the same tile and the same
// three mask PNGs the vision server produced, written to public/demo/ as
// files, plus every number the pricing engine returned. It exists because the
// two Python services can't be hosted on Vercel - a static host can serve a
// React build but not a 360MB segmentation model - so without this a deployed
// link would load the interface and then fail the moment anyone measured
// anything. Regenerate with scripts/build_saved_analysis.py.
const SAVED_ANALYSIS_URL = '/demo/9-roblin/analysis.json'
const SAVED_ANALYSIS_AT = { lat: 43.69592, lon: -79.32303 }

// Anywhere the two local services could plausibly be listening. Off localhost
// there is no backend to reach, so don't spend a fetch timeout finding out.
function backendIsReachable() {
  const h = window.location.hostname
  return h === 'localhost' || h === '127.0.0.1' || /^192\.168\./.test(h) || /^10\./.test(h)
}

function nearSavedAnalysis(lat, lon) {
  if (lat == null || lon == null) return false
  // ~50m. Tight enough that a different house never borrows these numbers.
  return Math.abs(lat - SAVED_ANALYSIS_AT.lat) < 0.0005 && Math.abs(lon - SAVED_ANALYSIS_AT.lon) < 0.0007
}

async function loadSavedAnalysis({ lat, lon }) {
  if (!nearSavedAnalysis(lat, lon)) {
    // Deliberately an error rather than serving 9 Roblin's figures for
    // whatever was typed. Wrong numbers under the right address is the one
    // failure mode here that would actually mislead someone.
    throw new Error(
      'This deployment ships one saved analysis, for 9 Roblin Avenue. Measuring a new address needs the vision and pricing services running locally - see the README.',
    )
  }
  const res = await fetch(SAVED_ANALYSIS_URL)
  if (!res.ok) throw new Error('Could not load the saved analysis.')
  const saved = await res.json()
  // Let the pipeline steps be readable instead of flashing past.
  await new Promise((r) => setTimeout(r, 2200))
  return saved
}

export async function fetchAnalysis({ address, lat, lon }) {
  if (isDemoMode()) {
    const fixture = findDemoFixture({ lat, lon })
    if (!fixture) {
      throw new Error(
        'Demo mode is on, but this location is not one of the three cached sample properties. Turn demo mode off, or pick a sample location.',
      )
    }
    // Hold briefly so the pipeline steps are legible rather than flashing past.
    await new Promise((r) => setTimeout(r, 2600))
    return fixture
  }

  // Served from anywhere but a local network - a Vercel deployment - there is
  // no backend, so go straight to the saved run.
  if (!backendIsReachable()) {
    return loadSavedAnalysis({ lat, lon })
  }

  try {
    const vision = await fetchVision({ address, lat, lon })
    const pricing = await fetchPricing(vision)
    return { ...vision, ...pricing }
  } catch (err) {
    // Running locally but the servers aren't up: fall back rather than dying,
    // so a fresh clone still shows something real.
    if (nearSavedAnalysis(lat, lon)) return loadSavedAnalysis({ lat, lon })
    throw err
  }
}
