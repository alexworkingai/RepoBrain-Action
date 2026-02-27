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
    tky_remote_enabled: bool = False
    tky_remote_allow_commands: tuple[str, ...] = ("ask", "explain")
    tky_remote_allow_branches: tuple[str, ...] = ("main",)
    tky_remote_allow_repos: tuple[str, ...] = ()
    tky_remote_fail_open: bool = True


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _as_str_tuple(value: Any, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    if isinstance(value, str):
        item = value.strip()
        return (item,) if item else default
    if isinstance(value, list):
        out = tuple(str(item).strip() for item in value if str(item).strip())
        return out if out else ()
    if isinstance(value, tuple):
        out = tuple(str(item).strip() for item in value if str(item).strip())
        return out if out else ()
    return default


def load_config(root: Path) -> RepoBrainConfig:
    """Load .repobrain.yml if present, otherwise return defaults."""
    cfg_path = root / ".repobrain.yml"
    if not cfg_path.exists():
        return RepoBrainConfig()

    data: dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    answer = data.get("answer", {}) or {}
    limits = data.get("limits", {}) or {}
    tky = data.get("tky", {}) or {}

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
    tky_remote_enabled = _as_bool(tky.get("remote_enabled"), False)
    tky_remote_allow_commands = _as_str_tuple(
        tky.get("remote_allow_commands"),
        ("ask", "explain"),
    )
    tky_remote_allow_branches = _as_str_tuple(
        tky.get("remote_allow_branches"),
        ("main",),
    )
    tky_remote_allow_repos = _as_str_tuple(
        tky.get("remote_allow_repos"),
        (),
    )
    tky_remote_fail_open = _as_bool(tky.get("remote_fail_open"), True)

    return RepoBrainConfig(
        max_sources=max_sources,
        topk=topk,
        min_score_fast=min_score_fast,
        min_score_keep=min_score_keep,
        max_sources_fast=max_sources_fast,
        max_sources_deep=max_sources_deep,
        topk_fast=topk_fast,
        topk_deep=topk_deep,
        tky_remote_enabled=tky_remote_enabled,
        tky_remote_allow_commands=tky_remote_allow_commands,
        tky_remote_allow_branches=tky_remote_allow_branches,
        tky_remote_allow_repos=tky_remote_allow_repos,
        tky_remote_fail_open=tky_remote_fail_open,
    )
