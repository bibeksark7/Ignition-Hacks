import { useState, useRef } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import 'leaflet/dist/leaflet.css'

const pinIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

// Free OSM geocoder — no API key needed, fine for hackathon use.
// Swap for Mapbox/Esri geocoding later if rate limits or coverage become an issue.
async function geocodeAddress(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  const results = await res.json()
  if (!results.length) return null
  return { lat: Number(results[0].lat), lon: Number(results[0].lon), label: results[0].display_name }
}

function DraggablePin({ position, onMove }) {
  const markerRef = useRef(null)

  useMapEvents({
    click(e) {
      onMove({ lat: e.latlng.lat, lon: e.latlng.lng })
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
          if (marker) {
            const { lat, lng } = marker.getLatLng()
            onMove({ lat, lon: lng })
          }
        },
      }}
    />
  )
}

export default function AddressMap({ onConfirm, loading }) {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('idle') // idle | searching | found | error
  const [pin, setPin] = useState(null)
  const [label, setLabel] = useState('')

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setStatus('searching')
    try {
      const result = await geocodeAddress(query)
      if (!result) {
        setStatus('error')
        return
      }
      setPin({ lat: result.lat, lon: result.lon })
      setLabel(result.label)
      setStatus('found')
    } catch {
      setStatus('error')
    }
  }

  return (
    <div className="address-map-block">
      <form className="address-entry" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Enter a home address..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={status === 'searching'}>
          {status === 'searching' ? 'Searching...' : 'Find on map'}
        </button>
      </form>

      {status === 'error' && (
        <p className="map-hint map-hint-error">Couldn't find that address — try adding city and province.</p>
      )}

      {pin && (
        <>
          <p className="map-hint">
            Drag the pin, or click the map, to point at the exact building — geocoding sometimes lands on the
            wrong house.
          </p>
          <div className="map-wrap">
            <MapContainer
              center={[pin.lat, pin.lon]}
              zoom={19}
              scrollWheelZoom
              style={{ height: '320px', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <DraggablePin position={pin} onMove={setPin} />
            </MapContainer>
          </div>
          <button
            type="button"
            className="confirm-button"
            disabled={loading}
            onClick={() => onConfirm({ address: label || query, lat: pin.lat, lon: pin.lon })}
          >
            {loading ? 'Analyzing...' : 'Confirm this location'}
          </button>
        </>
      )}
    </div>
  )
}
