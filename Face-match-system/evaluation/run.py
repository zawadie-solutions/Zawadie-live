"""Run the PRD §7 benchmark and (optionally) write the calibrated threshold to config.

    python -m evaluation.run                     # FG-NET + CFP + latency
    python -m evaluation.run --write-threshold   # also store FG-NET threshold@FAR=1% as the default

Embeddings of the public benchmark images are cached in evaluation/cache/ so re-runs are fast;
delete that folder after changing the model or detection code.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from facematch.config import PROJECT_ROOT, load_settings, save_threshold
from facematch.engine import FaceEngine, decode_image
from facematch.matching import cosine_score

from .datasets import load_cfp, load_fgnet
from .metrics import kfold_accuracy, rates_at_threshold, summarize

DATASETS = PROJECT_ROOT / "Datasets"
CACHE = Path(__file__).parent / "cache"
RESULTS = Path(__file__).parent / "results"
FAR = 0.01
TARGETS = {"age_tar": 0.90, "pose_tar": 0.85, "far": 0.01, "cpu_latency_s": 2.0}
ADULT_AGE = 18
AGE_GAP_BINS = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 100)]


def embed_all(engine: FaceEngine, paths: list[Path], cache_name: str, pad: bool | None) -> dict:
    """Embed the largest face per image. Failed detections get a zero embedding (scores 0 = reject)."""
    cache_file = CACHE / f"{cache_name}.npz"
    keys = [str(p) for p in paths]
    if cache_file.exists():
        cached = np.load(cache_file, allow_pickle=False)
        if list(cached["keys"]) == keys:
            return {k: cached[k] for k in ("emb", "n_faces")}

    emb = np.zeros((len(paths), 512), dtype=np.float32)
    n_faces = np.zeros(len(paths), dtype=np.int32)
    started = time.perf_counter()
    for i, path in enumerate(paths):
        image = decode_image(path.read_bytes())
        faces = engine.detect(image, pad=pad) if image is not None else []
        n_faces[i] = len(faces)
        if faces:
            emb[i] = faces[0].embedding
        if (i + 1) % 250 == 0:
            print(f"  [{cache_name}] {i + 1}/{len(paths)} images, {time.perf_counter() - started:.0f}s", flush=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(cache_file, keys=np.array(keys), emb=emb, n_faces=n_faces)
    return {"emb": emb, "n_faces": n_faces}


def detection_stats(n_faces: np.ndarray) -> dict:
    return {"images": int(len(n_faces)), "no_face": int((n_faces == 0).sum()), "multiple_faces": int((n_faces > 1).sum())}


def pair_scores(emb_a: np.ndarray, emb_b: np.ndarray) -> np.ndarray:
    # Row-wise cosine; zero (failed) embeddings give 0. Clamped to [0, 1] like the API.
    return np.clip((emb_a * emb_b).sum(axis=1), 0.0, 1.0)


def eval_fgnet(engine: FaceEngine) -> tuple[dict, np.ndarray, np.ndarray]:
    images = load_fgnet(DATASETS / "FGNET")
    out = embed_all(engine, [im.path for im in images], "fgnet", pad=None)
    emb = out["emb"]
    subjects = np.array([im.subject for im in images])
    ages = np.array([im.age for im in images])

    i, j = np.triu_indices(len(images), k=1)  # every unordered pair
    scores = pair_scores(emb[i], emb[j])
    labels = (subjects[i] == subjects[j]).astype(int)
    summary = summarize(scores, labels, FAR)
    thr = summary[f"threshold_at_far_{FAR:g}"]

    gaps = np.abs(ages[i] - ages[j])
    # The real use case is adult-to-adult (PRD §4): score that slice with the same operating threshold.
    adult = (ages[i] >= ADULT_AGE) & (ages[j] >= ADULT_AGE)
    adult_tar, adult_far = rates_at_threshold(scores[adult], labels[adult], thr)
    adult_summary = {
        **summarize(scores[adult], labels[adult], FAR),
        "subjects": int(len(set(subjects[ages >= ADULT_AGE]))),
        "at_operating_threshold": {"threshold": thr, "tar": adult_tar, "far": adult_far},
        "tar_by_age_gap": tar_by_age_gap(scores[adult], labels[adult], gaps[adult], thr),
    }
    child_to_adult = (labels == 1) & (np.minimum(ages[i], ages[j]) < 13) & (np.maximum(ages[i], ages[j]) >= ADULT_AGE)
    return {
        "detection": detection_stats(out["n_faces"]),
        **summary,
        "tar_by_age_gap": tar_by_age_gap(scores, labels, gaps, thr),
        "adult_pairs": adult_summary,
        "child_to_adult_genuine": {"n": int(child_to_adult.sum()), "tar": float((scores[child_to_adult] >= thr).mean())},
    }, scores, labels


def tar_by_age_gap(scores: np.ndarray, labels: np.ndarray, gaps: np.ndarray, thr: float) -> list[dict]:
    rows = []
    for lo, hi in AGE_GAP_BINS:
        sel = (labels == 1) & (gaps >= lo) & (gaps < hi)
        if sel.any():
            rows.append({"age_gap": f"{lo}-{hi - 1}" if hi < 100 else f"{lo}+", "n_genuine": int(sel.sum()),
                         "tar": float((scores[sel] >= thr).mean()), "median_score": float(np.median(scores[sel]))})
    return rows


def eval_cfp(engine: FaceEngine, threshold: float | None) -> tuple[dict, dict]:
    data = load_cfp(DATASETS / "cfp-dataset")
    # CFP images are tight crops, so pad up front instead of the auto retry.
    f = embed_all(engine, data.frontal, "cfp_frontal", pad=True)
    p = embed_all(engine, data.profile, "cfp_profile", pad=True)

    results, curves = {"detection": {"frontal": detection_stats(f["n_faces"]), "profile": detection_stats(p["n_faces"])}}, {}
    for name, folds, second in (("FF", data.ff_folds, f["emb"]), ("FP", data.fp_folds, p["emb"])):
        fold_scores, fold_labels = [], []
        for fold in folds:
            pairs = fold.same + fold.diff
            a = np.array([x for x, _ in pairs])
            b = np.array([y for _, y in pairs])
            fold_scores.append(pair_scores(f["emb"][a], second[b]))
            fold_labels.append(np.array([1] * len(fold.same) + [0] * len(fold.diff)))
        scores, labels = np.concatenate(fold_scores), np.concatenate(fold_labels)
        acc_mean, acc_std = kfold_accuracy(fold_scores, fold_labels)
        entry = {**summarize(scores, labels, FAR), "accuracy_10fold_mean": acc_mean, "accuracy_10fold_std": acc_std}
        if threshold is not None:
            tar, far = rates_at_threshold(scores, labels, threshold)
            entry["at_operating_threshold"] = {"threshold": threshold, "tar": tar, "far": far}
        results[name] = entry
        curves[f"CFP-{name}"] = (scores, labels)
    return results, curves


def measure_latency(engine: FaceEngine, n_pairs: int = 20) -> dict:
    """End-to-end per match (decode + detect/embed both images + score), like one API call with 1 candidate."""
    paths = [im.path for im in load_fgnet(DATASETS / "FGNET")]
    rng = np.random.default_rng(0)
    timings = []
    for k in range(n_pairs + 1):
        a, b = rng.choice(len(paths), size=2, replace=False)
        t = time.perf_counter()
        fa = engine.detect(decode_image(paths[a].read_bytes()))
        fb = engine.detect(decode_image(paths[b].read_bytes()))
        if fa and fb:
            cosine_score(fa[0].embedding, fb[0].embedding)
        if k:  # first call is warm-up
            timings.append(time.perf_counter() - t)
    timings.sort()
    return {"pairs": n_pairs, "median_s": statistics.median(timings), "p95_s": timings[int(0.95 * (len(timings) - 1))],
            "max_s": timings[-1]}


def plot_roc(curves: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve

    fig, ax = plt.subplots(figsize=(6, 5))
    for name, (scores, labels) in curves.items():
        fpr, tpr, _ = roc_curve(labels, scores)
        ax.plot(np.maximum(fpr, 1e-5), tpr, label=name)
    ax.axvline(FAR, color="gray", linestyle="--", linewidth=1, label=f"FAR = {FAR:.0%}")
    ax.set(xscale="log", xlim=(1e-4, 1), ylim=(0, 1.01), xlabel="False accept rate", ylabel="True accept rate",
           title="ROC — pretrained ArcFace (buffalo_l)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def pct(x: float) -> str:
    return f"{100 * x:.2f}%"


def write_summary(r: dict, path: Path) -> None:
    fg, fp = r["fgnet"], r["cfp"]["FP"]
    thr = fg[f"threshold_at_far_{FAR:g}"]
    op = fp["at_operating_threshold"]
    ad = fg["adult_pairs"]
    ad_op = ad["at_operating_threshold"]
    lat = r["latency"]
    rows = [
        (f"Age gap, adult pairs (both ≥ {ADULT_AGE}): TAR on FG-NET at the operating threshold", pct(ad_op["tar"]),
         f"≥ {TARGETS['age_tar']:.0%}", ad_op["tar"] >= TARGETS["age_tar"]),
        (f"Age gap, adult pairs (both ≥ {ADULT_AGE}): FAR on FG-NET at the operating threshold", pct(ad_op["far"]),
         f"≤ {TARGETS['far']:.0%}", ad_op["far"] <= TARGETS["far"]),
        ("Pose: TAR on CFP-FP at the operating threshold", pct(op["tar"]), f"≥ {TARGETS['pose_tar']:.0%}",
         op["tar"] >= TARGETS["pose_tar"]),
        ("Pose: FAR on CFP-FP at the operating threshold", pct(op["far"]), f"≤ {TARGETS['far']:.0%}",
         op["far"] <= TARGETS["far"]),
        ("Latency per match (CPU, median / p95)", f"{lat['median_s']:.2f}s / {lat['p95_s']:.2f}s",
         f"< {TARGETS['cpu_latency_s']:.0f}s", lat["p95_s"] < TARGETS["cpu_latency_s"]),
    ]
    lines = [
        "# Phase 1 baseline evaluation",
        "",
        f"Generated {r['generated']} by `python -m evaluation.run`. Model: InsightFace `buffalo_l` "
        "(RetinaFace detector + ArcFace R50), CPU. Scores are cosine similarity clamped to [0, 1].",
        "",
        f"**Operating threshold:** {thr:.4f}. It's calibrated on FG-NET so that FAR = 1%.",
        "",
        "## PRD §2 targets",
        "",
        "| Target | Result | Goal | Met |",
        "|---|---|---|---|",
        *[f"| {n} | {v} | {g} | {'yes' if ok else '**no**'} |" for n, v, g, ok in rows],
        "",
        f"The age target is measured on adult pairs because the real use case is adult-to-adult comparison "
        f"(PRD §4). For reference, TAR on **all** FG-NET pairs, childhood included, is "
        f"{pct(fg[f'tar_at_far_{FAR:g}'])} at FAR=1%.",
        "",
        f"## FG-NET: adult pairs (both photos age ≥ {ADULT_AGE})",
        "",
        f"- {ad['subjects']} subjects. Pairs: {ad['n_genuine']} genuine, {ad['n_impostor']} impostor",
        f"- AUC {ad['auc']:.4f}, EER {pct(ad['eer'])}. TAR at this slice's own FAR=1% threshold "
        f"({ad[f'threshold_at_far_{FAR:g}']:.4f}): {pct(ad[f'tar_at_far_{FAR:g}'])}",
        "",
        *gap_table(ad["tar_by_age_gap"]),
        "",
        "## FG-NET: all pairs (includes childhood photos)",
        "",
        f"- Pairs: {fg['n_genuine']} genuine, {fg['n_impostor']} impostor",
        f"- Faces not found: {fg['detection']['no_face']} of {fg['detection']['images']} images. "
        f"Images with several faces: {fg['detection']['multiple_faces']} (the largest face was used)",
        f"- AUC {fg['auc']:.4f}, EER {pct(fg['eer'])}",
        f"- Child (under 13) vs. adult genuine pairs: {pct(fg['child_to_adult_genuine']['tar'])} recognised "
        f"(n = {fg['child_to_adult_genuine']['n']}). Most of the all-pairs shortfall comes from these.",
        "",
        *gap_table(fg["tar_by_age_gap"]),
        "",
        "## CFP (pose, official 10-fold protocol)",
        "",
        "| Protocol | 10-fold accuracy | AUC | EER | TAR @ FAR=1% (own threshold) | TAR / FAR at operating threshold |",
        "|---|---|---|---|---|---|",
    ]
    for name in ("FF", "FP"):
        e = r["cfp"][name]
        o = e["at_operating_threshold"]
        lines.append(f"| {name} | {pct(e['accuracy_10fold_mean'])} ± {pct(e['accuracy_10fold_std'])} | {e['auc']:.4f} | "
                     f"{pct(e['eer'])} | {pct(e[f'tar_at_far_{FAR:g}'])} | {pct(o['tar'])} / {pct(o['far'])} |")
    d = r["cfp"]["detection"]
    lines += [
        "",
        f"Faces not found: {d['frontal']['no_face']} of {d['frontal']['images']} frontal images and "
        f"{d['profile']['no_face']} of {d['profile']['images']} profile images.",
        "",
        "## Caveats",
        "",
        "- The threshold is calibrated and tested on the same FG-NET pairs. That makes the FG-NET FAR exactly 1% by "
        "construction. CFP is the independent check of how well the threshold transfers.",
        "- A failed detection scores 0, which counts as a rejection. This is conservative for genuine pairs.",
        f"- The adult slice is small ({ad['subjects']} subjects), and its widest age-gap bins have few pairs. "
        "Treat those rows as indicative, and spot-check with your own photos.",
        "- Neither dataset has demographic labels, so this report has no per-slice bias check (PRD §8).",
        "",
        "![ROC](roc.png)",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def gap_table(rows: list[dict]) -> list[str]:
    return [
        "| Age gap (years) | Genuine pairs | TAR at operating threshold | Median score |",
        "|---|---|---|---|",
        *[f"| {b['age_gap']} | {b['n_genuine']} | {pct(b['tar'])} | {b['median_score']:.3f} |" for b in rows],
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-threshold", action="store_true",
                        help="store the FG-NET threshold at FAR=1%% as the default in facematch_config.json")
    parser.add_argument("--latency-pairs", type=int, default=20)
    args = parser.parse_args()

    settings = load_settings()
    engine = FaceEngine(settings.model_name, settings.det_size, settings.det_thresh)

    print("FG-NET ...", flush=True)
    fgnet, fg_scores, fg_labels = eval_fgnet(engine)
    threshold = fgnet[f"threshold_at_far_{FAR:g}"]
    print("CFP ...", flush=True)
    cfp, curves = eval_cfp(engine, threshold)
    print("Latency ...", flush=True)
    latency = measure_latency(engine, args.latency_pairs)

    results = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "model": settings.model_name,
               "fgnet": fgnet, "cfp": cfp, "latency": latency}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    plot_roc({"FG-NET (age)": (fg_scores, fg_labels), **curves}, RESULTS / "roc.png")
    write_summary(results, RESULTS / "summary.md")
    if args.write_threshold:
        save_threshold(threshold, f"FG-NET threshold at FAR=1% (evaluation run {results['generated']})")

    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    print((RESULTS / "summary.md").read_text(encoding="utf-8"))
    if args.write_threshold:
        print(f"Wrote threshold {threshold:.4f} to config.")


if __name__ == "__main__":
    main()
