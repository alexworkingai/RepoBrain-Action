from __future__ import annotations

from dataclasses import dataclass

_DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc")
_CONFIG_EXTENSIONS = (".yml", ".yaml", ".toml", ".ini", ".cfg")
_GENERATED_PATH_TOKENS = (
    "node_modules/",
    "vendor/",
    "third_party/",
    "dist/",
    "build/",
    ".min.",
    "package-lock.json",
    "pnpm-lock.yaml",
)


@dataclass(frozen=True)
class PRSegmentationResult:
    pr_segmentation_used: bool
    pr_segment_count: int
    pr_primary_segments: str
    pr_support_segments: str
    pr_cross_segment: bool
    pr_segment_summary: str
    pr_segment_file_counts: str
    pr_segment_candidate_counts: str
    pr_segmentation_fallback_reason: str
    file_segment_class_map: dict[str, str]

    def as_audit_fields(self) -> dict[str, object]:
        return {
            "pr_segmentation_used": bool(self.pr_segmentation_used),
            "pr_segment_count": int(self.pr_segment_count),
            "pr_primary_segments": str(self.pr_primary_segments or "none"),
            "pr_support_segments": str(self.pr_support_segments or "none"),
            "pr_cross_segment": bool(self.pr_cross_segment),
            "pr_segment_summary": str(self.pr_segment_summary or "none"),
            "pr_segment_file_counts": str(self.pr_segment_file_counts or "none"),
            "pr_segment_candidate_counts": str(self.pr_segment_candidate_counts or "none"),
            "pr_segmentation_fallback_reason": str(self.pr_segmentation_fallback_reason or "none"),
        }


def segmentation_defaults(*, fallback_reason: str = "not_applicable") -> dict[str, object]:
    return PRSegmentationResult(
        pr_segmentation_used=False,
        pr_segment_count=0,
        pr_primary_segments="none",
        pr_support_segments="none",
        pr_cross_segment=False,
        pr_segment_summary="none",
        pr_segment_file_counts="none",
        pr_segment_candidate_counts="none",
        pr_segmentation_fallback_reason=fallback_reason,
        file_segment_class_map={},
    ).as_audit_fields()


def _classify_segment_class(path: str) -> str:
    normalized = str(path or "").strip().lower()
    if not normalized:
        return "mixed_or_other"
    if any(token in normalized for token in _GENERATED_PATH_TOKENS):
        return "generated_or_vendor"
    if normalized.startswith(".github/workflows/") or "workflow" in normalized or normalized.startswith("ci/"):
        return "workflow_ci"
    if normalized.startswith(("docs/", "documentation/")) or normalized.endswith(_DOC_EXTENSIONS):
        return "docs"
    if normalized.startswith("tests/") or "/tests/" in f"/{normalized}/" or normalized.startswith("test_"):
        return "tests"
    if normalized.startswith(("scripts/", "tools/")):
        return "tooling_scripts"
    if (
        normalized in {"pyproject.toml", "dockerfile", "makefile", "package.json"}
        or normalized.startswith("requirements")
        or normalized.endswith(_CONFIG_EXTENSIONS)
    ):
        return "config_build"
    if normalized.endswith(
        (
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".go",
            ".rs",
            ".java",
            ".kt",
            ".rb",
            ".php",
            ".c",
            ".cc",
            ".cpp",
            ".cs",
            ".swift",
            ".scala",
            ".sh",
        )
    ):
        return "core_code"
    return "mixed_or_other"


def _classify_subsystem(path: str) -> str:
    normalized = str(path or "").strip().replace("\\", "/")
    if not normalized:
        return "root"
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return "root"
    if len(parts) >= 2 and parts[0] == ".github" and parts[1] == "workflows":
        return ".github/workflows"
    if parts[0] in {"repobrain", "src", "lib", "app"} and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    items = [f"{key}={int(value)}" for key, value in sorted(counts.items(), key=lambda item: item[0])]
    return "; ".join(items) if items else "none"


def _join_labels(values: list[str]) -> str:
    normalized = [str(item).strip() for item in values if str(item).strip()]
    return ", ".join(normalized) if normalized else "none"


def _is_support_class(segment_class: str) -> bool:
    return segment_class in {"tests", "docs", "generated_or_vendor"}


def build_pr_segmentation(
    *,
    changed_files: list[str],
    candidate_paths: list[str] | None = None,
) -> PRSegmentationResult:
    files = sorted(set(str(path).strip() for path in changed_files if str(path).strip()))
    if not files:
        return PRSegmentationResult(
            pr_segmentation_used=False,
            pr_segment_count=0,
            pr_primary_segments="none",
            pr_support_segments="none",
            pr_cross_segment=False,
            pr_segment_summary="none",
            pr_segment_file_counts="none",
            pr_segment_candidate_counts="none",
            pr_segmentation_fallback_reason="missing_changed_files",
            file_segment_class_map={},
        )

    segment_key_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    file_segment_class_map: dict[str, str] = {}
    for path in files:
        segment_class = _classify_segment_class(path)
        subsystem = _classify_subsystem(path)
        key = f"{segment_class}:{subsystem}"
        segment_key_counts[key] = segment_key_counts.get(key, 0) + 1
        class_counts[segment_class] = class_counts.get(segment_class, 0) + 1
        file_segment_class_map[path] = segment_class

    candidate_paths_norm = [str(path).strip() for path in (candidate_paths or []) if str(path).strip()]
    candidate_counts: dict[str, int] = {}
    for path in candidate_paths_norm:
        segment_class = file_segment_class_map.get(path, _classify_segment_class(path))
        candidate_counts[segment_class] = candidate_counts.get(segment_class, 0) + 1

    substantive = {k: v for k, v in segment_key_counts.items() if not _is_support_class(k.split(":", 1)[0])}
    source_for_primary = substantive if substantive else segment_key_counts
    top_count = max(source_for_primary.values()) if source_for_primary else 0
    primary_segments = sorted(key for key, count in source_for_primary.items() if count == top_count and count > 0)
    support_segments = sorted(key for key in segment_key_counts if key not in set(primary_segments))

    substantive_classes = {
        key.split(":", 1)[0]
        for key, count in segment_key_counts.items()
        if count > 0 and not _is_support_class(key.split(":", 1)[0])
    }
    pr_cross_segment = len(substantive_classes) > 1
    if not pr_cross_segment:
        major_subsystems = {
            key.split(":", 1)[1]
            for key, count in segment_key_counts.items()
            if count > 0 and key.split(":", 1)[0] in substantive_classes
        }
        pr_cross_segment = len(major_subsystems) > 1

    summary = (
        f"primary={_join_labels(primary_segments)}; "
        f"support={_join_labels(support_segments[:5])}; "
        f"cross_segment={'yes' if pr_cross_segment else 'no'}"
    )
    return PRSegmentationResult(
        pr_segmentation_used=True,
        pr_segment_count=len(segment_key_counts),
        pr_primary_segments=_join_labels(primary_segments),
        pr_support_segments=_join_labels(support_segments),
        pr_cross_segment=pr_cross_segment,
        pr_segment_summary=summary,
        pr_segment_file_counts=_format_counts(class_counts),
        pr_segment_candidate_counts=_format_counts(candidate_counts),
        pr_segmentation_fallback_reason="none",
        file_segment_class_map=file_segment_class_map,
    )
