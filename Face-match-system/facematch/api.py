"""FastAPI app: POST a reference image plus 1+ candidates, get a verdict per candidate.

Run: uvicorn facematch.api:app, then open http://localhost:8000/ for the upload page.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Annotated, Protocol

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, load_settings, validate_threshold
from .engine import decode_image
from .matching import DetectedFace, ImageAnalysis, MatchReport, match_reference, select_face

request_log = logging.getLogger("facematch.requests")
STATIC_DIR = Path(__file__).parent / "static"


class Detector(Protocol):
    model_name: str

    def detect(self, image: np.ndarray) -> list[DetectedFace]: ...


def parse_candidate_faces(raw: str | None, n_candidates: int) -> dict[int, int]:
    """Parse "candidate:face" pairs, e.g. "0:1,2:0" -> {0: 1, 2: 0}."""
    if not raw or not raw.strip():
        return {}
    selection = {}
    for part in raw.split(","):
        try:
            cand, face = (int(x) for x in part.split(":"))
        except ValueError:
            raise ValueError(f"candidate_faces entry {part!r} is not 'candidate_index:face_index'") from None
        if not 0 <= cand < n_candidates:
            raise ValueError(f"candidate_faces refers to candidate {cand}, but only {n_candidates} were sent")
        selection[cand] = face
    return selection


def _face_json(face: DetectedFace, index: int) -> dict:
    return {"index": index, "bbox": [round(v, 1) for v in face.bbox], "det_score": round(face.det_score, 4)}


def _image_json(img: ImageAnalysis) -> dict:
    return {
        "filename": img.filename,
        "status": img.status.value,
        "faces": [_face_json(f, i) for i, f in enumerate(img.faces)],
        "selected_face": img.selected_face,
    }


def report_json(report: MatchReport) -> dict:
    return {
        "status": "ok" if report.complete else "incomplete",
        "threshold": report.threshold,
        "reference": _image_json(report.reference),
        "results": [
            {
                "candidate_index": c.index,
                **_image_json(c.image),
                "score": None if c.score is None else round(c.score, 4),
                "match": c.match,
            }
            for c in report.candidates
        ],
    }


def _configure_request_log(settings: Settings) -> None:
    if request_log.handlers:
        return
    path = settings.resolved_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    request_log.addHandler(handler)
    request_log.setLevel(logging.INFO)


def create_app(engine: Detector | None = None, settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _configure_request_log(settings)
        if app.state.engine is None:
            from .engine import FaceEngine

            app.state.engine = FaceEngine(settings.model_name, settings.det_size, settings.det_thresh)
        yield

    app = FastAPI(title="Face Match", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "model": app.state.engine.model_name if app.state.engine else None,
            "threshold": settings.threshold,
            "threshold_source": settings.threshold_source,
        }

    # Sync handler on purpose: inference is CPU-bound, FastAPI runs it in a worker thread.
    @app.post("/match")
    def match(
        reference: Annotated[UploadFile, File(description="The known/reference face image")],
        candidates: Annotated[list[UploadFile], File(description="One or more images to compare against the reference")],
        reference_face: Annotated[int | None, Form(description="Face index in the reference image, if it has several")] = None,
        candidate_faces: Annotated[str | None, Form(description="Face picks for multi-face candidates, e.g. '0:1,2:0'")] = None,
        threshold: Annotated[float | None, Form(description="Override the configured match threshold (0-1)")] = None,
    ) -> dict:
        started = time.perf_counter()
        thr = settings.threshold if threshold is None else threshold
        try:
            validate_threshold(thr)
            picks = parse_candidate_faces(candidate_faces, len(candidates))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

        engine: Detector = app.state.engine

        def analyze(upload: UploadFile, face_index: int | None) -> ImageAnalysis:
            image = decode_image(upload.file.read())
            faces = None if image is None else engine.detect(image)
            return select_face(upload.filename or "", faces, face_index)

        ref = analyze(reference, reference_face)
        cands = [analyze(c, picks.get(i)) for i, c in enumerate(candidates)]
        body = report_json(match_reference(ref, cands, thr))
        _log_request(body, time.perf_counter() - started)
        return body

    return app


def _log_request(body: dict, elapsed_s: float) -> None:
    """Metadata only (FR5): no pixels and no embeddings ever reach the log."""
    request_log.info(json.dumps({
        "request_id": uuid.uuid4().hex,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_ms": round(elapsed_s * 1000, 1),
        **body,
    }))


def __getattr__(name: str):
    # Lazily build the module-level app so importing this module (e.g. in tests)
    # doesn't read config or load the model.
    if name == "app":
        globals()["app"] = create_app()
        return globals()["app"]
    raise AttributeError(name)
