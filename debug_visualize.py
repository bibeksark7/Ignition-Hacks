import sys

import numpy as np
import cv2

from vision import imagery, segmentation, features, footprints

lat, lon = 43.5183, -79.8774
if len(sys.argv) == 3:
    lat, lon = float(sys.argv[1]), float(sys.argv[2])

tile = imagery.fetch_tile(lat, lon)
image = np.array(tile["image"])
center = (image.shape[1] // 2, image.shape[0] // 2)

osm = footprints.query_buildings(lat, lon)
m_per_px = features.meters_per_pixel(lat, tile["zoom"], tile["retina"])
neighbor_mask = features.rasterize_local_polygons(osm["other_building_polygons_m"], image.shape, m_per_px)

roof_mask = segmentation.segment_roof(image, center)
canopy_mask = segmentation.segment_canopy(image)
impervious_mask = segmentation.segment_impervious(image, exclude_mask=roof_mask | neighbor_mask)

overlay = image.copy()
overlay[roof_mask] = (0.5 * overlay[roof_mask] + 0.5 * np.array([220, 40, 40])).astype("uint8")
overlay[canopy_mask] = (0.5 * overlay[canopy_mask] + 0.5 * np.array([40, 200, 60])).astype("uint8")
overlay[impervious_mask] = (0.5 * overlay[impervious_mask] + 0.5 * np.array([40, 100, 220])).astype("uint8")
cv2.circle(overlay, center, 5, (255, 255, 0), -1)

out_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
cv2.imwrite("debug_overlay.png", out_bgr)
cv2.imwrite("debug_original.png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
print("Saved debug_overlay.png and debug_original.png")
print(f"roof px={roof_mask.sum()} canopy px={canopy_mask.sum()} impervious px={impervious_mask.sum()}")
