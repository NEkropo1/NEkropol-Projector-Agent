from __future__ import annotations

from pathlib import Path
import os
import tempfile

import cv2 as cv
import httpx
from app.logger import logger

MODEL_DIR = Path.home() / ".cache" / "onnx_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / "face_detection_yunet_2023mar.onnx"

YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)

# Global singleton; FastAPI can later stash it into app.state if preferred


def _atomic_download(url: str, dest: Path, min_bytes: int = 100_000) -> None:
    """
    Download to a temp file and rename. Basic size check to avoid HTML or truncated files.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=30.0, follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        tmp_fd, tmp_path = tempfile.mkstemp(prefix="yunet_", suffix=".onnx", dir=str(dest.parent))
        os.close(tmp_fd)
        try:
            Path(tmp_path).write_bytes(r.content)
            sz = Path(tmp_path).stat().st_size
            if sz < min_bytes:
                raise RuntimeError(f"Downloaded file too small ({sz} bytes) — likely not the model.")
            Path(tmp_path).replace(dest)
        except Exception:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise


def ensure_model(path: Path = MODEL_PATH) -> Path:
    if path.exists():
        return path
    logger.info(f"Downloading YuNet ONNX to {path}")
    _atomic_download(YUNET_URL, path)
    logger.info(f"Downloaded YuNet ({path.stat().st_size} bytes)", )
    return path


DEFAULT_INPUT_SIZE = (320, 320)       # (w, h)
DEFAULT_CONF_THRESHOLD = 0.6
DEFAULT_NMS_THRESHOLD = 0.3
DEFAULT_TOPK = 5000
DEFAULT_BACKEND = cv.dnn.DNN_BACKEND_OPENCV
DEFAULT_TARGET = cv.dnn.DNN_TARGET_CPU

_DETECTOR: cv.FaceDetectorYN | None = None  # singleton


def coldstart_yunet() -> cv.FaceDetectorYN:
    """
    Create a single YuNet detector instance. Do NOT download here. Assume MODEL_PATH exists.
    """
    global _DETECTOR
    if _DETECTOR is not None:
        return _DETECTOR

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"YuNet model not found at {MODEL_PATH}")

    logger.info(f"Loading YuNet from {MODEL_PATH}")
    det = cv.FaceDetectorYN.create(
        model=str(MODEL_PATH),
        config="",
        input_size=DEFAULT_INPUT_SIZE,
        score_threshold=DEFAULT_CONF_THRESHOLD,
        nms_threshold=DEFAULT_NMS_THRESHOLD,
        top_k=DEFAULT_TOPK,
        backend_id=DEFAULT_BACKEND,
        target_id=DEFAULT_TARGET,
    )
    _DETECTOR = det
    logger.success(f"YuNet ready: model={MODEL_PATH}, input_size={DEFAULT_INPUT_SIZE}")
    return _DETECTOR
