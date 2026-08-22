import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// A plain CSS marker instead of Leaflet's default blue teardrop, which fights
// the palette. Two concentric rings, no artwork.
const pinIcon = L.divIcon({
  className: 'pin-icon',
  html: '<span class="pin-icon-dot"></span>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

// Known-good coordinates rather than address strings: picking one of these
// skips the geocoder entirely, so a demo never waits on a third-party lookup.
// Regional descriptions only, nothing that pre-empts what the pipeline returns.
const DEMO_PINS = [
  // First on purpose: this is the walkthrough property. Its analysis is
  // pre-cached on the vision server, so it returns instantly instead of
  // running a cold segmentation pass in front of an audience.
  { label: '9 Roblin Ave, Toronto', note: 'Semi-detached, driveway and back patio', lat: 43.69592, lon: -79.32303 },
  { label: 'Jasper, Alberta', note: 'Wildland urban interface', lat: 52.8734, lon: -118.0814 },
  { label: 'Downtown Toronto', note: 'Dense block, heavily paved', lat: 43.6532, lon: -79.3832 },
  { label: 'North York, Toronto', note: 'Detached, open lot', lat: 43.7, lon: -79.42 },
]

// Free OSM geocoder, no API key needed. Swap for Mapbox/Esri if rate limits or
// Canadian residential coverage become a problem.
async function geocodeAddress(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  const results = await res.json()
  if (!results.length) return null
  return { lat: Number(results[0].lat), lon: Number(results[0].lon), label: results[0].display_name }
}

// Nominatim returns the full administrative chain, which is far too long for a
// heading. Keep the parts a person would actually say out loud.
function shortenAddress(label, fallback) {
  if (!label) return fallback || ''
  const parts = label.split(',').map((s) => s.trim()).filter(Boolean)
  if (parts.length <= 3) return parts.join(', ')
  return parts.slice(0, 3).join(', ')
}

// Recentres when the pin arrives from a search or a sample pick. Deliberately
// does nothing when the user dragged the pin themselves, since yanking the map
// out from under someone mid-drag is disorienting.
function RecenterOnPin({ position }) {
  const map = useMap()
  useEffect(() => {
    if (position.fromMap) return
    map.setView([position.lat, position.lon], 19)
  }, [map, position.lat, position.lon, position.fromMap])
  return null
}

function DraggablePin({ position, onMove }) {
  const markerRef = useRef(null)

  useMapEvents({
    click(e) {
      onMove({ lat: e.latlng.lat, lon: e.latlng.lng, fromMap: true })
    },
  })

  return (
    <Marker
      position={[position.lat, position.lon]}
      icon={pinIcon}
      draggable
      ref={markerRef}
      eventHandlers={{
        dragend() {
          const marker = markerRef.current
          if (!marker) return
          const { lat, lng } = marker.getLatLng()
          onMove({ lat, lon: lng, fromMap: true })
        },
      }}
    />
  )
}

export default function AddressMap({ onConfirm, loading }) {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('idle') // idle | searching | found | notfound | error
  const [pin, setPin] = useState(null)
  const [label, setLabel] = useState('')

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setStatus('searching')
    try {
      const result = await geocodeAddress(query)
      if (!result) {
        setStatus('notfound')
        return
      }
      setPin({ lat: result.lat, lon: result.lon })
      setLabel(result.label)
      setStatus('found')
    } catch {
      setStatus('error')
    }
  }

  const pickDemo = (demo) => {
    setQuery(demo.label)
    setLabel(demo.label)
    setPin({ lat: demo.lat, lon: demo.lon })
    setStatus('found')
  }

  const confirm = () => {
    if (!pin) return
    onConfirm({
      address: label || query,
      displayAddress: shortenAddress(label, query),
      lat: pin.lat,
      lon: pin.lon,
    })
  }

  return (
    <div className="finder">
      <form className="finder-form" onSubmit={handleSearch}>
        <label className="field-label" htmlFor="address-input">
          Your home address
        </label>
        <div className="field-row">
          <input
            id="address-input"
            type="text"
            autoComplete="street-address"
            placeholder="123 Example St, Milton, ON"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn btn-primary" disabled={status === 'searching'}>
            {status === 'searching' ? 'Searching' : 'Find home'}
          </button>
        </div>
        <p className="field-help">
          We look up the address, then you place the pin on the roof yourself before anything is
          measured.
        </p>
      </form>

      {status === 'notfound' && (
        <p className="inline-error" role="status">
          No match for that address. Adding the city and province usually fixes it.
        </p>
      )}
      {status === 'error' && (
        <p className="inline-error" role="status">
          The address lookup did not respond. Try again, or drop a pin using one of the sample
          locations.
        </p>
      )}

      <div className="demo-picks">
        <span className="demo-picks-label">Or start from a sample location</span>
        <div className="demo-picks-row">
          {DEMO_PINS.map((d) => (
            <button
              key={d.label}
              type="button"
              className="chip"
              onClick={() => pickDemo(d)}
              disabled={loading}
            >
              <span className="chip-title">{d.label}</span>
              <span className="chip-note">{d.note}</span>
            </button>
          ))}
        </div>
      </div>

      {pin && (
        <div className="confirm-step">
          <div className="confirm-head">
            <h2 className="confirm-title">Is the pin on your roof?</h2>
            <p className="confirm-copy">
              Drag it, or click anywhere on the map. Address lookup often lands on the street or the
              house next door, and everything we measure comes from wherever this pin sits.
            </p>
          </div>

          <div className="map-frame">
            <MapContainer
              center={[pin.lat, pin.lon]}
              zoom={19}
              scrollWheelZoom
              style={{ height: '380px', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>, &copy; OpenStreetMap contributors'
                url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
              />
              <RecenterOnPin position={pin} />
              <DraggablePin position={pin} onMove={setPin} />
            </MapContainer>
          </div>

          <button type="button" className="btn btn-primary btn-block" disabled={loading} onClick={confirm}>
            {loading ? 'Measuring' : 'Measure this home'}
          </button>
        </div>
      )}
    </div>
  )
}
