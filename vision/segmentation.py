import numpy as np
import cv2

_sam_model = None


def _get_sam():
    global _sam_model
    if _sam_model is None:
        from ultralytics import SAM

        _sam_model = SAM("sam_b.pt")
    return _sam_model


def segment_roof(image: np.ndarray, point_xy: tuple) -> np.ndarray:
    """Zero-shot roof mask from a single point prompt at the parcel centre.

    SAM's raw output often has small holes around roof vents, ridge lines,
    and shadowed patches - real gaps in an otherwise coherent roof, not
    signal. A morphological close (dilate then erode) bridges those without
    growing the mask's actual outer boundary."""
    model = _get_sam()
    results = model(image, points=[list(point_xy)], labels=[1], verbose=False)
    mask = results[0].masks.data[0].cpu().numpy().astype(np.uint8)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return closed.astype(bool)


def segment_canopy(image: np.ndarray) -> np.ndarray:
    """Tree canopy via HSV thresholding, distinguished from flat lawn by
    local texture: tree cover has leaf/shadow variance that mowed grass
    doesn't, so a low-variance green region is classified as lawn, not
    canopy - the two carry very different fire risk.

    The raw texture filter fires on individual leaf clusters/shadow gaps,
    which reads as sparse speckles rather than a canopy shape - a real
    tree crown has small gaps in it too, they just shouldn't visually
    fragment the whole thing. A morphological close merges nearby
    speckles into the contiguous canopy patches they're actually part of,
    without touching well-separated trees or expanding onto the lawn."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([25, 40, 30])
    upper = np.array([95, 255, 255])
    green_mask = cv2.inRange(hsv, lower, upper).astype(bool)

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
    mean = cv2.blur(gray, (9, 9))
    local_var = cv2.blur((gray - mean) ** 2, (9, 9))
    textured = local_var > 25.0

    canopy = (green_mask & textured).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    closed = cv2.morphologyEx(canopy, cv2.MORPH_CLOSE, kernel)
    return closed.astype(bool)


def segment_pool(image: np.ndarray) -> np.ndarray:
    """Swimming pool water: saturated blue/turquoise, distinct from the
    low-saturation grey of pavement/concrete. Called out explicitly in
    the project brief as a naive-thresholding trap - without this, pale
    or sun-glared pool water reads as impervious pavement."""
    # Saturation bound is lower than a strict "pool blue" to also catch
    # pale/sun-glared water (chlorine-blue lap pools often wash out nearly
    # white) - hue stays tightly bounded to cyan/blue since that's what
    # keeps this from also matching grey pavement.
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([85, 20, 120])
    upper = np.array([130, 255, 255])
    return cv2.inRange(hsv, lower, upper).astype(bool)


def segment_impervious(image: np.ndarray, exclude_mask: np.ndarray = None) -> np.ndarray:
    """Grey asphalt/concrete via HSV thresholding (low saturation, mid-high
    value). Pools are excluded - see segment_pool - since a pool is not
    pavement, even though naive thresholding often confuses the two."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([0, 0, 60])
    upper = np.array([180, 40, 210])
    mask = cv2.inRange(hsv, lower, upper).astype(bool)
    mask &= ~segment_pool(image)
    if exclude_mask is not None:
        mask &= ~exclude_mask
    return mask
