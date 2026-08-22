import io

import requests
from PIL import Image

from . import config

_STATIC_URL = (
    "https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/"
    "{lon},{lat},{zoom}/{size}x{size}{retina}"
)


def fetch_tile(lat: float, lon: float, zoom: int = None) -> dict:
    """Fetch a satellite tile centred on (lat, lon). Returns image + metadata."""
    if not config.MAPBOX_TOKEN:
        raise RuntimeError(
            "MAPBOX_TOKEN is not set. Copy .env.example to .env and add your "
            "token from https://account.mapbox.com/access-tokens/"
        )

    zoom = zoom or config.DEFAULT_ZOOM
    retina = "@2x" if config.RETINA else ""
    url = _STATIC_URL.format(
        lon=lon, lat=lat, zoom=zoom, size=config.TILE_SIZE, retina=retina
    )
    resp = requests.get(url, params={"access_token": config.MAPBOX_TOKEN}, timeout=15)
    resp.raise_for_status()

    image = Image.open(io.BytesIO(resp.content)).convert("RGB")
    return {
        "image": image,
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "retina": config.RETINA,
        # Mapbox's Static Images API doesn't expose per-tile capture/vintage
        # date anywhere (checked response headers - nothing there either).
        # Showing today's date here would be actively misleading, since it
        # looks precise but isn't real - the brief itself says to flag
        # stale tiles, and we can't do that with a fabricated timestamp.
        "imagery_date": None,
    }
