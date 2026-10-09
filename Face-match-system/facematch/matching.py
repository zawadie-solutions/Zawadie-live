"""Model-free matching logic: face selection per image and reference-vs-candidate scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


@dataclass(frozen=True)
class DetectedFace:
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 in original image pixels
    det_score: float
    embedding: np.ndarray = field(repr=False)  # L2-normalized


class ImageStatus(str, Enum):
    OK = "ok"
    INVALID_IMAGE = "invalid_image"
    NO_FACE = "no_face"
    MULTIPLE_FACES = "multiple_faces"  # caller must pick a face index and re-submit
    INVALID_FACE_INDEX = "invalid_face_index"


@dataclass
class ImageAnalysis:
    filename: str
    status: ImageStatus
    faces: list[DetectedFace]
    selected_face: int | None = None

    @property
    def embedding(self) -> np.ndarray | None:
        if self.status is not ImageStatus.OK:
            return None
        return self.faces[self.selected_face].embedding


@dataclass
class CandidateResult:
    index: int
    image: ImageAnalysis
    score: float | None
    match: bool | None


@dataclass
class MatchReport:
    reference: ImageAnalysis
    candidates: list[CandidateResult]
    threshold: float

    @property
    def complete(self) -> bool:
        """True when every image yielded exactly one usable face and was scored."""
        return self.reference.status is ImageStatus.OK and all(
            c.image.status is ImageStatus.OK for c in self.candidates
        )


def select_face(filename: str, faces: list[DetectedFace] | None, face_index: int | None) -> ImageAnalysis:
    """Resolve which face in an image to use. Never guesses when there are several faces."""
    if faces is None:
        return ImageAnalysis(filename, ImageStatus.INVALID_IMAGE, [])
    if not faces:
        return ImageAnalysis(filename, ImageStatus.NO_FACE, [])
    if face_index is not None:
        if 0 <= face_index < len(faces):
            return ImageAnalysis(filename, ImageStatus.OK, faces, face_index)
        return ImageAnalysis(filename, ImageStatus.INVALID_FACE_INDEX, faces)
    if len(faces) == 1:
        return ImageAnalysis(filename, ImageStatus.OK, faces, 0)
    return ImageAnalysis(filename, ImageStatus.MULTIPLE_FACES, faces)


def cosine_score(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity clamped to [0, 1]; negative similarity means 'clearly different'."""
    sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    return min(max(sim, 0.0), 1.0)


def match_reference(reference: ImageAnalysis, candidates: list[ImageAnalysis], threshold: float) -> MatchReport:
    ref_emb = reference.embedding
    results = []
    for i, cand in enumerate(candidates):
        cand_emb = cand.embedding
        if ref_emb is None or cand_emb is None:
            results.append(CandidateResult(i, cand, None, None))
        else:
            score = cosine_score(ref_emb, cand_emb)
            results.append(CandidateResult(i, cand, score, score >= threshold))
    return MatchReport(reference, results, threshold)
