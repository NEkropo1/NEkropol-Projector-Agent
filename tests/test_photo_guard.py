import base64

import numpy as np
import pytest

import guards.photo_guard as pg


class DummyClient:
    def __init__(self, content=b"bytes"):
        self._content = content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url):  # pragma: no cover - ensures url preserved
        class Resp:
            def __init__(self, content):
                self.content = content

            def raise_for_status(self):
                pass

        return Resp(self._content)


class DummyDetector:
    def __init__(self, faces):
        self.faces = faces
        self.input_size = None

    def setInputSize(self, size):
        self.input_size = size

    def detect(self, img):
        return None, self.faces


def test__to_bytes_handles_various_inputs(monkeypatch):
    arr = np.zeros((1, 1, 3), dtype=np.uint8)
    monkeypatch.setattr(
        pg.cv,
        "imencode",
        lambda ext, image: (True, np.array([1, 2, 3], dtype=np.uint8)),
    )
    result_nd = pg._to_bytes(arr)
    assert result_nd == bytes(np.array([1, 2, 3], dtype=np.uint8))

    raw = b"raw"
    assert pg._to_bytes(raw) == raw

    b64 = base64.b64encode(b"data").decode()
    assert pg._to_bytes(b64) == b"data"

    data_url = "data:text/plain;base64," + b64
    assert pg._to_bytes(data_url) == b"data"

    def fake_client(timeout, follow_redirects):
        return DummyClient(b"http-bytes")

    monkeypatch.setattr(pg.httpx, "Client", fake_client)
    assert pg._to_bytes("http://example.com/img.jpg") == b"http-bytes"

    assert pg._to_bytes("not base64") is None


def test_image_has_person_no_bytes(monkeypatch):
    monkeypatch.setattr(pg, "_to_bytes", lambda image: None)
    monkeypatch.setattr(pg, "coldstart_yunet", lambda: DummyDetector(np.zeros((0,))))
    assert pg.image_has_person("anything") is False


def test_image_has_person_decode_failure(monkeypatch):
    monkeypatch.setattr(pg, "_to_bytes", lambda image: b"bytes")
    monkeypatch.setattr(pg, "coldstart_yunet", lambda: DummyDetector(np.zeros((0,))))
    monkeypatch.setattr(pg.cv, "imdecode", lambda buf, flags: None)
    assert pg.image_has_person("data") is False


@pytest.mark.parametrize(
    "faces,threshold,expected",
    [
        (np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7]]), 0.6, True),
        (np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5]]), 0.6, False),
    ],
)
def test_image_has_person_threshold(monkeypatch, faces, threshold, expected):
    monkeypatch.setattr(pg, "_to_bytes", lambda image: b"bytes")
    monkeypatch.setattr(
        pg.np, "frombuffer", lambda buffer, dtype: np.zeros((1,), dtype=np.uint8)
    )
    monkeypatch.setattr(
        pg.cv, "imdecode", lambda arr, flags: np.zeros((10, 5, 3), dtype=np.uint8)
    )
    det = DummyDetector(faces)
    monkeypatch.setattr(pg, "coldstart_yunet", lambda: det)

    assert pg.image_has_person("img", threshold=threshold) is expected
    assert det.input_size == (5, 10)
