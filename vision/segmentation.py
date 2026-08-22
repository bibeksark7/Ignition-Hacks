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
    """Zero-shot roof mask from a single point prompt at the parcel centre."""
    model = _get_sam()
    results = model(image, points=[list(point_xy)], labels=[1], verbose=False)
    mask = results[0].masks.data[0].cpu().numpy()
    return mask.astype(bool)


def segment_canopy(image: np.ndarray) -> np.ndarray:
    """Tree canopy via HSV thresholding, distinguished from flat lawn by
    local texture: tree cover has leaf/shadow variance that mowed grass
    doesn't, so a low-variance green region is classified as lawn, not
    canopy - the two carry very different fire risk."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([25, 40, 30])
    upper = np.array([95, 255, 255])
    green_mask = cv2.inRange(hsv, lower, upper).astype(bool)

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
    mean = cv2.blur(gray, (9, 9))
    local_var = cv2.blur((gray - mean) ** 2, (9, 9))
    textured = local_var > 25.0

    return green_mask & textured


def segment_impervious(image: np.ndarray, exclude_mask: np.ndarray = None) -> np.ndarray:
    """Grey asphalt/concrete via HSV thresholding (low saturation, mid-high value)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([0, 0, 60])
    upper = np.array([180, 40, 210])
    mask = cv2.inRange(hsv, lower, upper).astype(bool)
    if exclude_mask is not None:
        mask &= ~exclude_mask
    return mask
