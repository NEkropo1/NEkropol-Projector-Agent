# guards/face_detector.py
from __future__ import annotations

import base64
from typing import Optional, Union

import cv2 as cv
import numpy as np
import httpx
from loguru import logger

from app.coldstart.dirty_hacks_to_backlog import coldstart_yunet


def _to_bytes(image: Union[bytes, str, np.ndarray]) -> Optional[bytes]:
    try:
        if isinstance(image, bytes):
            return image
        if isinstance(image, np.ndarray):
            ok, buf = cv.imencode(".jpg", image)
            return bytes(buf) if ok else None
        if isinstance(image, str):
            s = image.strip()
            if s.startswith(("http://", "https://")):
                with httpx.Client(timeout=10.0, follow_redirects=True) as c:
                    r = c.get(s)
                    r.raise_for_status()
                    return r.content
            if s.startswith("data:"):
                _, b64 = s.split(",", 1)
                return base64.b64decode(b64)
            # raw base64 attempt
            try:
                return base64.b64decode(s, validate=True)
            except Exception:
                return None
        return None
    except Exception:
        return None


def image_has_person(
        image: Union[bytes, str, np.ndarray],
        threshold: float = 0.6
) -> bool:
    """
    True if YuNet detects at least one face with conf >= threshold.
    Uses OpenCV's FaceDetectorYN (YuNet) exactly like the Zoo code.
    """
    det = coldstart_yunet()

    buf = _to_bytes(image)
    if not buf:
        logger.warning("image_has_person: no bytes")
        return False

    arr = np.frombuffer(buf, dtype=np.uint8)
    img = cv.imdecode(arr, cv.IMREAD_COLOR)
    if img is None:
        logger.error("image_has_person: cv.imdecode failed")
        return False

    # YuNet expects BGR; set input size to the current image size (w, h)
    h, w = img.shape[:2]
    det.setInputSize((w, h))

    # detect() returns (retval, faces); faces is None or Nx15
    # columns: [x, y, w, h, 5*2 landmarks..., score]
    _, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        logger.info("YuNet: no faces")
        return False

    # Take the best confidence
    confs = faces[:, -1].astype(float)
    best = float(np.max(confs))
    logger.info("YuNet best conf = {:.4f}", best)
    return best >= threshold
