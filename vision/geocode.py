import requests

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode(address: str) -> dict:
    """Address -> {lat, lon, display_name}. Uses OSM Nominatim (free, no key)."""
    resp = requests.get(
        _NOMINATIM_URL,
        params={"q": address, "format": "json", "limit": 1},
        headers={"User-Agent": "sightline-hackathon/0.1"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"No geocoding match for address: {address!r}")

    top = results[0]
    return {
        "lat": float(top["lat"]),
        "lon": float(top["lon"]),
        "display_name": top["display_name"],
    }
