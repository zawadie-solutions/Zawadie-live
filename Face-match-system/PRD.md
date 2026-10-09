# PRD: Age & Angle-Invariant Face Match System

## 1. Overview

**Problem statement:** Build a system that takes two or more face images — potentially taken years apart, at different angles, and under different conditions — and determines whether they show the same person.

**Core capability:** Face verification (1:1 or 1:N matching), not classification. The system compares faces via numeric embeddings rather than trying to "learn" a fixed set of identities.

**Out of scope for v1:** Real-time video matching, liveness/anti-spoofing detection, large-scale (millions of identities) search infrastructure. These are noted as future phases in Section 9.

## 2. Goals & Success Criteria

| Goal | Metric | Target (v1) |
|---|---|---|
| Correctly match same-person images across age gaps | True Accept Rate (TAR) on FG-NET **adult pairs** (both photos age ≥ 18) at the operating threshold; the use case is adult-to-adult (Section 10) | ≥ 90% at fixed FAR |
| Correctly reject different-person images | False Accept Rate (FAR) | ≤ 1% |
| Handle pose/angle variation | TAR on profile-vs-frontal pairs | ≥ 85% |
| Inference speed | Latency per match (2 images) | < 2s on CPU, < 500ms on GPU |
| Usability | End-to-end: upload → result | Single API call or simple UI |

Success is measured against a held-out validation set using ROC curve / Equal Error Rate (EER) — not eyeballed examples. This must be established before claiming the system "works."

## 3. Non-Goals

- Not a general-purpose facial recognition surveillance tool.
- Not identifying *who* a person is from a database of names (no identity classification) — only "do these two/more images show the same person."
- No claims of legal-grade identity verification (e.g., KYC) without additional compliance work (Section 8).

## 4. Users & Use Cases

- **Primary use case: personal photo tool.** Single user (or small personal scale), comparing personal photos — e.g., old vs. recent photos of the same person — rather than any commercial identity-verification or surveillance use.
- **Deployment:** self-hosted, exposed as a local/private API (not a public multi-tenant service). No auth/multi-user system needed for v1 unless requested later.
- **Scale:** dozens of matches, not thousands — this relaxes performance/infra requirements considerably (no need for approximate nearest-neighbor search, vector DB, or horizontal scaling in v1).
- Input: 2+ images per match request, arbitrary source (old photo, phone photo, scanned photo, etc.)
- Output: match/no-match decision + confidence score, per pair (or per group if 3+ images)

## 5. System Architecture

### 5.1 Pipeline stages

1. **Face Detection & Alignment**
   - Detect face(s) in each image, extract landmarks (eyes, nose, mouth corners)
   - Warp/rotate to a canonical alignment before embedding
   - Library: RetinaFace or MTCNN (via `insightface` or `facenet-pytorch`)
   - Reject/flag images where no face or multiple faces are detected (need explicit user handling — see Section 6)

2. **Embedding Generation**
   - Convert aligned face to a fixed-length numeric vector (embedding)
   - Start with a pretrained model: **ArcFace via InsightFace** (recommended starting point — strong open baseline)
   - Output: e.g., 512-dim float vector per face

3. **Similarity Scoring**
   - Cosine similarity (or Euclidean distance) between embeddings
   - Calibrated threshold to output match/no-match + confidence

4. **Age-Invariance Layer (v1.1, after baseline is benchmarked)**
   - Only build this if baseline ArcFace underperforms on age-gap pairs during evaluation (Section 7)
   - Options, in order of effort: fine-tune on age-gap datasets → disentangled age/identity embedding → generative age-normalization (GAN-based)

### 5.2 Suggested stack

- **Language:** Python (backend/ML), since this is compute/model-heavy
- **ML libraries:** `insightface`, PyTorch, OpenCV
- **API layer:** FastAPI (simple REST endpoint: POST images → JSON result), run locally via `uvicorn` — no need for cloud deployment infra given self-hosted, personal-scale use
- **Storage:** given "dozens of matches" scale and personal use, a vector DB is overkill. Store embeddings as flat files (e.g., `.npy` per image) or a lightweight SQLite table with a BLOB/array column if any persistence across sessions is wanted. No pgvector/ANN index needed for v1.
- **Frontend:** deferred — v1 ships as an API only (e.g., `curl`/Postman-testable). A minimal upload UI can be added in Phase 2 if the API alone isn't convenient enough day-to-day.

## 6. Functional Requirements

- FR1: Accept 2+ images via API/upload
- FR2: Detect faces in each image. Zero faces → explicit error. Multiple faces → do not guess: return every detected face (index, bounding box, detection confidence) with a `multiple_faces` status, and let the caller re-submit specifying a face index for that image. Never silently pick a face.
- FR3: Return a similarity score (cosine similarity, clamped to 0–1) and a match/no-match boolean based on a configurable threshold
- FR4: **Reference mode.** One image is the reference; 1+ candidate images are each compared against it. Output one result (score + match/no-match) per candidate. No all-pairs mode in v1.
- FR5: Log each request's detection/embedding/decision steps for debugging and later evaluation (no black-box behavior). **Metadata only:** timestamps, face counts, bounding boxes, detection confidence, scores, threshold used, decision. Never write images, face crops, or embeddings to disk.
- FR6: Threshold must be configurable, not hardcoded. Default value is calibrated from the FG-NET evaluation at FAR = 1% (Section 7) and stored in config; overridable per request.

## 7. Evaluation Plan (must happen before calling this "done")

1. Datasets (confirmed): **FG-NET** (Kaggle mirror; official site is offline) for age-gap pairs, and **CFP-FP** (direct download from http://www.cfpw.io/cfp-dataset.zip, ~86 MB, no registration) for frontal-vs-profile pairs. AgeDB is optional — only if access is granted later.
2. Run baseline pretrained ArcFace on genuine pairs (same person, different ages / poses) and impostor pairs (different people)
3. Plot ROC curve, compute EER and TAR@FAR=1% — separately for FG-NET (age target) and CFP-FP (pose target). The FG-NET threshold at FAR=1% becomes the default threshold (FR6).
   - Known gap: neither dataset carries demographic labels, so the per-slice bias check in Section 8 cannot be done with these alone. Acceptable for personal use; must be addressed before any wider deployment.
4. Only proceed to fine-tuning/disentanglement (Section 5.1 step 4) if baseline numbers miss the targets in Section 2
5. Document results before/after any model changes — no changes without a measured before/after

## 8. Risks & Constraints

- **Bias/fairness:** Pretrained face models have documented accuracy disparities across skin tone, age, and gender. Must benchmark across demographic slices, not just aggregate accuracy, before any real-world deployment.
- **Legal/regulatory:** Biometric data (face embeddings tied to identity) is regulated (e.g., BIPA in Illinois, GDPR in EU). If storing embeddings tied to real people, requires consent flow and data retention/deletion policy — flag this explicitly before building persistence.
- **Image quality:** Old/scanned photos may need preprocessing (denoising, super-resolution) — not in v1 scope unless early testing shows it's a blocker.
- **No guessing on scope:** the exact use case (Section 4) should be confirmed before deep investment in fine-tuning or UI — the detection+embedding+scoring core is useful regardless of final use case.

## 9. Phased Rollout

- **Phase 1 (MVP):** Detection + alignment + pretrained ArcFace embedding + cosine similarity + configurable threshold. Evaluate on FG-NET/AgeDB. API-only, no persistence.
- **Phase 2:** Age-invariance improvements if Phase 1 eval shows gaps on large age deltas. Add basic upload UI if useful.
- **Phase 3 (only if needed):** Liveness detection, larger-scale N:N matching/search, persistence with compliance controls.

## 10. Open Questions — Resolved

- **Use case:** personal photo tool (confirmed). Compliance burden (Section 8) is much lighter than a commercial/ID-verification tool, but the consent/retention note still applies if photos of people other than the user are involved.
- **Deployment:** self-hosted, with an API (confirmed). No public-facing hosting, auth, or multi-tenancy needed for v1.
- **Scale:** dozens of matches (confirmed). Justifies the simplified storage approach in Section 5.2 — no vector DB or ANN search needed.
- **Test data:** no existing dataset yet; a handful of images may be provided later for real-world spot-checks. Public benchmarks (FG-NET/AgeDB, Section 7) remain the primary evaluation source until then — do not skip Section 7's evaluation step just because personal test images aren't available yet.

- **Comparison mode (FR4):** reference image vs. 1+ candidates, per-candidate verdict (confirmed).
- **Multiple faces (FR2):** return all detected faces, caller picks by index (confirmed).
- **Hardware:** Windows, CPU only (confirmed). Target is the < 2s CPU latency; use `onnxruntime` (CPU build). GPU is not a v1 concern.
- **Evaluation data:** FG-NET mirror + CFP-FP (confirmed); see Section 7.
- **Default threshold:** calibrated from FG-NET at FAR=1% (confirmed).
- **Logging:** metadata only, no biometric data on disk (confirmed).
- **Model license:** InsightFace pretrained weights are non-commercial only — accepted, since this is a personal tool. Any future commercial use requires swapping to a commercially licensed model.

- **Age range of real comparisons:** adult to adult (confirmed after Phase 1). The age-gap target is therefore measured on FG-NET pairs where both photos are age ≥ 18. Childhood-to-adult matching is not a goal; the all-ages FG-NET number is still reported for reference.

No remaining open questions block starting Phase 1.

## 11. Phase 1 Results (baseline, pretrained `buffalo_l`)

Full report: `evaluation/results/summary.md`. Operating threshold 0.2589 (FG-NET, FAR = 1%).

- Age gap, adult pairs: TAR 99.48% at FAR 0.65% (target ≥ 90% at ≤ 1%) — **met**. Weakest bin: 30+ year gaps, 93.3% (60 pairs).
- Pose, CFP-FP: TAR 96.29% at FAR 0.00% (target ≥ 85%) — **met**.
- Latency: ~0.9–1.2s per match on CPU (target < 2s) — **met**.
- All-ages FG-NET (reference only): TAR 85.42% at FAR 1%; the gap is child-to-adult pairs (57.7%).

**Upload UI (Phase 2 item):** built. A local page at `/` lets you choose a reference photo and photos to check, then shows a verdict label and score under each one. On a multi-face photo you click the face to use. The page makes no requests to other sites.

**Decision:** baseline meets every v1 target for the confirmed use case, so the Phase 2 age-invariance work (Section 5.1 step 4) is **not triggered**. Revisit only if real adult photo spot-checks disagree with these numbers.