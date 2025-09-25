import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _CvModule:
    IMREAD_COLOR = object()

    class dnn:
        DNN_BACKEND_OPENCV = 0
        DNN_TARGET_CPU = 0

    class FaceDetectorYN:
        @staticmethod
        def create(*args, **kwargs):  # pragma: no cover - safety net
            raise RuntimeError("cv2 stub should not create detectors in tests")

    @staticmethod
    def imencode(ext, image):
        return False, b""

    @staticmethod
    def imdecode(arr, flag):
        return None


sys.modules.setdefault("cv2", _CvModule)
