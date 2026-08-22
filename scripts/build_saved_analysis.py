"""Regenerate the saved analysis the deployed site serves.

The hosted build has no backend - Vercel runs a React bundle, not a 360MB
segmentation model - so it ships one real, precomputed run instead. This
script captures that run from the live services and writes it to public/.

Run it whenever the vision or pricing output changes, or the deployed site
will keep showing figures the local pipeline no longer produces:

    # with both services running
    .venv\\Scripts\\python.exe scripts/build_saved_analysis.py

Nothing here invents a number. It records what the pipeline returned.
"""

import base64
import json
import os

import requests

VISION = "http://127.0.0.1:8010"
PRICING = "http://127.0.0.1:8001"

# The property the pipeline has been tuned and verified against.
LAT, LON = 43.69592, -79.32303
OUT_DIR = os.path.join("public", "demo", "9-roblin")

# Written as files rather than inlined base64: the browser caches them, and a
# 1.1MB tile does not belong in a JSON payload parsed on every load.
IMAGE_FIELDS = {
    "imagery_png": "imagery.png",
    "roof_mask_png": "roof.png",
    "canopy_mask_png": "canopy.png",
    "impervious_mask_png": "impervious.png",
}


def main() -> None:
    vision = requests.get(f"{VISION}/analyze", params={"lat": LAT, "lon": LON}, timeout=300)
    vision.raise_for_status()
    contract_a = vision.json()

    pricing = requests.post(f"{PRICING}/price", json=contract_a, timeout=120)
    pricing.raise_for_status()
    contract_b = pricing.json()

    os.makedirs(OUT_DIR, exist_ok=True)

    merged = {k: v for k, v in {**contract_a, **contract_b}.items() if not k.endswith("_png")}
    for field, filename in IMAGE_FIELDS.items():
        path = os.path.join(OUT_DIR, filename)
        with open(path, "wb") as f:
            f.write(base64.b64decode(contract_a[field].split(",", 1)[1]))
        # Same key the frontend already reads; a URL works in `url(...)`
        # exactly like a data URI, so no component needs to change.
        merged[field] = f"/demo/9-roblin/{filename}"
        print(f"  {filename}  {os.path.getsize(path) // 1024} KB")

    merged["is_saved_analysis"] = True
    with open(os.path.join(OUT_DIR, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=1)

    score = merged.get("risk_score", {}).get("overall")
    print(f"  analysis.json  score {score}, ${merged.get('annual_premium')}, roof {merged.get('roof_area_m2')} m2")


if __name__ == "__main__":
    main()
