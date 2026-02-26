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
    min_score_fast: float = 0.05
    min_score_keep: float = 0.02
    max_sources_fast: int = 6
    max_sources_deep: int = 12
    topk_fast: int = 30
    topk_deep: int = 80


def load_config(root: Path) -> RepoBrainConfig:
    """Load .repobrain.yml if present, otherwise return defaults."""
    cfg_path = root / ".repobrain.yml"
    if not cfg_path.exists():
        return RepoBrainConfig()

    data: dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    answer = data.get("answer", {}) or {}
    limits = data.get("limits", {}) or {}

    legacy_max_sources = answer.get("max_sources", None)
    legacy_topk = limits.get("topk", None)

    max_sources_fast = int(answer.get("max_sources_fast", legacy_max_sources or 6))
    max_sources_deep = int(answer.get("max_sources_deep", legacy_max_sources or 12))
    max_sources = int(legacy_max_sources or max_sources_fast)

    topk_fast = int(limits.get("topk_fast", legacy_topk or 30))
    topk_deep = int(limits.get("topk_deep", legacy_topk or 80))
    topk = int(legacy_topk or topk_fast)

    min_score_fast = float(answer.get("min_score_fast", 0.05))
    min_score_keep = float(answer.get("min_score_keep", 0.02))

    return RepoBrainConfig(
        max_sources=max_sources,
        topk=topk,
        min_score_fast=min_score_fast,
        min_score_keep=min_score_keep,
        max_sources_fast=max_sources_fast,
        max_sources_deep=max_sources_deep,
        topk_fast=topk_fast,
        topk_deep=topk_deep,
    )
