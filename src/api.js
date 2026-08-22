// Override per-machine in .env.local (gitignored) as VITE_VISION_API_BASE / VITE_PRICING_API_BASE
// so this doesn't need editing every time whoever's running a server changes.
const VISION_API_BASE = import.meta.env.VITE_VISION_API_BASE || 'http://localhost:8000'
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
export async function fetchAnalysis({ address, lat, lon }) {
  const vision = await fetchVision({ address, lat, lon })
  const pricing = await fetchPricing(vision)
  return { ...vision, ...pricing }
}
