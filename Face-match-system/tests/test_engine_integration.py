"""Real-model checks. Skipped unless the buffalo_l model and the FG-NET images are present."""

from pathlib import Path

import pytest

from facematch.config import PROJECT_ROOT
from facematch.engine import FaceEngine, decode_image
from facematch.matching import cosine_score

pytestmark = pytest.mark.integration

FGNET = PROJECT_ROOT / "Datasets" / "FGNET" / "images"
CFP = PROJECT_ROOT / "Datasets" / "cfp-dataset" / "Data" / "Images"
MODEL_DIR = Path.home() / ".insightface" / "models" / "buffalo_l"

if not (MODEL_DIR.is_dir() and FGNET.is_dir() and CFP.is_dir()):
    pytest.skip("model or datasets not available", allow_module_level=True)


@pytest.fixture(scope="module")
def engine():
    return FaceEngine()


def embed(engine, path):
    faces = engine.detect(decode_image(path.read_bytes()))
    assert len(faces) == 1, path
    return faces[0].embedding


def test_same_person_scores_higher_than_different_person(engine):
    a = embed(engine, CFP / "001" / "frontal" / "01.jpg")
    same = embed(engine, CFP / "001" / "frontal" / "02.jpg")
    other = embed(engine, CFP / "002" / "frontal" / "01.jpg")
    assert cosine_score(a, same) > cosine_score(a, other) + 0.2


def test_tight_crop_detected_via_padding_fallback(engine):
    # CFP frontal crops fail without padding (the face fills the frame).
    image = decode_image((CFP / "001" / "frontal" / "01.jpg").read_bytes())
    assert engine.detect(image, pad=False) == []
    faces = engine.detect(image)
    assert len(faces) == 1
    x1, y1, x2, y2 = faces[0].bbox
    h, w = image.shape[:2]
    assert 0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h  # bbox mapped back to original image coords
