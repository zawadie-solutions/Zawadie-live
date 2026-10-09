"""API tests with a fake detector: an image's color encodes its faces.

red channel   -> identity of face 0 (face k has identity red + k)
blue channel  -> number of faces (blue // 50)
"""

import io
import json
import logging

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from facematch.api import create_app, parse_candidate_faces
from facematch.config import Settings
from facematch.matching import DetectedFace


class FakeEngine:
    model_name = "fake"

    def detect(self, image):
        b, _, r = (int(v) for v in image[0, 0])  # BGR
        faces = []
        for k in range(b // 50):
            emb = np.zeros(16, dtype=np.float32)
            emb[(r + k) % 16] = 1.0
            faces.append(DetectedFace((0, 0, 10 - k, 10 - k), 0.99, emb))
        return faces


def png(identity: int, n_faces: int = 1) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (identity, 0, n_faces * 50)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client(tmp_path):
    settings = Settings(threshold=0.5, threshold_source="test", log_path=str(tmp_path / "log.jsonl"))
    with TestClient(create_app(FakeEngine(), settings)) as c:
        yield c


def post(client, reference, candidates, **form):
    files = [("reference", ("ref.png", reference, "image/png"))]
    files += [("candidates", (f"c{i}.png", c, "image/png")) for i, c in enumerate(candidates)]
    return client.post("/match", files=files, data={k: str(v) for k, v in form.items()})


def test_reference_vs_candidates(client):
    r = post(client, png(3), [png(3), png(7)])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["threshold"] == 0.5
    assert [(c["candidate_index"], c["match"], c["score"]) for c in body["results"]] == [(0, True, 1.0), (1, False, 0.0)]


def test_threshold_override(client):
    body = post(client, png(3), [png(7)], threshold=0.0).json()
    assert body["threshold"] == 0.0 and body["results"][0]["match"] is True


@pytest.mark.parametrize("bad", [1.5, -0.1])
def test_threshold_out_of_range_rejected(client, bad):
    assert post(client, png(3), [png(3)], threshold=bad).status_code == 422


def test_multi_face_reference_lists_faces_and_scores_nothing(client):
    body = post(client, png(3, n_faces=2), [png(3)]).json()
    assert body["status"] == "incomplete"
    assert body["reference"]["status"] == "multiple_faces"
    assert [f["index"] for f in body["reference"]["faces"]] == [0, 1]
    assert body["results"][0]["match"] is None


def test_resubmit_with_face_selection(client):
    # Reference face 1 has identity 4; candidate 0's second face (index 1) also has identity 4.
    body = post(client, png(3, n_faces=2), [png(3, n_faces=2)], reference_face=1, candidate_faces="0:1").json()
    assert body["status"] == "ok"
    assert body["results"][0]["match"] is True


def test_no_face_and_invalid_image_are_reported_per_candidate(client):
    files = [("reference", ("ref.png", png(3), "image/png")),
             ("candidates", ("empty.png", png(3, n_faces=0), "image/png")),
             ("candidates", ("junk.png", b"not an image", "image/png")),
             ("candidates", ("ok.png", png(3), "image/png"))]
    body = client.post("/match", files=files).json()
    assert [c["status"] for c in body["results"]] == ["no_face", "invalid_image", "ok"]
    assert body["results"][2]["match"] is True


def test_invalid_face_index(client):
    body = post(client, png(3), [png(3)], reference_face=5).json()
    assert body["reference"]["status"] == "invalid_face_index"


def test_bad_candidate_faces_format_rejected(client):
    assert post(client, png(3), [png(3)], candidate_faces="zero:one").status_code == 422
    assert post(client, png(3), [png(3)], candidate_faces="4:0").status_code == 422


def test_request_log_is_metadata_only(client, caplog):
    with caplog.at_level(logging.INFO, logger="facematch.requests"):
        post(client, png(3), [png(3)])
    entry = json.loads(caplog.records[-1].getMessage())
    assert entry["results"][0]["score"] == 1.0 and "elapsed_ms" in entry
    assert "embedding" not in caplog.records[-1].getMessage()


def test_upload_page_is_served_and_self_contained(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    # Photos never leave the machine: the page must not pull anything from other sites.
    assert "http://" not in r.text and "https://" not in r.text and "//" + "fonts." not in r.text


def test_local_font_is_served(client):
    r = client.get("/static/fonts/plus-jakarta-sans-latin-wght-normal.woff2")
    assert r.status_code == 200 and len(r.content) > 10_000


def test_health(client):
    assert client.get("/health").json()["threshold"] == 0.5


def test_parse_candidate_faces():
    assert parse_candidate_faces("0:1, 2:0", 3) == {0: 1, 2: 0}
    assert parse_candidate_faces("", 1) == {}
