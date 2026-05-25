from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class AuditCategorySpec:
    key: str
    title: str
    max_score: int


CATEGORY_SPECS: tuple[AuditCategorySpec, ...] = (
    AuditCategorySpec("architecture", "Architecture and modularity", 15),
    AuditCategorySpec("code_quality", "Code quality and maintainability", 12),
    AuditCategorySpec("testing", "Testing and validation", 12),
    AuditCategorySpec("security", "Security posture", 12),
    AuditCategorySpec("ci_cd", "CI/CD and automation", 10),
    AuditCategorySpec("dependencies", "Dependency hygiene", 8),
    AuditCategorySpec("documentation", "Documentation and onboarding", 8),
    AuditCategorySpec("release_ops", "Release and operations readiness", 8),
    AuditCategorySpec("governance", "GitHub governance", 8),
    AuditCategorySpec("ai_readiness", "AI-readiness / repository intelligence", 7),
)

READINESS_BANDS: tuple[tuple[int, str], ...] = (
    (85, "STRONG"),
    (70, "GOOD"),
    (50, "NEEDS_ATTENTION"),
    (0, "WEAK"),
)

_IGNORE_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".topocore-v6",
    ".codex-skill-install-tmp",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "artifacts",
    "reports",
    "coverage",
    "htmlcov",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".idea",
    ".vscode",
    ".next",
}
_IGNORE_FILE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".jar",
    ".dll",
    ".so",
    ".dylib",
    ".exe",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".mp4",
    ".mov",
    ".avi",
    ".wav",
    ".mp3",
}
_CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".php",
    ".cs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
}
_MANIFEST_NAMES = {
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "go.mod",
    "cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "gemfile",
    "composer.json",
}
_LOCKFILE_NAMES = {
    "uv.lock",
    "poetry.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "cargo.lock",
    "gemfile.lock",
    "composer.lock",
}
_LINT_CONFIG_NAMES = {
    ".ruff.toml",
    "ruff.toml",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.cjs",
    ".eslintrc.json",
    ".flake8",
    "tox.ini",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.js",
}
_TYPE_CONFIG_NAMES = {
    "mypy.ini",
    "pyrightconfig.json",
    "tsconfig.json",
}
_FORMAT_CONFIG_NAMES = {
    ".editorconfig",
    "black.toml",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.js",
}
_ENTRYPOINT_NAMES = {
    "main.py",
    "app.py",
    "cli.py",
    "server.py",
    "index.ts",
    "index.js",
    "action.yml",
}
_WORKFLOW_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")
_MAX_TRACKED_FILES = 5000
_MAX_TEXT_BYTES = 200_000


def category_weight_total() -> int:
    return sum(item.max_score for item in CATEGORY_SPECS)


def readiness_band_for_score(score: int) -> str:
    normalized = max(0, min(100, int(score)))
    for threshold, label in READINESS_BANDS:
        if normalized >= threshold:
            return label
    return "WEAK"


def score_repository_audit(
    *,
    repo_root: Path,
    query: str = "",
    github_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = _scan_inventory(repo_root)
    categories = _build_category_results(inventory)
    overall_score = sum(int(item["score"]) for item in categories)
    readiness_band = readiness_band_for_score(overall_score)
    confidence = _resolve_confidence(inventory=inventory, categories=categories)
    critical_blockers = _build_critical_blockers(inventory=inventory, categories=categories)
    top_improvements = _build_top_improvements(inventory=inventory, categories=categories)
    roadmap = _build_roadmap(critical_blockers=critical_blockers, top_improvements=top_improvements)
    evidence_summary = _build_evidence_summary(inventory=inventory, github_context=github_context)
    limitations = _build_limitations(inventory=inventory, github_context=github_context)
    executive_summary = _build_executive_summary(
        categories=categories,
        overall_score=overall_score,
        readiness_band=readiness_band,
        query=query,
        github_context=github_context,
        critical_blockers=critical_blockers,
    )
    return {
        "overall_score": max(0, min(100, overall_score)),
        "readiness_band": readiness_band,
        "confidence": confidence,
        "executive_summary": executive_summary,
        "categories": categories,
        "critical_blockers": critical_blockers,
        "top_improvements": top_improvements,
        "roadmap": roadmap,
        "evidence_summary": evidence_summary,
        "limitations": limitations,
        "query": str(query or "").strip(),
        "pr_context": _build_pr_context(github_context),
        "inventory_summary": {
            "file_count": int(inventory["file_count"]),
            "workflow_count": len(inventory["workflow_paths"]),
            "docs_count": len(inventory["docs_paths"]),
            "test_count": len(inventory["test_paths"]),
            "manifest_count": len(inventory["manifest_paths"]),
            "inventory_truncated": bool(inventory["inventory_truncated"]),
        },
    }


def _scan_inventory(repo_root: Path) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    files: list[str] = []
    truncated = False
    for current_root, dir_names, file_names in os.walk(repo_root):
        dir_names[:] = [
            item
            for item in dir_names
            if item not in _IGNORE_DIR_NAMES and item != ".git" and (not item.startswith(".") or item == ".github")
        ]
        for file_name in file_names:
            absolute = Path(current_root) / file_name
            if _should_ignore_file(absolute):
                continue
            relative = absolute.relative_to(repo_root).as_posix()
            files.append(relative)
            if len(files) >= _MAX_TRACKED_FILES:
                truncated = True
                break
        if truncated:
            break

    file_set = set(files)
    workflow_paths = sorted(
        path for path in file_set if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
    )
    docs_paths = sorted(path for path in file_set if path == "README.md" or path.startswith("docs/"))
    markdown_paths = sorted(path for path in file_set if path.endswith(".md"))
    test_paths = sorted(
        path
        for path in file_set
        if path.startswith("tests/")
        or "/tests/" in path
        or Path(path).name.startswith("test_")
        or Path(path).name.endswith("_test.py")
    )
    code_paths = sorted(
        path for path in file_set if Path(path).suffix.lower() in _CODE_EXTENSIONS and not path.startswith("tests/")
    )
    top_level_code_paths = [path for path in code_paths if "/" not in path]
    code_roots = sorted(
        {
            Path(path).parts[0]
            for path in code_paths
            if len(Path(path).parts) > 1 and Path(path).parts[0] not in {"docs", "tests", ".github"}
        }
    )
    manifest_paths = sorted(path for path in file_set if Path(path).name.lower() in _MANIFEST_NAMES)
    lockfile_paths = sorted(path for path in file_set if Path(path).name.lower() in _LOCKFILE_NAMES)
    lint_paths = sorted(path for path in file_set if Path(path).name.lower() in {name.lower() for name in _LINT_CONFIG_NAMES})
    type_paths = sorted(path for path in file_set if Path(path).name.lower() in {name.lower() for name in _TYPE_CONFIG_NAMES})
    format_paths = sorted(path for path in file_set if Path(path).name.lower() in {name.lower() for name in _FORMAT_CONFIG_NAMES})
    entrypoint_paths = sorted(path for path in file_set if Path(path).name.lower() in {name.lower() for name in _ENTRYPOINT_NAMES})
    architecture_paths = sorted(path for path in file_set if "architecture" in path.lower())
    security_paths = sorted(path for path in file_set if "security" in path.lower())
    release_paths = sorted(
        path
        for path in file_set
        if Path(path).name.upper() in {"VERSION", "CHANGELOG.MD", "LICENSE"}
        or path.startswith("docs/release/")
    )
    governance_paths = sorted(
        path
        for path in file_set
        if Path(path).name == "CODEOWNERS"
        or "ISSUE_TEMPLATE" in path
        or "pull_request_template" in path.lower()
        or path.startswith("docs/troubleshooting/")
    )
    workflow_texts = {path: _read_text_limited(repo_root / path) for path in workflow_paths}
    workflow_text_joined = "\n".join(workflow_texts.values()).lower()
    permissions_block_present = "permissions:" in workflow_text_joined
    dangerous_permissions = sorted(
        {
            item
            for item, pattern in (
                ("pull_request_target", r"\bpull_request_target\b"),
                ("contents: write", r"contents\s*:\s*write"),
                ("checks: write", r"checks\s*:\s*write"),
                ("pull-requests: write", r"pull-requests\s*:\s*write"),
            )
            if re.search(pattern, workflow_text_joined)
        }
    )
    ci_keywords = (
        "pytest",
        "ruff",
        "npm test",
        "pnpm test",
        "yarn test",
        "go test",
        "cargo test",
        "jest",
        "vitest",
    )
    ci_keywords_detected = sorted({item for item in ci_keywords if item in workflow_text_joined})
    docs_text_paths = [
        path
        for path in (
            "README.md",
            "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
            "docs/commands/REPOBRAIN_COMMANDS.md",
            "docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md",
        )
        if path in file_set
    ]
    docs_text = "\n".join(_read_text_limited(repo_root / path) for path in docs_text_paths).lower()
    manifest_text = "\n".join(_read_text_limited(repo_root / path) for path in manifest_paths[:3]).lower()
    has_install_docs = "install" in docs_text or any("onboarding" in path.lower() for path in docs_paths)
    has_troubleshooting_docs = "troubleshooting" in docs_text or any("troubleshooting" in path.lower() for path in docs_paths)
    has_command_docs = "/repobrain" in docs_text or any("commands" in path.lower() for path in docs_paths)
    has_embedded_lint_config = any(
        token in manifest_text
        for token in ("[tool.ruff", "[tool.black", "[tool.flake8", "\"eslintconfig\"", "\"prettier\"")
    )
    has_embedded_type_config = any(
        token in manifest_text
        for token in ("[tool.mypy", "\"typescript\"", "\"tsconfig\"", "\"pyright\"")
    )
    has_embedded_format_config = any(
        token in manifest_text
        for token in ("[tool.black", "[tool.ruff", "\"prettier\"", ".editorconfig")
    )
    return {
        "repo_root": repo_root,
        "files": files,
        "file_set": file_set,
        "file_count": len(files),
        "inventory_truncated": truncated,
        "workflow_paths": workflow_paths,
        "docs_paths": docs_paths,
        "markdown_paths": markdown_paths,
        "test_paths": test_paths,
        "code_paths": code_paths,
        "top_level_code_paths": top_level_code_paths,
        "code_roots": code_roots,
        "manifest_paths": manifest_paths,
        "lockfile_paths": lockfile_paths,
        "lint_paths": lint_paths,
        "type_paths": type_paths,
        "format_paths": format_paths,
        "has_embedded_lint_config": has_embedded_lint_config,
        "has_embedded_type_config": has_embedded_type_config,
        "has_embedded_format_config": has_embedded_format_config,
        "entrypoint_paths": entrypoint_paths,
        "architecture_paths": architecture_paths,
        "security_paths": security_paths,
        "release_paths": release_paths,
        "governance_paths": governance_paths,
        "workflow_texts": workflow_texts,
        "permissions_block_present": permissions_block_present,
        "dangerous_permissions": dangerous_permissions,
        "ci_keywords_detected": ci_keywords_detected,
        "has_readme": "README.md" in file_set,
        "has_license": "LICENSE" in file_set,
        "has_version": "VERSION" in file_set,
        "has_changelog": "CHANGELOG.md" in file_set,
        "has_docs_dir": any(path.startswith("docs/") for path in docs_paths),
        "has_install_docs": has_install_docs,
        "has_troubleshooting_docs": has_troubleshooting_docs,
        "has_command_docs": has_command_docs,
        "has_codeowners": "CODEOWNERS" in file_set or ".github/CODEOWNERS" in file_set,
        "has_issue_templates": any("ISSUE_TEMPLATE" in path for path in file_set),
        "has_pr_template": any("pull_request_template" in path.lower() for path in file_set),
}


def _read_text_limited(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    return raw[:_MAX_TEXT_BYTES].decode("utf-8", errors="ignore")


def _should_ignore_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in _IGNORE_FILE_EXTENSIONS:
        return True
    if path.name.lower().endswith((".min.js", ".min.css")):
        return True
    try:
        if path.stat().st_size > _MAX_TEXT_BYTES * 2:
            return True
    except OSError:
        return True
    return False


def _build_category_results(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _architecture_result(inventory),
        _code_quality_result(inventory),
        _testing_result(inventory),
        _security_result(inventory),
        _ci_cd_result(inventory),
        _dependency_result(inventory),
        _documentation_result(inventory),
        _release_ops_result(inventory),
        _governance_result(inventory),
        _ai_readiness_result(inventory),
    ]


def _category_result(
    *,
    title: str,
    key: str,
    max_score: int,
    score: int,
    rationale: str,
    evidence_paths: list[str],
    assessable: bool = True,
) -> dict[str, Any]:
    bounded = max(0, min(max_score, int(score)))
    label = _category_label(score=bounded, max_score=max_score, assessable=assessable)
    return {
        "key": key,
        "title": title,
        "score": bounded,
        "max_score": max_score,
        "label": label,
        "rationale": rationale.strip() or "No clear rationale captured.",
        "evidence_paths": _unique_paths(evidence_paths)[:4],
        "assessable": bool(assessable),
    }


def _category_label(*, score: int, max_score: int, assessable: bool) -> str:
    if not assessable:
        return "UNKNOWN"
    ratio = (float(score) / float(max_score)) if max_score else 0.0
    if ratio >= 0.85:
        return "STRONG"
    if ratio >= 0.70:
        return "GOOD"
    if ratio >= 0.45:
        return "NEEDS_ATTENTION"
    return "WEAK"


def _architecture_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence: list[str] = []
    score = 0
    if inventory["code_roots"]:
        score += 6
        evidence.extend(inventory["code_roots"][:2])
    if len(inventory["top_level_code_paths"]) <= 3 and inventory["code_paths"]:
        score += 4
        evidence.extend(inventory["top_level_code_paths"][:2])
    if inventory["architecture_paths"]:
        score += 3
        evidence.extend(inventory["architecture_paths"][:2])
    if inventory["entrypoint_paths"]:
        score += 2
        evidence.extend(inventory["entrypoint_paths"][:2])
    assessable = bool(inventory["code_paths"] or inventory["docs_paths"] or inventory["manifest_paths"])
    rationale_parts: list[str] = []
    if inventory["code_roots"]:
        rationale_parts.append(f"Code is split across {len(inventory['code_roots'])} clear root areas.")
    else:
        rationale_parts.append("Repository structure offers limited obvious code-root separation.")
    if inventory["architecture_paths"]:
        rationale_parts.append("Architecture-oriented docs are present.")
    else:
        rationale_parts.append("No architecture-specific documentation was detected.")
    if len(inventory["top_level_code_paths"]) > 3:
        rationale_parts.append("Several top-level code files may make entry points harder to follow.")
    return _category_result(
        title="Architecture and modularity",
        key="architecture",
        max_score=15,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _code_quality_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["lint_paths"]:
        score += 4
        evidence.extend(inventory["lint_paths"][:2])
    elif inventory["has_embedded_lint_config"]:
        score += 3
        evidence.extend(inventory["manifest_paths"][:1])
    if inventory["type_paths"]:
        score += 3
        evidence.extend(inventory["type_paths"][:2])
    elif inventory["has_embedded_type_config"]:
        score += 2
        evidence.extend(inventory["manifest_paths"][:1])
    if inventory["format_paths"]:
        score += 2
        evidence.extend(inventory["format_paths"][:2])
    elif inventory["has_embedded_format_config"]:
        score += 2
        evidence.extend(inventory["manifest_paths"][:1])
    if inventory["code_roots"]:
        score += 3
        evidence.extend(inventory["code_roots"][:2])
    assessable = bool(inventory["code_paths"] or inventory["manifest_paths"])
    rationale_parts = []
    if (
        inventory["lint_paths"]
        or inventory["type_paths"]
        or inventory["format_paths"]
        or inventory["has_embedded_lint_config"]
        or inventory["has_embedded_type_config"]
        or inventory["has_embedded_format_config"]
    ):
        rationale_parts.append("Static quality signals such as linting, typing, or formatting configs are present.")
    else:
        rationale_parts.append("No obvious lint/type/formatting configuration was detected.")
    if inventory["code_paths"]:
        rationale_parts.append(f"Detected {len(inventory['code_paths'])} code files for maintainability scoring.")
    else:
        rationale_parts.append("Little or no code was available for maintainability scoring.")
    return _category_result(
        title="Code quality and maintainability",
        key="code_quality",
        max_score=12,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _testing_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["test_paths"]:
        score += 6
        evidence.extend(inventory["test_paths"][:2])
    if inventory["ci_keywords_detected"]:
        score += 4
        evidence.extend(inventory["workflow_paths"][:2])
    if inventory["workflow_paths"]:
        score += 2
        evidence.extend(inventory["workflow_paths"][:1])
    assessable = bool(inventory["workflow_paths"] or inventory["test_paths"] or inventory["manifest_paths"])
    rationale_parts = []
    if inventory["test_paths"]:
        rationale_parts.append(f"Detected {len(inventory['test_paths'])} test paths.")
    else:
        rationale_parts.append("No automated tests were detected from repository structure.")
    if inventory["ci_keywords_detected"]:
        rationale_parts.append("Workflow files reference concrete validation commands.")
    else:
        rationale_parts.append("Workflow files do not clearly advertise test execution.")
    return _category_result(
        title="Testing and validation",
        key="testing",
        max_score=12,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _security_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["security_paths"]:
        score += 4
        evidence.extend(inventory["security_paths"][:2])
    if inventory["workflow_paths"]:
        score += 4
        evidence.extend(inventory["workflow_paths"][:2])
    if inventory["permissions_block_present"]:
        score += 2
    if not inventory["dangerous_permissions"]:
        score += 2
    penalties = 0
    if "pull_request_target" in inventory["dangerous_permissions"]:
        penalties += 4
    if "contents: write" in inventory["dangerous_permissions"]:
        penalties += 3
    if "checks: write" in inventory["dangerous_permissions"]:
        penalties += 1
    if "pull-requests: write" in inventory["dangerous_permissions"]:
        penalties += 2
    score -= penalties
    assessable = bool(inventory["workflow_paths"] or inventory["security_paths"] or inventory["docs_paths"])
    rationale_parts = []
    if inventory["security_paths"]:
        rationale_parts.append("Security-focused docs or policies are present.")
    else:
        rationale_parts.append("No dedicated security policy files were detected.")
    if inventory["dangerous_permissions"]:
        rationale_parts.append(
            "Workflow review found potentially risky triggers or permissions: "
            + ", ".join(f"`{item}`" for item in inventory["dangerous_permissions"])
            + "."
        )
    else:
        rationale_parts.append("No obvious dangerous workflow trigger or write-heavy permission pattern was detected.")
    return _category_result(
        title="Security posture",
        key="security",
        max_score=12,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _ci_cd_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["workflow_paths"]:
        score += 5
        evidence.extend(inventory["workflow_paths"][:2])
    if inventory["ci_keywords_detected"]:
        score += 3
    if inventory["permissions_block_present"] and not inventory["dangerous_permissions"]:
        score += 2
    assessable = bool(inventory["workflow_paths"])
    rationale_parts = []
    if inventory["workflow_paths"]:
        rationale_parts.append(f"Detected {len(inventory['workflow_paths'])} GitHub workflow files.")
    else:
        rationale_parts.append("No GitHub workflow automation was detected.")
    if inventory["ci_keywords_detected"]:
        rationale_parts.append("Automation appears to run concrete validation steps.")
    else:
        rationale_parts.append("Automation depth is hard to confirm from workflow content.")
    return _category_result(
        title="CI/CD and automation",
        key="ci_cd",
        max_score=10,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _dependency_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["manifest_paths"]:
        score += 4
        evidence.extend(inventory["manifest_paths"][:2])
    if inventory["lockfile_paths"]:
        score += 3
        evidence.extend(inventory["lockfile_paths"][:2])
    if any("dependabot" in path.lower() for path in inventory["files"]):
        score += 1
        evidence.extend([path for path in inventory["files"] if "dependabot" in path.lower()][:1])
    assessable = bool(inventory["manifest_paths"] or inventory["code_paths"])
    rationale_parts = []
    if inventory["manifest_paths"]:
        rationale_parts.append("Dependency manifests are present.")
    else:
        rationale_parts.append("No obvious dependency manifest was detected.")
    if inventory["lockfile_paths"]:
        rationale_parts.append("Lockfiles improve reproducibility.")
    else:
        rationale_parts.append("No lockfile was detected from the sampled inventory.")
    return _category_result(
        title="Dependency hygiene",
        key="dependencies",
        max_score=8,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _documentation_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["has_readme"]:
        score += 3
        evidence.append("README.md")
    if inventory["has_docs_dir"]:
        score += 2
        evidence.extend(inventory["docs_paths"][:2])
    if inventory["has_install_docs"] or inventory["has_troubleshooting_docs"] or inventory["has_command_docs"]:
        score += 2
    if inventory["architecture_paths"]:
        score += 1
        evidence.extend(inventory["architecture_paths"][:1])
    assessable = bool(inventory["has_readme"] or inventory["docs_paths"])
    rationale_parts = []
    if inventory["has_readme"]:
        rationale_parts.append("A README is present.")
    else:
        rationale_parts.append("No README was detected.")
    if inventory["has_install_docs"] or inventory["has_troubleshooting_docs"]:
        rationale_parts.append("Onboarding or troubleshooting documentation exists.")
    else:
        rationale_parts.append("Setup and support documentation looks thin.")
    return _category_result(
        title="Documentation and onboarding",
        key="documentation",
        max_score=8,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _release_ops_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["has_version"]:
        score += 2
        evidence.append("VERSION")
    if inventory["has_changelog"]:
        score += 2
        evidence.append("CHANGELOG.md")
    if inventory["has_license"]:
        score += 2
        evidence.append("LICENSE")
    if inventory["release_paths"]:
        score += 2
        evidence.extend([path for path in inventory["release_paths"] if path.startswith("docs/release/")][:2])
    assessable = bool(inventory["release_paths"] or inventory["has_version"] or inventory["has_changelog"] or inventory["has_license"])
    rationale_parts = []
    if inventory["has_version"] or inventory["has_changelog"] or inventory["has_license"]:
        rationale_parts.append("Versioning, changelog, or license metadata is present.")
    else:
        rationale_parts.append("Release metadata is minimal or absent.")
    if any(path.startswith("docs/release/") for path in inventory["release_paths"]):
        rationale_parts.append("Release process documentation exists.")
    else:
        rationale_parts.append("No dedicated release-process docs were detected.")
    return _category_result(
        title="Release and operations readiness",
        key="release_ops",
        max_score=8,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _governance_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["permissions_block_present"]:
        score += 2
        evidence.extend(inventory["workflow_paths"][:1])
    if inventory["has_codeowners"]:
        score += 2
        evidence.append(".github/CODEOWNERS" if ".github/CODEOWNERS" in inventory["file_set"] else "CODEOWNERS")
    if inventory["has_issue_templates"]:
        score += 2
        evidence.extend([path for path in inventory["files"] if "ISSUE_TEMPLATE" in path][:1])
    if inventory["has_pr_template"]:
        score += 1
        evidence.extend([path for path in inventory["files"] if "pull_request_template" in path.lower()][:1])
    if inventory["has_troubleshooting_docs"]:
        score += 1
        evidence.extend([path for path in inventory["docs_paths"] if "troubleshooting" in path.lower()][:1])
    if "pull_request_target" in inventory["dangerous_permissions"]:
        score -= 2
    assessable = bool(inventory["workflow_paths"] or inventory["governance_paths"] or inventory["docs_paths"])
    rationale_parts = []
    if inventory["has_codeowners"] or inventory["has_issue_templates"] or inventory["has_pr_template"]:
        rationale_parts.append("Some GitHub governance scaffolding is present.")
    else:
        rationale_parts.append("Little GitHub governance scaffolding was detected.")
    if inventory["permissions_block_present"]:
        rationale_parts.append("Workflow permissions are explicit.")
    else:
        rationale_parts.append("Workflow permission intent is not explicit.")
    return _category_result(
        title="GitHub governance",
        key="governance",
        max_score=8,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _ai_readiness_result(inventory: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    score = 0
    if inventory["has_readme"] or inventory["has_docs_dir"]:
        score += 2
        evidence.append("README.md" if inventory["has_readme"] else inventory["docs_paths"][0])
    if inventory["manifest_paths"]:
        score += 2
        evidence.extend(inventory["manifest_paths"][:1])
    if inventory["workflow_paths"]:
        score += 1
        evidence.extend(inventory["workflow_paths"][:1])
    if inventory["architecture_paths"] or inventory["governance_paths"]:
        score += 2
        evidence.extend((inventory["architecture_paths"] or inventory["governance_paths"])[:2])
    assessable = bool(inventory["docs_paths"] or inventory["code_paths"] or inventory["manifest_paths"])
    rationale_parts = []
    if inventory["has_readme"] or inventory["has_docs_dir"]:
        rationale_parts.append("Repository intent and operating model are documented enough for machine-assisted analysis.")
    else:
        rationale_parts.append("Repository intent is sparsely documented for repository intelligence tooling.")
    if inventory["manifest_paths"] and inventory["workflow_paths"]:
        rationale_parts.append("Machine-readable configs and workflow signals are available.")
    else:
        rationale_parts.append("Machine-readable config and workflow coverage is still thin.")
    return _category_result(
        title="AI-readiness / repository intelligence",
        key="ai_readiness",
        max_score=7,
        score=score,
        rationale=" ".join(rationale_parts),
        evidence_paths=evidence,
        assessable=assessable,
    )


def _build_critical_blockers(*, inventory: dict[str, Any], categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if not inventory["workflow_paths"]:
        blockers.append(
            _blocker(
                title="No CI workflow detected",
                category="CI/CD and automation",
                evidence=[],
                rationale="The repository does not expose a GitHub workflow, so validation and automation readiness are hard to trust.",
            )
        )
    if not inventory["test_paths"]:
        blockers.append(
            _blocker(
                title="No automated tests detected",
                category="Testing and validation",
                evidence=[],
                rationale="The MVP audit did not find a `tests/` surface or test-named files, which materially lowers confidence in change safety.",
            )
        )
    if "pull_request_target" in inventory["dangerous_permissions"]:
        blockers.append(
            _blocker(
                title="Workflow uses `pull_request_target`",
                category="Security posture",
                evidence=inventory["workflow_paths"][:2],
                rationale="This trigger expands risk for untrusted contribution flows and should be reviewed before a public-facing demo.",
            )
        )
    for permission_name in ("contents: write", "checks: write", "pull-requests: write"):
        if permission_name in inventory["dangerous_permissions"]:
            blockers.append(
                _blocker(
                    title=f"Workflow permissions include `{permission_name}`",
                    category="Security posture",
                    evidence=inventory["workflow_paths"][:2],
                    rationale="Write-heavy workflow permissions increase blast radius unless they are explicitly required and justified.",
                )
            )
    if not inventory["has_readme"] and not inventory["has_docs_dir"]:
        blockers.append(
            _blocker(
                title="No onboarding docs detected",
                category="Documentation and onboarding",
                evidence=[],
                rationale="A repository without a README or docs surface is difficult to evaluate and hand off safely.",
            )
        )
    return blockers[:5]


def _blocker(*, title: str, category: str, evidence: list[str], rationale: str) -> dict[str, Any]:
    return {
        "title": title,
        "category": category,
        "evidence_paths": _unique_paths(evidence)[:3],
        "rationale": rationale.strip(),
    }


def _build_top_improvements(*, inventory: dict[str, Any], categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    improvements: list[dict[str, Any]] = []
    if not inventory["test_paths"]:
        improvements.append(
            _improvement(
                category="Testing and validation",
                title="Add at least one automated test surface and wire it into CI.",
                affected_files=inventory["workflow_paths"][:2],
                rationale="Tests and CI are the fastest way to improve audit confidence and reduce regression risk.",
                expected_score_impact="high",
            )
        )
    if not inventory["workflow_paths"]:
        improvements.append(
            _improvement(
                category="CI/CD and automation",
                title="Add a read-only GitHub workflow that runs validation on pushes and pull requests.",
                affected_files=[],
                rationale="Automation makes repository quality repeatable and visible to contributors.",
                expected_score_impact="high",
            )
        )
    if inventory["dangerous_permissions"]:
        improvements.append(
            _improvement(
                category="Security posture",
                title="Reduce workflow triggers and permissions to the minimum required baseline.",
                affected_files=inventory["workflow_paths"][:2],
                rationale="Safer workflow defaults improve both security posture and governance confidence.",
                expected_score_impact="high",
            )
        )
    if not inventory["has_readme"] or not inventory["has_install_docs"]:
        improvements.append(
            _improvement(
                category="Documentation and onboarding",
                title="Strengthen README/onboarding guidance for contributors and operators.",
                affected_files=["README.md", *inventory["docs_paths"][:2]],
                rationale="Clear onboarding docs improve both repository readiness and AI-grounded analysis quality.",
                expected_score_impact="medium",
            )
        )
    if not inventory["lint_paths"] and not inventory["type_paths"]:
        improvements.append(
            _improvement(
                category="Code quality and maintainability",
                title="Add linting or typing configuration and document the standard validation path.",
                affected_files=inventory["manifest_paths"][:2],
                rationale="Static quality gates make maintenance expectations explicit.",
                expected_score_impact="medium",
            )
        )
    if not inventory["has_version"] or not inventory["has_changelog"]:
        improvements.append(
            _improvement(
                category="Release and operations readiness",
                title="Add lightweight versioning and changelog discipline.",
                affected_files=["VERSION", "CHANGELOG.md"],
                rationale="Release metadata helps demos graduate into repeatable operations.",
                expected_score_impact="medium",
            )
        )
    if not inventory["has_codeowners"] and not inventory["has_issue_templates"] and not inventory["has_pr_template"]:
        improvements.append(
            _improvement(
                category="GitHub governance",
                title="Add CODEOWNERS and basic issue/PR templates.",
                affected_files=[],
                rationale="Simple governance scaffolding improves accountability and contribution hygiene.",
                expected_score_impact="medium",
            )
        )
    if not inventory["architecture_paths"]:
        improvements.append(
            _improvement(
                category="Architecture and modularity",
                title="Add a short architecture note or module map.",
                affected_files=["README.md", *inventory["docs_paths"][:1]],
                rationale="A small architecture note makes repository intent easier to understand and score accurately.",
                expected_score_impact="low",
            )
        )
    if not inventory["manifest_paths"] and inventory["code_paths"]:
        improvements.append(
            _improvement(
                category="Dependency hygiene",
                title="Make dependency manifests explicit and reproducible.",
                affected_files=[],
                rationale="Machine-readable dependency declarations are a prerequisite for trustworthy upgrade and security work.",
                expected_score_impact="medium",
            )
        )
    if not improvements:
        improvements.append(
            _improvement(
                category="Repository health",
                title="Keep validation, docs, and permissions aligned as the repository grows.",
                affected_files=[],
                rationale="No single dominant improvement surfaced from the current evidence sample.",
                expected_score_impact="low",
            )
        )
    return improvements[:10]


def _improvement(
    *,
    category: str,
    title: str,
    affected_files: list[str],
    rationale: str,
    expected_score_impact: str,
) -> dict[str, Any]:
    return {
        "category": category,
        "title": title.strip(),
        "affected_files": _unique_paths(affected_files)[:4],
        "rationale": rationale.strip(),
        "expected_score_impact": str(expected_score_impact or "medium").strip().lower(),
    }


def _build_roadmap(
    *,
    critical_blockers: list[dict[str, Any]],
    top_improvements: list[dict[str, Any]],
) -> dict[str, list[str]]:
    blockers_lines = [
        _roadmap_line(item["title"], item["category"])
        for item in critical_blockers[:3]
    ]
    improvement_lines = [
        _roadmap_line(item["title"], item["category"])
        for item in top_improvements[:6]
    ]
    thirty = blockers_lines or improvement_lines[:3] or ["No immediate blocker-level action surfaced from the current evidence."]
    sixty = improvement_lines[3:6] or improvement_lines[:2] or ["Stabilize structure, docs, and validation after immediate fixes land."]
    ninety = [
        "Institutionalize governance, release hygiene, and evidence refresh routines.",
    ]
    return {
        "30_days": thirty[:3],
        "60_days": sixty[:3],
        "90_days": ninety[:3],
    }


def _roadmap_line(title: str, category: str) -> str:
    return f"{title} ({category})"


def _build_evidence_summary(*, inventory: dict[str, Any], github_context: dict[str, Any] | None) -> dict[str, Any]:
    key_files = _unique_paths(
        [
            "README.md" if inventory["has_readme"] else "",
            *inventory["workflow_paths"][:2],
            *inventory["manifest_paths"][:2],
            *inventory["test_paths"][:2],
            *inventory["architecture_paths"][:1],
            *inventory["security_paths"][:1],
            *inventory["release_paths"][:2],
        ]
    )
    changed_files = _changed_files(github_context)
    if changed_files:
        key_files = _unique_paths([*changed_files[:2], *key_files])[:8]
    return {
        "evidence_count": len(key_files),
        "key_files": key_files,
        "workflows_considered": inventory["workflow_paths"][:4],
        "docs_considered": inventory["docs_paths"][:4],
        "tests_considered": inventory["test_paths"][:4],
        "manifests_considered": inventory["manifest_paths"][:4],
        "sampled_inventory": bool(inventory["inventory_truncated"]),
    }


def _build_limitations(*, inventory: dict[str, Any], github_context: dict[str, Any] | None) -> list[str]:
    limitations = [
        "Audit is informational and does not certify merge, security, or production readiness.",
        "No runtime execution was performed; the MVP score is based on repository structure and file evidence.",
    ]
    if inventory["inventory_truncated"]:
        limitations.append(
            f"Evidence was sampled from the first {_MAX_TRACKED_FILES} tracked files to keep the audit bounded."
        )
    if not inventory["workflow_paths"]:
        limitations.append("No workflow files were available to assess CI/CD depth.")
    if not inventory["test_paths"]:
        limitations.append("No automated tests were detected from repository structure.")
    changed_files = _changed_files(github_context)
    if github_context and bool(github_context.get("is_pr", False)):
        if changed_files:
            limitations.append(
                f"PR context was used as supplemental evidence only; the audit remains repository-level ({len(changed_files)} changed files)."
            )
        else:
            limitations.append("PR context was detected, but changed-file metadata was not available in the current payload.")
    return limitations[:6]


def _resolve_confidence(*, inventory: dict[str, Any], categories: list[dict[str, Any]]) -> str:
    unknown_count = sum(1 for item in categories if item["label"] == "UNKNOWN")
    evidence_count = len(_unique_paths(
        [
            *inventory["workflow_paths"],
            *inventory["docs_paths"],
            *inventory["manifest_paths"],
            *inventory["test_paths"],
            *inventory["release_paths"],
        ]
    ))
    if inventory["inventory_truncated"] or unknown_count >= 4 or evidence_count < 6:
        return "low"
    if evidence_count >= 15 and unknown_count <= 1 and inventory["workflow_paths"] and inventory["manifest_paths"]:
        return "high"
    return "medium"


def _build_executive_summary(
    *,
    categories: list[dict[str, Any]],
    overall_score: int,
    readiness_band: str,
    query: str,
    github_context: dict[str, Any] | None,
    critical_blockers: list[dict[str, Any]],
) -> str:
    ordered = sorted(categories, key=lambda item: (item["score"] / max(item["max_score"], 1)), reverse=True)
    strongest = ordered[0]["title"] if ordered else "repository structure"
    weakest = ordered[-1]["title"] if ordered else "documentation"
    parts = [
        f"The repository currently scores {overall_score}/100 (`{readiness_band}`), with stronger signals in {strongest} and the largest drag in {weakest}.",
    ]
    if critical_blockers:
        parts.append(f"The most important near-term blocker is {critical_blockers[0]['title'].lower()}.")
    else:
        parts.append("No critical blocker was confirmed from the sampled evidence.")
    changed_files = _changed_files(github_context)
    if github_context and bool(github_context.get("is_pr", False)) and changed_files:
        parts.append(f"Current PR context contributed {len(changed_files)} changed files as supplemental evidence.")
    return " ".join(parts)


def _build_pr_context(github_context: dict[str, Any] | None) -> dict[str, Any]:
    changed_files = _changed_files(github_context)
    if not github_context:
        return {
            "is_pr": False,
            "pr_number": None,
            "changed_files_count": 0,
            "changed_files_sample": [],
        }
    return {
        "is_pr": bool(github_context.get("is_pr", False)),
        "pr_number": github_context.get("pr_number"),
        "changed_files_count": len(changed_files),
        "changed_files_sample": changed_files[:5],
    }


def _changed_files(github_context: dict[str, Any] | None) -> list[str]:
    if not isinstance(github_context, dict):
        return []
    raw = github_context.get("changed_files", [])
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _unique_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for raw in paths:
        path = str(raw or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        output.append(path)
    return output
