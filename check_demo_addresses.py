"""Regression check across the fixed demo address set.

Run this after ANY change to vision/ before pushing. It re-analyzes every
demo address, prints the numbers side by side, flags anything implausible,
and writes one overlay image per address to debug_demo/ so the whole set
can be eyeballed at once.

The point: tuning segmentation one address at a time is how you fix a
threshold for house A and silently break house B. The demo set is small
and fixed on purpose (see CONTEXT.md "golden rule") - verify against all
of it, every time.

    .venv\\Scripts\\python.exe check_demo_addresses.py
"""

import os

import cv2
import numpy as np

from vision.pipeline import analyze_with_images

DEMO_ADDRESSES = [
    "85 Pitt Ave, Scarborough, ON",
    "149A Pitt Ave, Scarborough, ON",
    "149B Pitt Ave, Scarborough, ON",
    "68A Bexhill Ave, Scarborough, ON",
    "68B Bexhill Ave, Scarborough, ON",
    "84 Bexhill Ave, Scarborough, ON",
    "440 Pharmacy Ave, Scarborough, ON",
    "9 Roblin Ave, Toronto, ON",
]

OUTPUT_DIR = "debug_demo"

# Sanity ranges for a detached/semi-detached Canadian home. Outside these,
# something is wrong even if the pipeline reported itself confident.
EXPECTED = {
    "roof_area_m2": (60, 700),
    "impervious_pct": (2, 70),
    "canopy_within_5m_pct": (0, 90),
}


def _overlay(images: dict) -> np.ndarray:
    out = images["tile"].copy()
    for key, colour in (
        ("impervious_mask", (40, 100, 220)),
        ("canopy_mask", (40, 200, 60)),
        ("roof_mask", (220, 40, 40)),
    ):
        m = images[key]
        out[m] = (0.5 * out[m] + 0.5 * np.array(colour)).astype("uint8")
    return out


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    problems = []

    header = f"{'address':<36} {'roof m2':>8} {'lot m2':>8} {'imperv%':>8} {'can5m%':>8} {'conf':>5}  flags"
    print(header)
    print("-" * len(header))

    for address in DEMO_ADDRESSES:
        try:
            result, images = analyze_with_images(address)
        except Exception as exc:  # noqa: BLE001 - a failure here is itself the finding
            print(f"{address:<36} FAILED: {exc}")
            problems.append(f"{address}: raised {type(exc).__name__}")
            continue

        flags = []
        if not result["roof_segmentation_plausible"]:
            flags.append("implausible")
        for field, (low, high) in EXPECTED.items():
            value = result[field]
            if not low <= value <= high:
                flags.append(f"{field}={value} outside {low}-{high}")

        short = address.split(",")[0]
        print(
            f"{short:<36} {result['roof_area_m2']:>8.1f} {result['lot_area_m2']:>8.1f} "
            f"{result['impervious_pct']:>8.1f} {result['canopy_within_5m_pct']:>8.1f} "
            f"{result['confidence']:>5.2f}  {', '.join(flags) if flags else 'ok'}"
        )
        if flags:
            problems.append(f"{short}: {', '.join(flags)}")

        slug = short.lower().replace(" ", "_").replace(",", "")
        cv2.imwrite(
            os.path.join(OUTPUT_DIR, f"{slug}.png"),
            cv2.cvtColor(_overlay(images), cv2.COLOR_RGB2BGR),
        )

    print()
    if problems:
        print(f"{len(problems)} address(es) need a look:")
        for p in problems:
            print(f"  - {p}")
    else:
        print(f"All {len(DEMO_ADDRESSES)} demo addresses within expected ranges.")
    print(f"Overlays written to {OUTPUT_DIR}/ - eyeball them before pushing.")


if __name__ == "__main__":
    main()
