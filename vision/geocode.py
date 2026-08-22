import requests

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _region_key(addr: dict) -> str:
    city = (addr.get("city") or addr.get("town") or addr.get("village") or "").strip()
    state = (addr.get("state") or "").strip()
    if not city or not state:
        return "default"

    province_abbrev = {
        "ontario": "on", "quebec": "qc", "british columbia": "bc",
        "alberta": "ab", "manitoba": "mb", "saskatchewan": "sk",
        "nova scotia": "ns", "new brunswick": "nb",
        "newfoundland and labrador": "nl", "prince edward island": "pe",
    }.get(state.lower())
    if not province_abbrev:
        return "default"

    key = f"{city.lower().replace(' ', '_')}_{province_abbrev}"
    return key


def geocode(address: str) -> dict:
    """Address -> {lat, lon, display_name, region_key}. Uses OSM Nominatim (free, no key)."""
    resp = requests.get(
        _NOMINATIM_URL,
        params={"q": address, "format": "json", "limit": 1, "addressdetails": 1},
        headers={"User-Agent": "sightline-hackathon/0.1"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"No geocoding match for address: {address!r}")

    top = results[0]
    addresstype = top.get("addresstype", "")
    # "place" covers OSM place=house nodes, which are a common and usually
    # accurate way residential points are tagged in Canada - treating only
    # "house"/"building" as precise wrongly flagged real, well-placed
    # addresses as low-confidence.
    is_precise = addresstype in ("house", "building", "place")

    return {
        "lat": float(top["lat"]),
        "lon": float(top["lon"]),
        "display_name": top["display_name"],
        "region_key": _region_key(top.get("address", {})),
        "address_precision": addresstype,
        "is_precise_match": is_precise,
    }
