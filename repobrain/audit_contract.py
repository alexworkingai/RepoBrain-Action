from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from repobrain.audit_scoring import CATEGORY_SPECS, readiness_band_for_score


AUDIT_V6_CONTRACT_VERSION = "topocore.audit_score.v1"
AUDIT_V6_MAX_EVIDENCE_ITEMS = 16
AUDIT_V6_MAX_LIST_ITEMS = 10
AUDIT_V6_MAX_TEXT_LENGTH = 240

_CATEGORY_TITLES_BY_KEY = {item.key: item.title for item in CATEGORY_SPECS}
_CATEGORY_MAX_BY_KEY = {item.key: item.max_score for item in CATEGORY_SPECS}
_CATEGORY_ORDER = [item.key for item in CATEGORY_SPECS]
_READINESS_LABELS = {"STRONG", "GOOD", "NEEDS_ATTENTION", "WEAK"}
_CATEGORY_LABELS = {"STRONG", "GOOD", "NEEDS_ATTENTION", "WEAK", "UNKNOWN"}
_PATH_TOKEN_RE = re.compile(
    r"([A-Za-z]:\\[^\\\s]+(?:\\[^\\\s]+)*)|(/[^/\s]+(?:/[^/\s]+)*)"
)
_PATH_CANDIDATE_RE = re.compile(
    r"(?P<path>(?:[A-Za-z]:[\\/][^\s`\"'<>|]+)|(?:/[^\s`\"'<>|]+)|(?:\.?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+))"
)
_TOKEN_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9_]+\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]+\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
_UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bsafe[- ]to[- ]merge\b"),
    re.compile(r"(?i)\bsecurity approval\b"),
    re.compile(r"(?i)\bsecurity approved\b"),
    re.compile(r"(?i)\bmerge approval\b"),
    re.compile(r"(?i)\bproduction certification\b"),
    re.compile(r"(?i)\brisk[- ]free certification\b"),
    re.compile(r"(?i)\bv5 fallback\b"),
    re.compile(r"(?i)\brepobrain" + re.escape("-") + r"community\b"),
    re.compile(r"(?i)\btraceback \(most recent call last\):"),
)
_PRIVATE_PATH_PATTERNS = (
    re.compile(r"(?i)\.topocore-v6"),
    re.compile(r"(?i)ariadna_minsk"),
    re.compile(r"(?i)c:\\users"),
    re.compile(r"(?i)/mnt/data"),
)
_REPO_RELATIVE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_FORBIDDEN_PATH_SEGMENTS = {
    ".git",
    ".ssh",
    ".topocore-v6",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "artifacts",
    "reports",
}
_SENSITIVE_PATH_MARKERS = (
    "secret",
    "token",
    "credential",
    "private-key",
    "private_key",
    "id_rsa",
    ".pem",
    ".p12",
    ".pfx",
    ".key",
    ".env",
)


class AuditContractError(ValueError):
    """Raised when audit contract request/response data is unsafe or invalid."""


def build_audit_score_request_v1(
    *,
    repo_root: Path,
    report: Mapping[str, Any],
    github_context: Mapping[str, Any] | None,
    query: str,
) -> dict[str, Any]:
    _ = Path(repo_root).resolve()
    github_context = dict(github_context) if isinstance(github_context, Mapping) else {}
    repository = str(github_context.get("repository", "") or "").strip()
    owner, repo = _split_repository_name(repository)
    pr_changed_files = {
        str(item).strip()
        for item in _safe_string_list(
            github_context.get("changed_files", [])
            or [
                entry.get("filename", "")
                for entry in github_context.get("files", [])
                if isinstance(entry, Mapping)
            ]
        )
        if str(item).strip()
    }
    evidence_manifest = _build_evidence_manifest(report=report, pr_changed_files=pr_changed_files)
    return {
        "contract_version": AUDIT_V6_CONTRACT_VERSION,
        "repo_metadata": {
            "owner": owner,
            "repo": repo,
            "default_branch": _sanitize_text(
                github_context.get("base_ref") or github_context.get("ref") or ""
            ),
            "event_type": _sanitize_text(github_context.get("event_name", "issue_comment")),
            "is_pr": bool(github_context.get("is_pr", False)),
            "pr_number": _safe_optional_int(github_context.get("pr_number")),
            "head_sha": _sanitize_text(github_context.get("head_sha") or github_context.get("sha") or ""),
        },
        "audit_focus": {
            "query": _sanitize_text(query, max_length=180),
        },
        "static_baseline": {
            "overall_score": _bounded_int(report.get("overall_score", 0), minimum=0, maximum=100),
            "readiness_band": _safe_readiness_band(report.get("readiness_band", "WEAK")),
            "category_scores": _build_category_payload(report),
            "category_max_weights": {
                item.title: item.max_score
                for item in CATEGORY_SPECS
            },
            "confidence": _safe_confidence(report.get("confidence", "medium")),
            "limitations": _safe_text_list(report.get("limitations", []), limit=6),
        },
        "evidence_manifest": evidence_manifest,
        "repo_signals": _build_repo_signals(report),
        "constraints": {
            "no_mutation": True,
            "no_patch": True,
            "no_branch_commit_pr": True,
            "no_security_approval_claim": True,
            "no_merge_approval_claim": True,
            "max_response_items": AUDIT_V6_MAX_LIST_ITEMS,
            "max_output_chars": 6000,
        },
    }


def validate_audit_score_response_v1(response: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise AuditContractError("v6 audit response must be a mapping.")
    _assert_no_forbidden_content(response)

    contract_version = str(response.get("contract_version", "") or "").strip()
    if contract_version != AUDIT_V6_CONTRACT_VERSION:
        raise AuditContractError("v6 audit response contract version mismatch.")

    status = str(response.get("status", "") or "").strip().lower()
    if status not in {"ok", "partial", "unsupported", "error_sanitized"}:
        raise AuditContractError("v6 audit response status is invalid.")

    category_scores_raw = response.get("category_scores", [])
    if not isinstance(category_scores_raw, Sequence) or isinstance(category_scores_raw, (str, bytes)):
        raise AuditContractError("v6 audit response category_scores must be a list.")

    normalized_categories = [_normalize_response_category(item) for item in category_scores_raw]
    keys = [item["key"] for item in normalized_categories]
    if sorted(keys) != sorted(_CATEGORY_ORDER):
        raise AuditContractError("v6 audit response category set is incomplete or invalid.")

    overall_score = _bounded_int(response.get("overall_score", 0), minimum=0, maximum=100)
    readiness_band = _safe_readiness_band(response.get("readiness_band", "WEAK"))
    warnings = _safe_text_list(_extract_diagnostic_warnings(response), limit=6)
    expected_band = readiness_band_for_score(overall_score)
    if readiness_band != expected_band:
        warnings.append(
            f"v6 readiness band `{readiness_band}` did not match score `{overall_score}`; expected `{expected_band}`."
        )

    safety = dict(response.get("safety", {})) if isinstance(response.get("safety", {}), Mapping) else {}
    if safety.get("patch_authorized") is not False:
        raise AuditContractError("v6 audit response attempted to authorize patch behavior.")
    if safety.get("patch_applied") is not False:
        raise AuditContractError("v6 audit response implied patch application.")
    for field_name in ("files_modified", "branch_created", "commit_created", "pr_created"):
        if safety.get(field_name) is not False:
            raise AuditContractError(f"v6 audit response implied mutation via {field_name}.")
    if safety.get("no_security_approval") is not True:
        raise AuditContractError("v6 audit response safety flags must deny security approval.")
    if safety.get("no_merge_approval") is not True:
        raise AuditContractError("v6 audit response safety flags must deny merge approval.")

    critical_blockers = _normalize_bounded_item_list(
        response.get("critical_blockers", []),
        limit=5,
        item_kind="blocker",
    )
    top_improvements = _normalize_bounded_item_list(
        response.get("top_improvements", []),
        limit=10,
        item_kind="improvement",
    )
    roadmap_raw = response.get("roadmap", {})
    roadmap_mapping = dict(roadmap_raw) if isinstance(roadmap_raw, Mapping) else {}
    roadmap = {
        "30_days": _safe_text_list(roadmap_mapping.get("30_days", []), limit=5),
        "60_days": _safe_text_list(roadmap_mapping.get("60_days", []), limit=5),
        "90_days": _safe_text_list(roadmap_mapping.get("90_days", []), limit=5),
    }

    limitations = _safe_text_list(response.get("limitations", []), limit=6)
    diagnostics = dict(response.get("diagnostics", {})) if isinstance(response.get("diagnostics", {}), Mapping) else {}
    diagnostics = {
        "backend_mode": _sanitize_text(diagnostics.get("backend_mode", ""), max_length=80),
        "capability_version": _sanitize_text(diagnostics.get("capability_version", ""), max_length=80),
        "warnings": warnings[:6],
    }

    score_adjustments_raw = response.get("score_adjustments", [])
    score_adjustments: list[dict[str, Any]] = []
    if isinstance(score_adjustments_raw, Sequence) and not isinstance(score_adjustments_raw, (str, bytes)):
        for item in list(score_adjustments_raw)[:AUDIT_V6_MAX_LIST_ITEMS]:
            if not isinstance(item, Mapping):
                raise AuditContractError("v6 audit score adjustment must be a mapping.")
            category_key = _normalize_category_key(item.get("category"))
            delta = int(item.get("delta", 0) or 0)
            score_adjustments.append(
                {
                    "category": category_key,
                    "delta": max(-_CATEGORY_MAX_BY_KEY[category_key], min(_CATEGORY_MAX_BY_KEY[category_key], delta)),
                    "reason": _sanitize_text(item.get("reason", "No reason recorded."), max_length=AUDIT_V6_MAX_TEXT_LENGTH),
                    "evidence_paths": _sanitize_evidence_paths(item.get("evidence_paths", []), limit=4),
                }
            )

    normalized = {
        "contract_version": AUDIT_V6_CONTRACT_VERSION,
        "status": status,
        "overall_score": overall_score,
        "readiness_band": readiness_band,
        "categories": normalized_categories,
        "score_adjustments": score_adjustments,
        "critical_blockers": critical_blockers,
        "top_improvements": top_improvements,
        "roadmap": roadmap,
        "confidence": _safe_confidence(response.get("confidence", "medium")),
        "limitations": limitations,
        "safety": {
            "patch_authorized": False,
            "patch_applied": False,
            "files_modified": False,
            "branch_created": False,
            "commit_created": False,
            "pr_created": False,
            "no_security_approval": True,
            "no_merge_approval": True,
        },
        "diagnostics": diagnostics,
    }
    _assert_no_forbidden_content(normalized)
    return normalized


def merge_audit_report_with_v6(
    *,
    static_report: Mapping[str, Any],
    validated_response: Mapping[str, Any],
) -> dict[str, Any]:
    merged = copy.deepcopy(dict(static_report))
    static_score = _bounded_int(static_report.get("overall_score", 0), minimum=0, maximum=100)
    static_band = _safe_readiness_band(static_report.get("readiness_band", "WEAK"))
    merged["static_baseline"] = {
        "overall_score": static_score,
        "readiness_band": static_band,
    }
    merged["audit_mode"] = "v6_enriched"
    merged["overall_score"] = int(validated_response["overall_score"])
    merged["readiness_band"] = str(validated_response["readiness_band"])
    merged["categories"] = [
        {
            "key": item["key"],
            "title": item["title"],
            "score": item["score"],
            "max_score": item["max_score"],
            "label": item["label"],
            "rationale": item["rationale"],
            "evidence_paths": list(item["evidence_paths"]),
            "assessable": True,
        }
        for item in validated_response["categories"]
    ]
    merged["critical_blockers"] = list(validated_response["critical_blockers"])
    merged["top_improvements"] = _filter_renderable_top_improvements(
        validated_response["top_improvements"],
        categories=validated_response["categories"],
    )
    merged["roadmap"] = _filter_renderable_roadmap(
        validated_response["roadmap"],
        categories=validated_response["categories"],
    )
    merged["confidence"] = str(validated_response["confidence"])
    merged["limitations"] = _unique_text(
        [
            *_safe_text_list(static_report.get("limitations", []), limit=6),
            *_safe_text_list(validated_response.get("limitations", []), limit=6),
        ]
    )[:6]
    merged["v6_score_adjustments"] = list(validated_response.get("score_adjustments", []))
    merged["v6_contract_diagnostics"] = dict(validated_response.get("diagnostics", {}))
    merged["executive_summary"] = _build_v6_executive_summary(
        static_score=static_score,
        static_band=static_band,
        merged_score=merged["overall_score"],
        merged_band=merged["readiness_band"],
        adjustments=merged["v6_score_adjustments"],
        existing_summary=str(static_report.get("executive_summary", "") or "").strip(),
        pr_context=merged.get("pr_context", {}),
    )
    return merged


def append_static_contract_limitation(report: Mapping[str, Any], message: str) -> dict[str, Any]:
    updated = copy.deepcopy(dict(report))
    updated["audit_mode"] = "static_contract_ready"
    updated["limitations"] = _unique_text(
        [
            *_safe_text_list(updated.get("limitations", []), limit=6),
            _sanitize_text(message, max_length=180),
        ]
    )[:6]
    return updated


def append_contract_rejection_limitation(report: Mapping[str, Any], message: str) -> dict[str, Any]:
    updated = copy.deepcopy(dict(report))
    updated["audit_mode"] = "static_contract_rejected"
    updated["limitations"] = _unique_text(
        [
            *_safe_text_list(updated.get("limitations", []), limit=6),
            _sanitize_text(message, max_length=180),
        ]
    )[:6]
    return updated


def _build_category_payload(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    categories_raw = report.get("categories", [])
    categories = []
    if isinstance(categories_raw, Sequence) and not isinstance(categories_raw, (str, bytes)):
        for item in categories_raw:
            if not isinstance(item, Mapping):
                continue
            key = _normalize_category_key(item.get("key"))
            categories.append(
                {
                    "key": key,
                    "title": _CATEGORY_TITLES_BY_KEY[key],
                    "score": _bounded_int(item.get("score", 0), minimum=0, maximum=_CATEGORY_MAX_BY_KEY[key]),
                    "max": _CATEGORY_MAX_BY_KEY[key],
                    "label": _safe_category_label(item.get("label", "UNKNOWN")),
                    "rationale": _sanitize_text(item.get("rationale", "No rationale recorded."), max_length=AUDIT_V6_MAX_TEXT_LENGTH),
                    "evidence_paths": _sanitize_evidence_paths(item.get("evidence_paths", []), limit=4),
                }
            )
    if len(categories) != len(CATEGORY_SPECS):
        raise AuditContractError("Static audit report categories are incomplete.")
    categories.sort(key=lambda item: _CATEGORY_ORDER.index(item["key"]))
    return categories


def _build_repo_signals(report: Mapping[str, Any]) -> dict[str, Any]:
    evidence_summary = report.get("evidence_summary", {}) if isinstance(report.get("evidence_summary", {}), Mapping) else {}
    key_files = [str(item).strip() for item in evidence_summary.get("key_files", []) if str(item).strip()]
    workflows = [str(item).strip() for item in evidence_summary.get("workflows_considered", []) if str(item).strip()]
    docs = [str(item).strip() for item in evidence_summary.get("docs_considered", []) if str(item).strip()]
    tests = [str(item).strip() for item in evidence_summary.get("tests_considered", []) if str(item).strip()]
    manifests = [str(item).strip() for item in evidence_summary.get("manifests_considered", []) if str(item).strip()]
    blockers = report.get("critical_blockers", []) if isinstance(report.get("critical_blockers", []), Sequence) else []
    dangerous_permissions = any(
        isinstance(item, Mapping) and str(item.get("category", "")).strip().lower() == "security posture"
        for item in blockers
    )
    return {
        "has_tests": bool(tests),
        "has_ci": bool(workflows),
        "has_docs": bool(docs),
        "has_release_files": any(Path(path).name.upper() in {"VERSION", "CHANGELOG.MD", "LICENSE"} or "release" in path.lower() for path in key_files),
        "has_security_policy": any("security" in path.lower() for path in key_files),
        "risky_permissions_detected": bool(dangerous_permissions),
        "dependency_manifest_count": len(manifests),
        "workflow_count": len(workflows),
        "docs_count": len(docs),
        "test_file_count": len(tests),
    }


def _build_evidence_manifest(
    *,
    report: Mapping[str, Any],
    pr_changed_files: set[str],
) -> list[dict[str, Any]]:
    evidence_summary = report.get("evidence_summary", {}) if isinstance(report.get("evidence_summary", {}), Mapping) else {}
    candidates: list[tuple[str, str, str]] = []
    for path in _safe_string_list(evidence_summary.get("key_files", [])):
        candidates.append((path, _path_kind(path), "key_evidence"))
    for path in _safe_string_list(evidence_summary.get("workflows_considered", [])):
        candidates.append((path, "workflow", "workflow_considered"))
    for path in _safe_string_list(evidence_summary.get("docs_considered", [])):
        candidates.append((path, "documentation", "documentation_considered"))
    for path in _safe_string_list(evidence_summary.get("tests_considered", [])):
        candidates.append((path, "test", "test_considered"))
    for path in _safe_string_list(evidence_summary.get("manifests_considered", [])):
        candidates.append((path, "manifest", "manifest_considered"))

    seen: set[str] = set()
    manifest: list[dict[str, Any]] = []
    for path, kind, reason in candidates:
        safe_path = _sanitize_repo_path(path)
        if not safe_path or safe_path in seen:
            continue
        seen.add(safe_path)
        manifest.append(
            {
                "path": safe_path,
                "kind": kind,
                "reason": reason,
                "is_changed_file": safe_path in pr_changed_files,
                "safe_excerpt": "",
            }
        )
        if len(manifest) >= AUDIT_V6_MAX_EVIDENCE_ITEMS:
            break
    return manifest


def _normalize_response_category(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise AuditContractError("v6 audit response category item must be a mapping.")
    key = _normalize_category_key(item.get("key") or item.get("category"))
    max_score = _bounded_int(item.get("max", _CATEGORY_MAX_BY_KEY[key]), minimum=0, maximum=100)
    if max_score != _CATEGORY_MAX_BY_KEY[key]:
        raise AuditContractError("v6 audit response category max score mismatch.")
    score = _bounded_int(item.get("score", 0), minimum=0, maximum=max_score)
    return {
        "key": key,
        "title": _CATEGORY_TITLES_BY_KEY[key],
        "score": score,
        "max_score": max_score,
        "label": _safe_category_label(item.get("label", "UNKNOWN")),
        "rationale": _sanitize_text(item.get("rationale", "No rationale recorded."), max_length=AUDIT_V6_MAX_TEXT_LENGTH),
        "evidence_paths": _sanitize_evidence_paths(item.get("evidence_paths", []), limit=4),
    }


def _normalize_bounded_item_list(value: Any, *, limit: int, item_kind: str) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    normalized: list[dict[str, Any]] = []
    for item in list(value)[:limit]:
        if not isinstance(item, Mapping):
            raise AuditContractError(f"v6 audit {item_kind} item must be a mapping.")
        normalized.append(
            {
                "title": _sanitize_text(item.get("title", "Untitled item"), max_length=140),
                "category": _sanitize_text(item.get("category", "General"), max_length=80),
                "rationale": _sanitize_text(item.get("rationale", "No rationale recorded."), max_length=AUDIT_V6_MAX_TEXT_LENGTH),
                "expected_score_impact": _sanitize_text(item.get("impact", item.get("expected_score_impact", "medium")), max_length=24).lower() or "medium",
                "affected_files": _sanitize_evidence_paths(item.get("affected_files", item.get("evidence_paths", [])), limit=4),
                "evidence_paths": _sanitize_evidence_paths(item.get("evidence_paths", item.get("affected_files", [])), limit=4),
            }
        )
    return normalized


def _extract_diagnostic_warnings(response: Mapping[str, Any]) -> list[str]:
    diagnostics = response.get("diagnostics", {})
    if not isinstance(diagnostics, Mapping):
        return []
    return _safe_text_list(diagnostics.get("sanitized_warnings", diagnostics.get("warnings", [])), limit=6)


def _build_v6_executive_summary(
    *,
    static_score: int,
    static_band: str,
    merged_score: int,
    merged_band: str,
    adjustments: Sequence[Mapping[str, Any]],
    existing_summary: str,
    pr_context: Mapping[str, Any] | None = None,
) -> str:
    is_pr = bool((pr_context or {}).get("is_pr", False))
    pr_suffix = " with PR context" if is_pr else ""
    delta = merged_score - static_score
    final_intro = f"The final RepoBrain score{pr_suffix} is `{merged_score} / 100` (`{merged_band}`)."
    if delta == 0:
        return (
            f"{final_intro} Static baseline was `{static_score} / 100` (`{static_band}`), and v6 bounded enrichment "
            f"retained the same final score with deeper rationale."
        )
    count = len(adjustments)
    delta_text = f"+{delta}" if delta > 0 else str(delta)
    return (
        f"{final_intro} Static baseline was `{static_score} / 100` (`{static_band}`), and v6 bounded enrichment "
        f"adjusted the final score by `{delta_text}`"
        f"{' across ' + str(count) + ' bounded adjustments' if count else ''}."
    )


def _assert_no_forbidden_content(value: Any) -> None:
    for text in _iter_text_values(value):
        if any(pattern.search(text) for pattern in _TOKEN_PATTERNS):
            raise AuditContractError("v6 audit contract content contained a token-like secret.")
        if any(pattern.search(text) for pattern in _PRIVATE_PATH_PATTERNS):
            raise AuditContractError("v6 audit contract content contained a private path.")
        if any(pattern.search(text) for pattern in _UNSAFE_TEXT_PATTERNS):
            raise AuditContractError("v6 audit contract content contained an unsafe claim.")
        if _PATH_TOKEN_RE.search(text) and any(sep in text for sep in ("\\", "/")):
            lowered = text.lower()
            if ".topocore-v6" in lowered or "ariadna_minsk" in lowered or "c:\\users" in lowered or "/mnt/data" in lowered:
                raise AuditContractError("v6 audit contract content contained a local/private path.")


def _iter_text_values(value: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            texts.append(str(key))
            texts.extend(_iter_text_values(item))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            texts.extend(_iter_text_values(item))
    elif isinstance(value, (str, bytes)):
        texts.append(str(value))
    return texts


def _sanitize_evidence_paths(value: Any, *, limit: int) -> list[str]:
    paths = []
    for item in _safe_string_list(value):
        safe = _sanitize_repo_path(item)
        if safe:
            paths.append(safe)
    return _unique_text(paths)[:limit]


def _sanitize_repo_path(value: Any) -> str:
    text = _normalize_repo_relative_path(value)
    if not text:
        return ""
    lowered = text.lower()
    if any(token in lowered for token in (".topocore-v6", "ariadna_minsk", "c:\\users", "/mnt/data")):
        return ""
    if any(token in lowered for token in ("/artifacts/", "artifacts/", "/reports/", "reports/")):
        return ""
    if any(
        token in lowered
        for token in ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", "dist/", "build/")
    ):
        return ""
    return text


def _path_kind(path: str) -> str:
    lowered = path.lower()
    if lowered.startswith(".github/workflows/"):
        return "workflow"
    if lowered.startswith("docs/") or lowered == "readme.md":
        return "documentation"
    if lowered.startswith("tests/"):
        return "test"
    if Path(path).name.lower() in {"pyproject.toml", "package.json", "requirements.txt", "go.mod"}:
        return "manifest"
    return "file"


def _safe_text_list(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    cleaned = [_sanitize_text(item, max_length=AUDIT_V6_MAX_TEXT_LENGTH) for item in value]
    return [item for item in cleaned if item][:limit]


def _safe_string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _safe_optional_int(value: Any) -> int | None:
    try:
        if value in {"", None}:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _sanitize_text(value: Any, *, max_length: int = AUDIT_V6_MAX_TEXT_LENGTH) -> str:
    text = " ".join(str(value or "").split())
    text = text.replace("`", "'")
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub("[redacted-secret]", text)
    text = _PATH_CANDIDATE_RE.sub(_sanitize_path_match, text)
    return text[:max_length].strip()


def _bounded_int(value: Any, *, minimum: int, maximum: int) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        raise AuditContractError("v6 audit contract expected an integer score.") from None
    if normalized < minimum or normalized > maximum:
        raise AuditContractError("v6 audit contract score was out of bounds.")
    return normalized


def _safe_readiness_band(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text not in _READINESS_LABELS:
        raise AuditContractError("v6 audit readiness band was invalid.")
    return text


def _safe_category_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text not in _CATEGORY_LABELS:
        raise AuditContractError("v6 audit category label was invalid.")
    return text


def _safe_confidence(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text not in {"high", "medium", "low"}:
        return "medium"
    return text


def _normalize_category_key(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in _CATEGORY_MAX_BY_KEY:
        return text
    for key, title in _CATEGORY_TITLES_BY_KEY.items():
        if text == title.lower():
            return key
    raise AuditContractError("v6 audit category key was invalid.")


def _normalize_category_title(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _maxed_category_titles(categories: Sequence[Mapping[str, Any]] | Any) -> set[str]:
    maxed: set[str] = set()
    if not isinstance(categories, Sequence) or isinstance(categories, (str, bytes)):
        return maxed
    for item in categories:
        if not isinstance(item, Mapping):
            continue
        title = _normalize_category_title(item.get("title", ""))
        if not title:
            continue
        try:
            score = int(item.get("score", 0))
            max_score = int(item.get("max_score", 0))
        except (TypeError, ValueError):
            continue
        if max_score > 0 and score >= max_score:
            maxed.add(title)
    return maxed


def _is_advisory_maintenance_item(text: Any) -> bool:
    normalized = " ".join(str(text or "").strip().lower().split())
    if not normalized:
        return False
    advisory_markers = ("maintain", "monitor", "preserve", "keep", "watch", "guard", "drift")
    return any(marker in normalized for marker in advisory_markers)


def _filter_renderable_top_improvements(
    improvements: Sequence[Mapping[str, Any]] | Any,
    *,
    categories: Sequence[Mapping[str, Any]] | Any,
) -> list[dict[str, Any]]:
    if not isinstance(improvements, Sequence) or isinstance(improvements, (str, bytes)):
        return []
    maxed_titles = _maxed_category_titles(categories)
    filtered: list[dict[str, Any]] = []
    for item in improvements:
        if not isinstance(item, Mapping):
            continue
        category = _normalize_category_title(item.get("category", ""))
        title = str(item.get("title", "") or "").strip()
        if category in maxed_titles and not _is_advisory_maintenance_item(title):
            continue
        filtered.append(dict(item))
    return filtered


def _extract_roadmap_category(item_text: str) -> str:
    match = re.search(r"\(([^()]+)\)\s*$", str(item_text or "").strip())
    if not match:
        return ""
    return _normalize_category_title(match.group(1))


def _filter_renderable_roadmap(
    roadmap: Mapping[str, Any] | Any,
    *,
    categories: Sequence[Mapping[str, Any]] | Any,
) -> dict[str, list[str]]:
    if not isinstance(roadmap, Mapping):
        return {"30_days": [], "60_days": [], "90_days": []}
    maxed_titles = _maxed_category_titles(categories)
    filtered: dict[str, list[str]] = {}
    for phase in ("30_days", "60_days", "90_days"):
        raw_items = roadmap.get(phase, [])
        items = [str(item).strip() for item in raw_items if str(item).strip()] if isinstance(raw_items, Sequence) and not isinstance(raw_items, (str, bytes)) else []
        filtered_phase: list[str] = []
        for item_text in items:
            category = _extract_roadmap_category(item_text)
            if category in maxed_titles and not _is_advisory_maintenance_item(item_text):
                continue
            filtered_phase.append(item_text)
        filtered[phase] = filtered_phase
    return filtered


def _split_repository_name(value: str) -> tuple[str, str]:
    text = str(value or "").strip()
    if "/" not in text:
        return "", text
    owner, repo = text.split("/", 1)
    return _sanitize_text(owner, max_length=80), _sanitize_text(repo, max_length=120)


def _unique_text(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _sanitize_path_match(match: re.Match[str]) -> str:
    candidate = str(match.group("path") or "").strip()
    safe_path = _normalize_repo_relative_path(candidate)
    if safe_path:
        return safe_path
    return "[redacted-path]"


def _normalize_repo_relative_path(value: Any) -> str:
    raw = " ".join(str(value or "").split()).strip().replace("\\", "/").replace("`", "")
    if not raw:
        return ""
    while raw.startswith("./"):
        raw = raw[2:]
    raw = re.sub(r"/{2,}", "/", raw)
    lowered = raw.lower()
    if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
        return ""
    if raw.startswith("../") or "/../" in raw or lowered.startswith("~/"):
        return ""
    if any(pattern.search(raw) for pattern in _TOKEN_PATTERNS):
        return ""
    if any(pattern.search(raw) for pattern in _PRIVATE_PATH_PATTERNS):
        return ""
    segments = [segment for segment in raw.split("/") if segment]
    if not segments:
        return ""
    if any(segment in {".", ".."} for segment in segments):
        return ""
    if any(not _REPO_RELATIVE_SEGMENT_RE.match(segment) for segment in segments):
        return ""
    if any(segment.lower() in _FORBIDDEN_PATH_SEGMENTS for segment in segments):
        return ""
    normalized = "/".join(segments)
    lowered = normalized.lower()
    if any(marker in lowered for marker in _SENSITIVE_PATH_MARKERS):
        return ""
    return normalized[:160]
