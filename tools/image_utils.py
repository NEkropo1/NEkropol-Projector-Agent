
from __future__ import annotations
from urllib.parse import urlparse


def looks_like_image_url(url: str) -> bool:
    try:
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp"))
    except Exception:
        return False
