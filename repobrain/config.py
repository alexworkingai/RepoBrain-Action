from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RepoBrainConfig:
    """Minimal config with safe defaults."""

    max_sources: int = 8
    topk: int = 30


def load_config(root: Path) -> RepoBrainConfig:
    """Load .repobrain.yml if present, otherwise return defaults."""
    cfg_path = root / ".repobrain.yml"
    if not cfg_path.exists():
        return RepoBrainConfig()

    data: dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    answer = data.get("answer", {}) or {}
    limits = data.get("limits", {}) or {}

    max_sources = int(answer.get("max_sources", 8))
    topk = int(limits.get("topk", 30))

    return RepoBrainConfig(max_sources=max_sources, topk=topk)
