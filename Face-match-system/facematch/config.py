"""Runtime settings, loaded from facematch_config.json with env-var overrides.

FACEMATCH_CONFIG   path to an alternative config file
FACEMATCH_THRESHOLD  overrides the match threshold
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "facematch_config.json"


@dataclass(frozen=True)
class Settings:
    threshold: float
    threshold_source: str
    model_name: str = "buffalo_l"
    det_size: int = 640
    det_thresh: float = 0.5
    log_path: str = "logs/facematch.log"

    def resolved_log_path(self) -> Path:
        path = Path(self.log_path)
        return path if path.is_absolute() else PROJECT_ROOT / path


def config_path() -> Path:
    return Path(os.environ.get("FACEMATCH_CONFIG", DEFAULT_CONFIG_PATH))


def load_settings(path: Path | None = None) -> Settings:
    data = json.loads((path or config_path()).read_text(encoding="utf-8"))
    settings = Settings(**data)
    override = os.environ.get("FACEMATCH_THRESHOLD")
    if override is not None:
        settings = Settings(**{**asdict(settings), "threshold": float(override),
                               "threshold_source": "FACEMATCH_THRESHOLD env var"})
    validate_threshold(settings.threshold)
    return settings


def save_threshold(threshold: float, source: str, path: Path | None = None) -> None:
    validate_threshold(threshold)
    target = path or config_path()
    data = json.loads(target.read_text(encoding="utf-8"))
    data["threshold"] = round(float(threshold), 4)
    data["threshold_source"] = source
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def validate_threshold(threshold: float) -> None:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be in [0, 1], got {threshold}")
