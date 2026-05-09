from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


_DOC_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
    ".adoc",
}
_CODE_EXTENSIONS = {
    ".py",
    ".pyi",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".sql",
    ".sh",
}


@dataclass(frozen=True)
class PatchTarget:
    path: str
    score: int
    reason: str
    category: str
    hunk_count: int


@dataclass(frozen=True)
class _PatchTargetAssessment:
    target: PatchTarget
    has_localized_evidence: bool
    has_query_match: bool


def _extension(path: str) -> str:
    base = os.path.basename(path)
    if "." not in base:
        return ""
    return "." + base.rsplit(".", 1)[1].lower()


def _is_likely_fixable_path(path: str) -> bool:
    ext = _extension(path)
    if ext in _DOC_EXTENSIONS:
        return False
    if ext in _CODE_EXTENSIONS:
        return True
    lowered = path.lower()
    return any(
        token in lowered
        for token in ("src/", "repobrain/", "scripts/", "tests/", ".github/workflows/")
    )


def _split_patch_hunks(patch: str) -> list[str]:
    text = str(patch or "")
    if not text.strip():
        return []
    lines = text.splitlines()
    hunks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("@@ "):
            if current:
                hunks.append(current)
            current = [line]
            continue
        if current:
            current.append(line)
    if current:
        hunks.append(current)
    if not hunks:
        return [text]
    return ["\n".join(chunk).strip() for chunk in hunks if "\n".join(chunk).strip()]


def _extract_review_evidence_paths(review: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    confirmed_items = review.get("confirmed_risk_items", [])
    if isinstance(confirmed_items, list):
        for item in confirmed_items:
            if not isinstance(item, dict):
                continue
            evidence_paths = item.get("evidence_paths", [])
            if isinstance(evidence_paths, list):
                for value in evidence_paths:
                    path = str(value).strip()
                    if path:
                        paths.add(path)

    risk_items = review.get("risk_items", [])
    if isinstance(risk_items, list):
        for item in risk_items:
            if not isinstance(item, dict):
                continue
            evidence = item.get("evidence", [])
            if not isinstance(evidence, list):
                continue
            for entry in evidence:
                if not isinstance(entry, dict):
                    continue
                path = str(entry.get("path", "")).strip()
                if path:
                    paths.add(path)
    return paths


def _query_matches_file(query: str, path: str) -> bool:
    query_norm = str(query or "").strip().lower()
    if not query_norm:
        return False
    full = path.lower()
    base = os.path.basename(path).lower()
    stem = base.rsplit(".", 1)[0] if "." in base else base
    return full in query_norm or base in query_norm or (stem and stem in query_norm)


def _assess_patch_target(
    *,
    path: str,
    status: str,
    changes: int,
    hunks: list[str],
    evidence_paths: set[str],
    query: str,
    max_hunks: int,
) -> _PatchTargetAssessment:
    if not _is_likely_fixable_path(path):
        return _PatchTargetAssessment(
            target=PatchTarget(
                path=path,
                score=-100,
                reason="non_patchable_or_too_broad",
                category="non_patchable_or_too_broad",
                hunk_count=len(hunks),
            ),
            has_localized_evidence=False,
            has_query_match=False,
        )

    score = 0
    reasons: list[str] = []
    has_localized_evidence = path in evidence_paths
    has_query_match = _query_matches_file(query, path)

    if has_localized_evidence:
        score += 120
        reasons.append("evidence_path")
    if has_query_match:
        score += 90
        reasons.append("query_matched_path")
    if hunks:
        score += 24
        reasons.append("has_diff_hunks")
    if status in {"modified", "renamed"}:
        score += 10
    elif status == "added":
        score += 4
    if changes <= 250:
        score += 12
    elif changes > 900:
        score -= 18
    if len(hunks) > max_hunks:
        score -= 5
    if path.lower().startswith(".github/workflows/") and not has_localized_evidence:
        score -= 10
    if _extension(path) in _DOC_EXTENSIONS:
        score -= 30

    return _PatchTargetAssessment(
        target=PatchTarget(
            path=path,
            score=score,
            reason=",".join(reasons) if reasons else "low_localization",
            category="likely_fixable" if score >= 30 else "context_only",
            hunk_count=len(hunks),
        ),
        has_localized_evidence=has_localized_evidence,
        has_query_match=has_query_match,
    )


def select_patch_targets(
    *,
    files: list[dict[str, Any]],
    review: dict[str, Any],
    query: str,
    max_target_files: int,
    max_target_hunks: int,
    require_localized_evidence: bool,
) -> dict[str, Any]:
    evidence_paths = _extract_review_evidence_paths(review)
    max_files = max(1, int(max_target_files))
    max_hunks = max(1, int(max_target_hunks))
    ranked: list[PatchTarget] = []
    hunks_by_path: dict[str, list[str]] = {}
    localized_evidence_count = 0
    query_matched_count = 0
    non_patchable_count = 0

    for file_item in files:
        if not isinstance(file_item, dict):
            continue
        path = str(file_item.get("filename", "")).strip()
        if not path:
            continue
        patch = str(file_item.get("patch", "") or "")
        hunks = _split_patch_hunks(patch)
        hunks_by_path[path] = list(hunks)
        changes = int(file_item.get("changes", 0) or 0)
        status = str(file_item.get("status", "modified") or "modified").lower()
        assessment = _assess_patch_target(
            path=path,
            status=status,
            changes=changes,
            hunks=hunks,
            evidence_paths=evidence_paths,
            query=query,
            max_hunks=max_hunks,
        )
        if assessment.target.category == "non_patchable_or_too_broad":
            non_patchable_count += 1
        if assessment.has_localized_evidence:
            localized_evidence_count += 1
        if assessment.has_query_match:
            query_matched_count += 1
        ranked.append(assessment.target)

    ranked_sorted = sorted(ranked, key=lambda item: (-item.score, item.path))
    likely = [item for item in ranked_sorted if item.category == "likely_fixable"]
    context_only = [item for item in ranked_sorted if item.category == "context_only"]

    selected_candidates = list(likely[:max_files])
    if not selected_candidates and not require_localized_evidence:
        selected_candidates = list(context_only[:max_files])

    localized_signals = localized_evidence_count + query_matched_count
    if require_localized_evidence and localized_signals <= 0:
        selected_candidates = []

    selected_files = [item.path for item in selected_candidates]
    selected_hunks: list[str] = []
    for target in selected_candidates:
        for hunk in hunks_by_path.get(target.path, []):
            selected_hunks.append(f"[{target.path}]\n{hunk}")
            if len(selected_hunks) >= max_hunks:
                break
        if len(selected_hunks) >= max_hunks:
            break

    if not selected_files:
        mode = "none"
        if require_localized_evidence and localized_signals <= 0:
            reason = "no_localized_evidence_backed_patch_target"
        elif ranked_sorted:
            reason = "all_targets_non_patchable_or_low_localization"
        else:
            reason = "no_changed_files"
    else:
        capped = len(selected_files) < len(likely)
        mode = "localized_capped" if capped else "localized"
        reason = "patch_target_narrowed_to_localized_subset"

    return {
        "patch_target_files_total": len([item for item in ranked if item.category != "non_patchable_or_too_broad"])
        + non_patchable_count,
        "patch_target_files_selected": len(selected_files),
        "patch_target_hunks_selected": len(selected_hunks),
        "patch_targeting_mode": mode,
        "patch_targeting_reason": reason,
        "localized_patch_evidence_count": int(localized_signals),
        "query_matched_patch_files_count": int(query_matched_count),
        "selected_files": selected_files,
        "selected_hunks": selected_hunks,
        "ranked_targets": [
            {
                "path": item.path,
                "score": item.score,
                "reason": item.reason,
                "category": item.category,
                "hunk_count": item.hunk_count,
            }
            for item in ranked_sorted
        ],
    }
