import hashlib
import json
import os

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache")


def _slug(address: str) -> str:
    return hashlib.sha1(address.strip().lower().encode()).hexdigest()[:12]


def load(address: str) -> dict:
    path = os.path.join(_CACHE_DIR, f"{_slug(address)}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def save(address: str, result: dict) -> str:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = os.path.join(_CACHE_DIR, f"{_slug(address)}.json")
    payload = {"address": address, **result}
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


def analyze_cached(address: str, force_refresh: bool = False) -> dict:
    from .pipeline import analyze

    if not force_refresh:
        cached = load(address)
        if cached is not None:
            return cached

    result = analyze(address)
    save(address, result)
    return result
