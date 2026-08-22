import base64
import io

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from vision.pipeline import analyze_with_images, analyze_at_with_images
from vision.cache import load as cache_load, save as cache_save

app = FastAPI(title="Sightline - Workstream 01 Vision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _png_data_uri(array: np.ndarray) -> str:
    is_bgr = array.ndim == 3 and array.shape[2] == 3
    encode_input = cv2.cvtColor(array, cv2.COLOR_RGB2BGR) if is_bgr else (array.astype(np.uint8) * 255)
    ok, buf = cv2.imencode(".png", encode_input)
    if not ok:
        raise RuntimeError("PNG encoding failed")
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()


def _build_response(result: dict, images: dict) -> dict:
    return {
        **result,
        "imagery_png": _png_data_uri(images["tile"]),
        "roof_mask_png": _png_data_uri(images["roof_mask"]),
        "canopy_mask_png": _png_data_uri(images["canopy_mask"]),
        "impervious_mask_png": _png_data_uri(images["impervious_mask"]),
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

    if address:
        result, images = analyze_with_images(address)
    else:
        result, images = analyze_at_with_images(lat, lon)

    response = _build_response(result, images)
    cache_save(cache_key, response)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}
