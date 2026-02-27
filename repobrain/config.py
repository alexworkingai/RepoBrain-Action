from __future__ import annotations

from dataclasses import dataclass, field
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
    config_loaded: bool = False
    config_path: str = "<missing>"
    tky_remote_enabled: bool = False
    tky_remote_allow_commands: list[str] = field(default_factory=lambda: ["ask", "explain"])
    tky_remote_allow_branches: list[str] = field(default_factory=lambda: ["main"])
    tky_remote_allow_repos: list[str] = field(default_factory=list)
    tky_remote_fail_open: bool = True


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _as_str_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return default
    if isinstance(value, str):
        item = value.strip()
        return [item] if item else default
    if isinstance(value, list):
        out = [str(item).strip() for item in value if str(item).strip()]
        return out if out else []
    if isinstance(value, tuple):
        out = [str(item).strip() for item in value if str(item).strip()]
        return out if out else []
    return default


def load_config(root: Path) -> RepoBrainConfig:
    """Load .repobrain.yml if present, otherwise return defaults."""
    cfg_path = root / ".repobrain.yml"
    if not cfg_path.exists():
        return RepoBrainConfig(config_loaded=False, config_path="<missing>")

    data_raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    data: dict[str, Any] = data_raw if isinstance(data_raw, dict) else {}
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
    tky_remote_enabled = _to_bool(
        tky.get("remote_enabled", tky.get("remoteEnabled", False)),
        False,
    )
    tky_remote_allow_commands = _as_str_list(
        tky.get("remote_allow_commands", tky.get("remoteAllowCommands")),
        ["ask", "explain"],
    )
    tky_remote_allow_branches = _as_str_list(
        tky.get("remote_allow_branches", tky.get("remoteAllowBranches")),
        ["main"],
    )
    tky_remote_allow_repos = _as_str_list(
        tky.get("remote_allow_repos", tky.get("remoteAllowRepos")),
        [],
    )
    tky_remote_fail_open = _to_bool(
        tky.get("remote_fail_open", tky.get("remoteFailOpen", True)),
        True,
    )

    return RepoBrainConfig(
        max_sources=max_sources,
        topk=topk,
        min_score_fast=min_score_fast,
        min_score_keep=min_score_keep,
        max_sources_fast=max_sources_fast,
        max_sources_deep=max_sources_deep,
        topk_fast=topk_fast,
        topk_deep=topk_deep,
        config_loaded=True,
        config_path=str(cfg_path),
        tky_remote_enabled=tky_remote_enabled,
        tky_remote_allow_commands=tky_remote_allow_commands,
        tky_remote_allow_branches=tky_remote_allow_branches,
        tky_remote_allow_repos=tky_remote_allow_repos,
        tky_remote_fail_open=tky_remote_fail_open,
    )
