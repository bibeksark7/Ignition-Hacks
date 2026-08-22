import base64
import logging

import cv2
import numpy as np
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("sightline.api")

from vision.pipeline import analyze_with_images, analyze_at_with_images
from vision.cache import load as cache_load, save as cache_save

try:
    from pricing.engine import analyze as price_analyze
except ImportError:
    # pricing/ only exists once Workstream 02's branch is merged in - keep
    # this endpoint usable standalone (features + images only) until then.
    price_analyze = None

app = FastAPI(title="Sightline - Workstream 01 Vision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _png_data_uri(image: np.ndarray) -> str:
    """RGB photo -> PNG data URI."""
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".png", bgr)
    if not ok:
        raise RuntimeError("PNG encoding failed")
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()


def _mask_png_data_uri(mask: np.ndarray) -> str:
    """Mask -> RGBA PNG data URI with the mask in the ALPHA channel.

    Accepts either a boolean mask or a graduated float mask in [0, 1] (see
    features.canopy_display_alpha, which fades canopy by distance from the
    structure so the overlay ranks severity instead of painting one flat
    tint). Both encode into alpha the same way.

    A plain opaque grayscale PNG is unreliable for CSS mask-image: some
    browsers treat an image with no transparency as "fully revealed"
    everywhere, ignoring the black/white content entirely - which is
    exactly the bug where toggling a layer tinted the whole photo instead
    of just the detected shape. Encoding the mask as alpha (white RGB,
    alpha = mask) is the convention that reads correctly everywhere,
    since CSS masking multiplies luminance by alpha regardless of mode.
    """
    h, w = mask.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0:3] = 255
    if mask.dtype == bool:
        rgba[..., 3] = mask.astype(np.uint8) * 255
    else:
        # Casting a float mask to uint8 first would truncate every partial
        # value to 0, silently erasing everything but full-strength pixels.
        rgba[..., 3] = np.clip(mask * 255.0, 0, 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", rgba)
    if not ok:
        raise RuntimeError("PNG encoding failed")
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()


def _build_response(result: dict, images: dict) -> dict:
    return {
        **result,
        "imagery_png": _png_data_uri(images["tile"]),
        "roof_mask_png": _mask_png_data_uri(images["roof_mask"]),
        "canopy_mask_png": _mask_png_data_uri(images["canopy_mask"]),
        "impervious_mask_png": _mask_png_data_uri(images["impervious_mask"]),
    }


@app.get("/analyze")
def analyze_endpoint(
    address: str = Query(None, description="Street address to analyze"),
    lat: float = Query(None, description="Latitude, used with lon after pin-confirm"),
    lon: float = Query(None, description="Longitude, used with lat after pin-confirm"),
    fresh: bool = Query(False, description="Bypass the demo-address cache"),
):
    """Workstream 01's half of the contract: address or pin-confirmed
    coordinates -> features + estimated value + mask/imagery PNGs.
    Does not include Workstream 02's risk_score/premium fields - those
    are merged in by whatever combines both workstreams' output."""
    if not address and (lat is None or lon is None):
        raise HTTPException(400, "Provide either `address` or both `lat` and `lon`.")

    cache_key = address or f"{lat},{lon}"
    if not fresh:
        cached = cache_load(cache_key)
        if cached is not None:
            return cached

    try:
        if address:
            result, images = analyze_with_images(address)
        else:
            result, images = analyze_at_with_images(lat, lon)
    except ValueError as e:
        # geocode.geocode raises this when the address has no match
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        # e.g. imagery.fetch_tile when MAPBOX_TOKEN isn't configured
        raise HTTPException(500, f"Server configuration error: {e}")
    except requests.HTTPError as e:
        raise HTTPException(502, f"Upstream imagery/geocoding service error: {e}")
    except requests.RequestException as e:
        raise HTTPException(504, f"Upstream service timeout or connection error: {e}")
    except Exception:
        logger.exception("Unexpected error analyzing %s", cache_key)
        raise HTTPException(500, "Internal error processing this address.")

    pricing = {}
    if price_analyze is not None:
        try:
            pricing = price_analyze(result, coverage_amount=None)
        except ValueError as e:
            raise HTTPException(422, str(e))
        except Exception:
            # Don't let a pricing bug throw away the vision half of the
            # response, which is already computed - degrade gracefully.
            logger.exception("Pricing engine failed, returning vision-only response")

    response = {**_build_response(result, images), **pricing}
    cache_save(cache_key, response)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}
