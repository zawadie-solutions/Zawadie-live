# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

[PRD.md](PRD.md) is the source of truth for scope and design. Phase 1 (pretrained baseline + API + evaluation) is implemented.

## What this is

A self-hosted, personal-scale **face verification** system. One reference photo is compared with 1+ candidate photos, and each candidate gets a similarity score and a match or no-match verdict. It compares embeddings; it does not classify identities, and it is not a search or surveillance tool.

## Commands

Windows, Python 3.11, CPU only. Use the venv interpreter at `.venv/Scripts/python`.

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m pytest                                   # all tests
.venv/Scripts/python -m pytest -m "not integration"              # fast: no model loading
.venv/Scripts/python -m pytest tests/test_api.py::test_threshold_override   # single test
.venv/Scripts/uvicorn facematch.api:app                          # upload page at :8000/, API docs at /docs
.venv/Scripts/python -m evaluation.run [--write-threshold]       # benchmark; writes evaluation/results/
```

On first use, InsightFace downloads the `buffalo_l` model (~280 MB) into `~/.insightface/models/`.

Example request (image files are placeholders):

```bash
curl -F reference=@old.jpg -F candidates=@new1.jpg -F candidates=@new2.jpg http://localhost:8000/match
```

## Architecture

- [facematch/matching.py](facematch/matching.py): pure logic with no model. `select_face` resolves each image to a status (`ok`, `no_face`, `multiple_faces`, `invalid_image` or `invalid_face_index`). It **never auto-picks** among several faces (FR2). `match_reference` scores each candidate against the reference. Cosine similarity is clamped to [0, 1], and a pair matches when `score >= threshold`.
- [facematch/engine.py](facematch/engine.py): wraps InsightFace (RetinaFace + ArcFace R50, CPU onnxruntime).
  - Faces are returned largest first, and that order defines the face indices callers use.
  - **Padding fallback:** when nothing is detected, detection is retried with a black border. RetinaFace misses faces that fill the frame, so tight crops (all of CFP, about 40% of FG-NET) would fail without it.
  - Bounding boxes are mapped back to the original image coordinates.
  - Images are decoded with Pillow so EXIF rotation from phone photos is honored.
- [facematch/api.py](facematch/api.py): `create_app(engine, settings)` makes the app testable with a fake engine; `facematch.api:app` builds it lazily.
  - `POST /match` takes multipart `reference` and `candidates[]`, plus optional form fields `reference_face`, `candidate_faces` (`"cand:face,..."`) and `threshold`. It always returns 200 with a status per image. A 422 is only for malformed parameters.
  - Each request writes one JSON line to `logs/facematch.log` with **metadata only**. Never add embeddings or pixels to it (FR5).
- [facematch/static/index.html](facematch/static/index.html): the upload page served at `/`. It implements the Google Stitch design in [stitch_face_match/](stitch_face_match/) ("Kinship & Memory" tokens in `kinship_memory/DESIGN.md`). The Stitch HTML is a reference only; it pulls Tailwind, fonts and images from other sites, so don't copy it in.
  - The page uses inline CSS, JS and SVG icons, plus Plus Jakarta Sans served from `static/fonts/` (OFL license alongside it).
  - A test enforces that it loads nothing from other sites. It calls `/health` for the default threshold and `/match` for results. Clicking a face box on a multi-face photo sends that face index and compares again.
  - **Reference groups:** the page holds up to 10 groups (`MAX_REFS`), each with its own reference photo and photos to check. "Compare all" sends one `/match` request per group, one after another. The model already uses every CPU core, so running them in parallel wouldn't be faster. The backend has no notion of groups.
  - **Theme:** a Light/Dark toggle sets `data-theme` on `<html>` and saves the choice in `localStorage` (`facematch-theme`). With nothing saved, the page follows the Windows setting.
- [facematch/config.py](facematch/config.py): settings come from [facematch_config.json](facematch_config.json). The env vars `FACEMATCH_CONFIG` and `FACEMATCH_THRESHOLD` override them.
- [evaluation/](evaluation/): benchmark loaders, metrics and a runner.
  - **FG-NET:** every same-subject and cross-subject pair; results broken down by age gap.
  - **CFP:** the official 10-fold FF and FP protocol. CFP images are padded up front.
  - Benchmark embeddings are cached in `evaluation/cache/`. **Delete the cache after changing the model or the detection code**, or the results will be stale.
  - The report goes to `evaluation/results/summary.md`.
- Datasets live in `Datasets/FGNET` and `Datasets/cfp-dataset`, and are gitignored.

## Rules from the PRD

- **Threshold:** the default comes from FG-NET at FAR=1%, written by `evaluation.run --write-threshold`. Don't hand-edit it without a measurement.
- **Evaluation is a gate:** targets are TAR ≥ 90% at FAR ≤ 1% on age gaps, TAR ≥ 85% on CFP-FP, and under 2s per match on CPU. The use case is adult-to-adult, so the age target is scored on FG-NET pairs where both photos are 18 or older; the all-ages number is reported only for reference. Don't call anything "working" from hand-picked examples. Every model or pipeline change needs a before/after run of `evaluation.run`.
- **Age-invariance work (fine-tuning, disentanglement):** not triggered. The baseline meets all targets (PRD §11). Revisit only if real adult photos contradict the benchmark.
- **Model license:** the InsightFace pretrained weights are for non-commercial use only. That's fine for this personal tool.
- **Biometric data:** embeddings count as biometric data. Before adding any persistence, flag the consent and retention concerns (PRD §8).
- **Known gap:** the datasets have no demographic labels, so the per-slice bias check can't be run.
- **Out of scope for v1:** auth, persistence, video, liveness, and image restoration. The upload page is the one Phase 2 item built so far.
