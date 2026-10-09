"""InsightFace wrapper: image decoding, detection + alignment, and ArcFace embeddings."""

from __future__ import annotations

import io
import warnings

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from .matching import DetectedFace

# insightface's alignment calls a deprecated scikit-image API; harmless noise.
warnings.filterwarnings("ignore", category=FutureWarning, module="insightface")

# Fraction of the longer side added as black border when retrying detection.
# RetinaFace misses faces that fill the whole frame (tight crops, scanned portraits).
PAD_RATIO = 0.5


def decode_image(data: bytes) -> np.ndarray | None:
    """Decode bytes to a BGR uint8 array, honoring EXIF orientation. None if undecodable."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    except (UnidentifiedImageError, OSError, ValueError):
        return None


class FaceEngine:
    def __init__(self, model_name: str = "buffalo_l", det_size: int = 640, det_thresh: float = 0.5):
        from insightface.app import FaceAnalysis

        self.model_name = model_name
        self._app = FaceAnalysis(
            name=model_name,
            allowed_modules=["detection", "recognition"],
            providers=["CPUExecutionProvider"],
        )
        self._app.prepare(ctx_id=-1, det_thresh=det_thresh, det_size=(det_size, det_size))

    def detect(self, image: np.ndarray, pad: bool | None = None) -> list[DetectedFace]:
        """Detect, align and embed every face, largest first.

        pad=None tries the raw image and retries with a border if nothing is found;
        pad=True goes straight to the padded image (for datasets of tight crops).
        """
        faces, offset = [], 0
        if not pad:
            faces = self._app.get(image)
        if not faces and pad is not False:
            h, w = image.shape[:2]
            offset = int(max(h, w) * PAD_RATIO / 2)
            padded = cv2.copyMakeBorder(image, offset, offset, offset, offset, cv2.BORDER_CONSTANT, value=0)
            faces = self._app.get(padded)

        h, w = image.shape[:2]
        detected = []
        for f in faces:
            x1, y1, x2, y2 = (float(v) - offset for v in f.bbox)
            bbox = (max(x1, 0.0), max(y1, 0.0), min(x2, float(w)), min(y2, float(h)))
            detected.append(DetectedFace(bbox, float(f.det_score), np.asarray(f.normed_embedding, dtype=np.float32)))
        detected.sort(key=lambda d: (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]), reverse=True)
        return detected
