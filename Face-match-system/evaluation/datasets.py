"""Loaders for the benchmark layouts under Datasets/."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# FG-NET file names: <subject:3 digits>A<age:2 digits>[optional letter].JPG, e.g. 001A43b.JPG
_FGNET_NAME = re.compile(r"^(\d{3})a(\d{2})[a-z]?$", re.IGNORECASE)


@dataclass(frozen=True)
class FGNetImage:
    path: Path
    subject: int
    age: int


def parse_fgnet_name(stem: str) -> tuple[int, int]:
    m = _FGNET_NAME.match(stem)
    if not m:
        raise ValueError(f"not an FG-NET image name: {stem!r}")
    return int(m.group(1)), int(m.group(2))


def load_fgnet(root: Path) -> list[FGNetImage]:
    images = []
    for path in sorted((root / "images").iterdir()):
        subject, age = parse_fgnet_name(path.stem)
        images.append(FGNetImage(path, subject, age))
    return images


@dataclass(frozen=True)
class CFPFold:
    same: list[tuple[int, int]]  # 0-based indices into (first list, second list)
    diff: list[tuple[int, int]]


@dataclass(frozen=True)
class CFPData:
    frontal: list[Path]
    profile: list[Path]
    ff_folds: list[CFPFold]  # frontal vs frontal
    fp_folds: list[CFPFold]  # frontal vs profile


def _read_image_list(protocol_dir: Path, name: str) -> list[Path]:
    paths = []
    for line in (protocol_dir / name).read_text().splitlines():
        if line.strip():
            _, rel = line.split(maxsplit=1)
            paths.append((protocol_dir / rel).resolve())
    return paths


def _read_pairs(path: Path) -> list[tuple[int, int]]:
    pairs = []
    for line in path.read_text().splitlines():
        if line.strip():
            a, b = line.split(",")
            pairs.append((int(a) - 1, int(b) - 1))  # protocol indices are 1-based
    return pairs


def _read_folds(split_dir: Path) -> list[CFPFold]:
    return [
        CFPFold(_read_pairs(d / "same.txt"), _read_pairs(d / "diff.txt"))
        for d in sorted(p for p in split_dir.iterdir() if p.is_dir())
    ]


def load_cfp(root: Path) -> CFPData:
    protocol = root / "Protocol"
    return CFPData(
        frontal=_read_image_list(protocol, "Pair_list_F.txt"),
        profile=_read_image_list(protocol, "Pair_list_P.txt"),
        ff_folds=_read_folds(protocol / "Split" / "FF"),
        fp_folds=_read_folds(protocol / "Split" / "FP"),
    )
