from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from repobrain.tky_provider import CandidateChunk

_DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc")
_TEST_PATH_TOKENS = ("/test", "/tests/", "test_", "_test.", "spec/")
_WORKFLOW_PATH_TOKENS = (".github/workflows/", "workflow", "ci/", "pipeline")
_CONFIG_EXTENSIONS = (".yml", ".yaml", ".toml", ".ini", ".cfg", ".json")

_BUCKET_ORDER = (
    "changed_primary",
    "changed_secondary",
    "support_context",
    "tests",
    "docs",
    "workflow_config",
)


@dataclass(frozen=True)
class EvidenceBudgetPlanResult:
    candidates: list[CandidateChunk]
    evidence_budget_used: int
    evidence_budget_limit: int
    evidence_budget_mode: str
    evidence_budget_bucket_counts: dict[str, int]
    evidence_budget_cutoffs: list[str]
    evidence_budget_overflow: int
    evidence_budget_primary_selected: int
    evidence_budget_support_selected: int


def _normalize_command(command: str) -> str:
    normalized = str(command or "ask").strip().lower()
    if normalized in {"ask", "explain", "locate", "review", "fix"}:
        return normalized
    return "ask"


def _is_docs_path(path: str) -> bool:
    lowered = str(path or "").strip().lower()
    if not lowered:
        return False
    if lowered.startswith(("docs/", "documentation/")):
        return True
    return any(lowered.endswith(ext) for ext in _DOC_EXTENSIONS)


def _is_test_path(path: str) -> bool:
    lowered = f"/{str(path or '').strip().lower()}/"
    return any(token in lowered for token in _TEST_PATH_TOKENS)


def _is_workflow_or_config_path(path: str) -> bool:
    lowered = str(path or "").strip().lower()
    if not lowered:
        return False
    if any(token in lowered for token in _WORKFLOW_PATH_TOKENS):
        return True
    return any(lowered.endswith(ext) for ext in _CONFIG_EXTENSIONS)


def _is_code_like_path(path: str) -> bool:
    lowered = str(path or "").strip().lower()
    if not lowered:
        return False
    if _is_docs_path(lowered) or _is_test_path(lowered) or _is_workflow_or_config_path(lowered):
        return False
    if "." not in lowered:
        return True
    ext = lowered.rsplit(".", 1)[-1]
    return ext in {
        "py",
        "js",
        "ts",
        "tsx",
        "jsx",
        "go",
        "rs",
        "java",
        "kt",
        "swift",
        "rb",
        "php",
        "c",
        "cc",
        "cpp",
        "h",
        "hpp",
        "cs",
        "scala",
        "sh",
    }


def _changed_files_from_context(github_context: dict[str, Any] | None) -> set[str]:
    if not isinstance(github_context, dict):
        return set()
    raw = github_context.get("changed_files", [])
    if not isinstance(raw, list):
        return set()
    return {str(item).strip() for item in raw if str(item).strip()}


def _profile_for(
    command: str,
    *,
    limit_hint: int,
    incremental_scope_mode: str,
    ultra_large_mode: bool = False,
) -> tuple[int, str, dict[str, int], list[str]]:
    cmd = _normalize_command(command)
    scope_mode = str(incremental_scope_mode or "fallback_full")
    if cmd in {"ask", "explain", "locate"}:
        base_limit = max(3, min(18, int(limit_hint * 0.60) if limit_hint > 0 else 10))
        mode = "ask_dense_incremental" if scope_mode != "fallback_full" else "ask_dense"
        if ultra_large_mode:
            base_limit = min(base_limit, 10)
            mode = "ultra_large_ask_capped"
        caps = {
            "changed_primary": max(3, int(base_limit * 0.45)),
            "changed_secondary": max(1, int(base_limit * 0.15)),
            "support_context": max(2, int(base_limit * 0.25)),
            "tests": max(1, int(base_limit * 0.08)),
            "docs": max(1, int(base_limit * 0.05)),
            "workflow_config": max(1, int(base_limit * 0.10)),
        }
        priority = [
            "changed_primary",
            "support_context",
            "workflow_config",
            "changed_secondary",
            "tests",
            "docs",
        ]
        return base_limit, mode, caps, priority
    if cmd == "review":
        base_limit = max(6, min(30, int(limit_hint * 0.75) if limit_hint > 0 else 20))
        mode = "review_risk_weighted_incremental" if scope_mode != "fallback_full" else "review_risk_weighted"
        if ultra_large_mode:
            base_limit = min(base_limit, 18)
            mode = "ultra_large_review_capped"
        caps = {
            "changed_primary": max(6, int(base_limit * 0.45)),
            "changed_secondary": max(2, int(base_limit * 0.20)),
            "workflow_config": max(2, int(base_limit * 0.15)),
            "support_context": max(2, int(base_limit * 0.10)),
            "tests": max(1, int(base_limit * 0.07)),
            "docs": max(1, int(base_limit * 0.05)),
        }
        priority = [
            "changed_primary",
            "workflow_config",
            "changed_secondary",
            "tests",
            "support_context",
            "docs",
        ]
        return base_limit, mode, caps, priority

    base_limit = max(4, min(20, int(limit_hint * 0.50) if limit_hint > 0 else 12))
    mode = "fix_localized_strict_incremental" if scope_mode != "fallback_full" else "fix_localized_strict"
    if ultra_large_mode:
        base_limit = min(base_limit, 14)
        mode = "ultra_large_fix_capped"
    caps = {
        "changed_primary": max(4, int(base_limit * 0.60)),
        "changed_secondary": max(1, int(base_limit * 0.20)),
        "workflow_config": max(1, int(base_limit * 0.08)),
        "support_context": max(1, int(base_limit * 0.07)),
        "tests": max(1, int(base_limit * 0.03)),
        "docs": max(1, int(base_limit * 0.02)),
    }
    priority = [
        "changed_primary",
        "changed_secondary",
        "workflow_config",
        "support_context",
        "tests",
        "docs",
    ]
    return base_limit, mode, caps, priority


def _bucket_for(path: str, changed_files: set[str]) -> str:
    normalized = str(path or "").strip()
    in_changed = normalized in changed_files
    if in_changed and _is_code_like_path(normalized):
        return "changed_primary"
    if in_changed:
        return "changed_secondary"
    if _is_workflow_or_config_path(normalized):
        return "workflow_config"
    if _is_test_path(normalized):
        return "tests"
    if _is_docs_path(normalized):
        return "docs"
    return "support_context"


def _bucket_with_segment_hint(
    path: str,
    *,
    changed_files: set[str],
    file_segment_class_map: dict[str, str],
) -> str:
    normalized = str(path or "").strip()
    hinted_class = str(file_segment_class_map.get(normalized, "")).strip().lower()
    if hinted_class in {"docs"}:
        return "docs"
    if hinted_class in {"tests"}:
        return "tests"
    if hinted_class in {"workflow_ci", "config_build"}:
        return "workflow_config"
    if hinted_class in {"generated_or_vendor"}:
        return "support_context"
    if hinted_class in {"tooling_scripts"}:
        return "support_context"
    if hinted_class in {"core_code", "mixed_or_other"}:
        if normalized in changed_files:
            return "changed_primary"
        return "support_context"
    return _bucket_for(normalized, changed_files)


def plan_evidence_budget(
    candidates: list[CandidateChunk],
    *,
    command: str,
    github_context: dict[str, Any] | None = None,
    limit_hint: int | None = None,
    incremental_scope_mode: str = "fallback_full",
    segment_hints: dict[str, Any] | None = None,
    ultra_large_mode: bool = False,
) -> EvidenceBudgetPlanResult:
    if not candidates:
        return EvidenceBudgetPlanResult(
            candidates=[],
            evidence_budget_used=0,
            evidence_budget_limit=0,
            evidence_budget_mode="not_applied",
            evidence_budget_bucket_counts={bucket: 0 for bucket in _BUCKET_ORDER},
            evidence_budget_cutoffs=["no_cutoff"],
            evidence_budget_overflow=0,
            evidence_budget_primary_selected=0,
            evidence_budget_support_selected=0,
        )

    try:
        hint = int(limit_hint) if limit_hint is not None else len(candidates)
    except (TypeError, ValueError):
        hint = len(candidates)
    safe_hint = max(1, min(len(candidates), hint))
    limit, mode, bucket_caps, priority = _profile_for(
        command,
        limit_hint=safe_hint,
        incremental_scope_mode=incremental_scope_mode,
        ultra_large_mode=bool(ultra_large_mode),
    )
    budget_limit = max(1, min(len(candidates), int(limit)))
    changed_files = _changed_files_from_context(github_context)
    segment_hints_map = dict(segment_hints or {})
    file_segment_class_map_raw = segment_hints_map.get("file_segment_class_map", {})
    file_segment_class_map = (
        {
            str(path).strip(): str(segment_class).strip().lower()
            for path, segment_class in file_segment_class_map_raw.items()
            if str(path).strip()
        }
        if isinstance(file_segment_class_map_raw, dict)
        else {}
    )

    bucketed: dict[str, list[CandidateChunk]] = {bucket: [] for bucket in _BUCKET_ORDER}
    for item in candidates:
        bucket = (
            _bucket_with_segment_hint(
                item.file_path,
                changed_files=changed_files,
                file_segment_class_map=file_segment_class_map,
            )
            if file_segment_class_map
            else _bucket_for(item.file_path, changed_files)
        )
        bucketed[bucket].append(item)

    selected: list[CandidateChunk] = []
    selected_ids: set[str] = set()
    selected_counts: dict[str, int] = {bucket: 0 for bucket in _BUCKET_ORDER}
    cutoffs: set[str] = set()

    for bucket in priority:
        cap = max(0, int(bucket_caps.get(bucket, 0)))
        if cap == 0:
            continue
        for item in bucketed.get(bucket, []):
            if len(selected) >= budget_limit:
                cutoffs.add("budget_exhausted")
                break
            if selected_counts[bucket] >= cap:
                cutoffs.add(f"cut_{bucket}")
                break
            if item.chunk_id in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item.chunk_id)
            selected_counts[bucket] += 1
        if len(selected) >= budget_limit:
            break

    if len(selected) < budget_limit:
        for item in candidates:
            if len(selected) >= budget_limit:
                break
            if item.chunk_id in selected_ids:
                continue
            bucket = (
                _bucket_with_segment_hint(
                    item.file_path,
                    changed_files=changed_files,
                    file_segment_class_map=file_segment_class_map,
                )
                if file_segment_class_map
                else _bucket_for(item.file_path, changed_files)
            )
            selected.append(item)
            selected_ids.add(item.chunk_id)
            selected_counts[bucket] = selected_counts.get(bucket, 0) + 1

    overflow = max(0, len(candidates) - len(selected))
    if overflow > 0 and "budget_exhausted" not in cutoffs:
        cutoffs.add("budget_exhausted")
    for bucket in _BUCKET_ORDER:
        total = len(bucketed.get(bucket, []))
        kept = int(selected_counts.get(bucket, 0))
        if total > kept:
            cutoffs.add(f"dropped_{bucket}")
    if not cutoffs:
        cutoffs.add("no_cutoff")

    primary_selected = int(selected_counts.get("changed_primary", 0)) + int(
        selected_counts.get("changed_secondary", 0)
    )
    support_selected = max(0, len(selected) - primary_selected)
    return EvidenceBudgetPlanResult(
        candidates=selected,
        evidence_budget_used=len(selected),
        evidence_budget_limit=budget_limit,
        evidence_budget_mode=mode,
        evidence_budget_bucket_counts={bucket: int(selected_counts.get(bucket, 0)) for bucket in _BUCKET_ORDER},
        evidence_budget_cutoffs=sorted(cutoffs),
        evidence_budget_overflow=overflow,
        evidence_budget_primary_selected=primary_selected,
        evidence_budget_support_selected=support_selected,
    )
