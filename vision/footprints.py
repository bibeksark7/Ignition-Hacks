import math

import requests

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_SEARCH_RADIUS_M = 60


def _to_local_xy(lat, lon, lat0, lon0):
    x = (lon - lon0) * 111320.0 * math.cos(math.radians(lat0))
    y = (lat - lat0) * 110540.0
    return x, y


def _polygon_area(coords):
    area = 0.0
    n = len(coords)
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _point_in_polygon(px, py, coords):
    inside = False
    n = len(coords)
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        if ((y1 > py) != (y2 > py)) and (
            px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1
        ):
            inside = not inside
    return inside

def _point_to_segment_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x, proj_y = x1 + t * dx, y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def _polygon_centroid(coords):
    """Area-weighted (shoelace) centroid - correct for irregular building
    shapes, unlike a plain vertex average."""
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(coords)
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area *= 0.5
    if abs(area) < 1e-9:
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        return sum(xs) / n, sum(ys) / n
    cx /= 6 * area
    cy /= 6 * area
    return cx, cy


def _polygon_min_dist(coords_a, coords_b):
    best = float("inf")
    for i in range(len(coords_b)):
        x1, y1 = coords_b[i]
        x2, y2 = coords_b[(i + 1) % len(coords_b)]
        for px, py in coords_a:
            best = min(best, _point_to_segment_dist(px, py, x1, y1, x2, y2))
    return best


def query_buildings(lat: float, lon: float) -> dict:
    """Nearby building footprints from OSM, in local metre coordinates.

    Returns {"target_area_m2", "nearest_structure_m"} using real geometry
    when OSM has coverage at this location, or None values if it doesn't
    (sparse in many residential areas - caller should fall back to defaults).
    """
    query = (
        "[out:json][timeout:15];"
        f"way(around:{_SEARCH_RADIUS_M},{lat},{lon})[\"building\"];"
        "out geom;"
    )
    try:
        resp = requests.post(
            _OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": "sightline-hackathon/0.1", "Accept": "*/*"},
            timeout=20,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except (requests.RequestException, ValueError):
        return {"target_area_m2": None, "nearest_structure_m": None, "other_building_polygons_m": [], "target_centroid_m": None}

    polygons = []
    for el in elements:
        geom = el.get("geometry")
        if not geom or len(geom) < 3:
            continue
        coords = [_to_local_xy(p["lat"], p["lon"], lat, lon) for p in geom]
        polygons.append(coords)

    if not polygons:
        return {"target_area_m2": None, "nearest_structure_m": None, "other_building_polygons_m": [], "target_centroid_m": None}

    target = None
    for poly in polygons:
        if _point_in_polygon(0.0, 0.0, poly):
            target = poly
            break
    if target is None:
        target = min(polygons, key=lambda p: min(math.hypot(x, y) for x, y in p))

    others = [p for p in polygons if p is not target]
    nearest = (
        min(_polygon_min_dist(target, o) for o in others) if others else None
    )

    return {
        "target_area_m2": round(_polygon_area(target), 1),
        "nearest_structure_m": round(nearest, 1) if nearest is not None else None,
        "other_building_polygons_m": others,
        "target_centroid_m": _polygon_centroid(target),
    }
