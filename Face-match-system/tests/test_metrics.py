import numpy as np
import pytest

from evaluation.datasets import parse_fgnet_name
from evaluation.metrics import eer, kfold_accuracy, rates_at_threshold, threshold_at_far


def test_threshold_at_far_accepts_at_most_target_fraction():
    rng = np.random.default_rng(0)
    scores = np.concatenate([rng.uniform(0.5, 1.0, 100), rng.uniform(0.0, 0.6, 1000)])
    labels = np.array([1] * 100 + [0] * 1000)
    thr = threshold_at_far(scores, labels, 0.01)
    _, far = rates_at_threshold(scores, labels, thr)
    assert far <= 0.01
    # Lowering the threshold to the next impostor score would exceed the target.
    next_impostor = np.sort(scores[labels == 0])[::-1][10]
    assert rates_at_threshold(scores, labels, next_impostor)[1] > 0.01


def test_eer_is_zero_when_perfectly_separable():
    scores = np.array([0.9, 0.8, 0.2, 0.1])
    labels = np.array([1, 1, 0, 0])
    assert eer(scores, labels)[0] == 0.0


def test_kfold_accuracy_perfect_separation():
    s = [np.array([0.9, 0.1]), np.array([0.8, 0.2])]
    l = [np.array([1, 0]), np.array([1, 0])]
    assert kfold_accuracy(s, l) == (1.0, 0.0)


@pytest.mark.parametrize("stem, expected", [("001A02", (1, 2)), ("001a43b", (1, 43)), ("082A18", (82, 18))])
def test_parse_fgnet_name(stem, expected):
    assert parse_fgnet_name(stem) == expected


def test_parse_fgnet_name_rejects_other_files():
    with pytest.raises(ValueError):
        parse_fgnet_name("readme")
