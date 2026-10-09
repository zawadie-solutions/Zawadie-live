"""Verification metrics. Convention: label 1 = genuine (same person), a pair matches when score >= threshold."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve


def rates_at_threshold(scores: np.ndarray, labels: np.ndarray, threshold: float) -> tuple[float, float]:
    """Return (TAR, FAR) at a threshold."""
    accept = scores >= threshold
    return float(accept[labels == 1].mean()), float(accept[labels == 0].mean())


def threshold_at_far(scores: np.ndarray, labels: np.ndarray, far: float) -> float:
    """Lowest threshold whose false accept rate does not exceed `far`."""
    impostor = np.sort(scores[labels == 0])[::-1]
    k = int(np.floor(far * len(impostor)))  # number of impostors we may accept
    if k >= len(impostor):
        return float(impostor[-1])
    # Accept only the k highest impostors: sit just above the (k+1)-th highest.
    return float(np.nextafter(impostor[k], np.inf))


def eer(scores: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    """Equal error rate and the threshold where it occurs."""
    fpr, tpr, thr = roc_curve(labels, scores)
    fnr = 1 - tpr
    i = int(np.nanargmin(np.abs(fnr - fpr)))
    return float((fpr[i] + fnr[i]) / 2), float(thr[i])


def best_accuracy_threshold(scores: np.ndarray, labels: np.ndarray) -> float:
    # Cut between neighbouring scores, not on them, so the threshold generalizes to held-out folds.
    unique = np.unique(scores)
    candidates = np.concatenate([[unique[0]], (unique[:-1] + unique[1:]) / 2, [np.nextafter(unique[-1], np.inf)]])
    accs = [((scores >= t) == (labels == 1)).mean() for t in candidates]
    return float(candidates[int(np.argmax(accs))])


def summarize(scores: np.ndarray, labels: np.ndarray, far: float = 0.01) -> dict:
    thr = threshold_at_far(scores, labels, far)
    tar, actual_far = rates_at_threshold(scores, labels, thr)
    eer_value, eer_thr = eer(scores, labels)
    return {
        "n_genuine": int((labels == 1).sum()),
        "n_impostor": int((labels == 0).sum()),
        "auc": float(roc_auc_score(labels, scores)),
        "eer": eer_value,
        "eer_threshold": eer_thr,
        f"threshold_at_far_{far:g}": thr,
        f"tar_at_far_{far:g}": tar,
        f"actual_far_at_far_{far:g}": actual_far,
    }


def kfold_accuracy(fold_scores: list[np.ndarray], fold_labels: list[np.ndarray]) -> tuple[float, float]:
    """Standard 10-fold protocol: pick the best-accuracy threshold on the other folds, test on the held-out one."""
    accs = []
    for i in range(len(fold_scores)):
        train_s = np.concatenate([s for j, s in enumerate(fold_scores) if j != i])
        train_l = np.concatenate([l for j, l in enumerate(fold_labels) if j != i])
        t = best_accuracy_threshold(train_s, train_l)
        accs.append(((fold_scores[i] >= t) == (fold_labels[i] == 1)).mean())
    return float(np.mean(accs)), float(np.std(accs))
