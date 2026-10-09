import numpy as np
import pytest

from facematch.matching import DetectedFace, ImageStatus, cosine_score, match_reference, select_face


def face(vec, bbox=(0, 0, 10, 10)):
    v = np.asarray(vec, dtype=np.float32)
    return DetectedFace(bbox, 0.9, v / np.linalg.norm(v))


def test_select_face_invalid_image():
    assert select_face("x.jpg", None, None).status is ImageStatus.INVALID_IMAGE


def test_select_face_no_face():
    assert select_face("x.jpg", [], None).status is ImageStatus.NO_FACE


def test_select_face_single_face_is_auto_selected():
    a = select_face("x.jpg", [face([1, 0])], None)
    assert a.status is ImageStatus.OK and a.selected_face == 0


def test_select_face_multiple_faces_requires_choice():
    a = select_face("x.jpg", [face([1, 0]), face([0, 1])], None)
    assert a.status is ImageStatus.MULTIPLE_FACES
    assert a.selected_face is None and len(a.faces) == 2
    assert a.embedding is None


def test_select_face_explicit_index():
    a = select_face("x.jpg", [face([1, 0]), face([0, 1])], 1)
    assert a.status is ImageStatus.OK
    np.testing.assert_allclose(a.embedding, [0, 1])


@pytest.mark.parametrize("index", [2, -1])
def test_select_face_out_of_range_index(index):
    assert select_face("x.jpg", [face([1, 0]), face([0, 1])], index).status is ImageStatus.INVALID_FACE_INDEX


def test_cosine_score_is_clamped_to_unit_interval():
    assert cosine_score(np.array([1.0, 0]), np.array([1.0, 0])) == pytest.approx(1.0)
    assert cosine_score(np.array([1.0, 0]), np.array([-1.0, 0])) == 0.0


def test_match_reference_scores_each_candidate_against_threshold():
    ref = select_face("ref.jpg", [face([1, 0])], None)
    same = select_face("a.jpg", [face([0.9, 0.1])], None)
    other = select_face("b.jpg", [face([0.1, 0.9])], None)
    missing = select_face("c.jpg", [], None)

    report = match_reference(ref, [same, other, missing], threshold=0.5)

    assert [c.match for c in report.candidates] == [True, False, None]
    assert report.candidates[2].score is None
    assert not report.complete


def test_match_reference_unusable_reference_scores_nothing():
    ref = select_face("ref.jpg", [face([1, 0]), face([0, 1])], None)
    report = match_reference(ref, [select_face("a.jpg", [face([1, 0])], None)], threshold=0.5)
    assert report.candidates[0].score is None and report.candidates[0].match is None
