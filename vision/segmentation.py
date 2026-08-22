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
    """Green vegetation via HSV thresholding."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([25, 40, 30])
    upper = np.array([95, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    return mask.astype(bool)


def segment_impervious(image: np.ndarray, exclude_mask: np.ndarray = None) -> np.ndarray:
    """Grey asphalt/concrete via HSV thresholding (low saturation, mid-high value)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower = np.array([0, 0, 60])
    upper = np.array([180, 40, 210])
    mask = cv2.inRange(hsv, lower, upper).astype(bool)
    if exclude_mask is not None:
        mask &= ~exclude_mask
    return mask
