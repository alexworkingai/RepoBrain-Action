from __future__ import annotations

import re

TODO_MARKERS = ("TODO", "FIXME")

GITHUB_TOKEN_RE = re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")
AWS_ACCESS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
KEY_VALUE_SECRET_RE = re.compile(
    r'''(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['"]?.{8,}'''
)
ENV_SECRET_LINE_RE = re.compile(
    r"""(?im)^(?:export\s+)?(api[_-]?key|secret|token|password)\s*=\s*.+$"""
)
SECURITY_WORDING_RE = re.compile(r"(?i)\b(secret|secrets|token|password|api[_-]?key)\b")


def _normalize_path(file_item: dict[str, object]) -> str:
    return str(file_item.get("filename", "")).strip()


def _file_link(path: str, repo: str | None, head_sha: str | None) -> str | None:
    if not repo or not head_sha:
        return None
    return f"https://github.com/{repo}/blob/{head_sha}/{path}"


def _is_docs_only(paths: list[str]) -> bool:
    if not paths:
        return False
    doc_ext = (".md", ".rst", ".txt")
    return all(path.lower().endswith(doc_ext) for path in paths)


def _scan_patch_for_signals(patch: str) -> tuple[list[str], list[str], int, bool]:
    risks: list[str] = []
    notes: list[str] = []
    risk_score = 0
    high_found = False
    upper_patch = patch.upper()

    has_conflict_markers = "<<<<<<<" in patch or "=======" in patch or ">>>>>>>" in patch
    if has_conflict_markers:
        risks.append("Merge conflict markers present")
        risk_score += 4
        high_found = True

    strong_secret_signal = (
        "BEGIN PRIVATE KEY" in upper_patch
        or "BEGIN RSA PRIVATE KEY" in upper_patch
        or bool(GITHUB_TOKEN_RE.search(patch))
        or bool(AWS_ACCESS_KEY_RE.search(patch))
        or bool(KEY_VALUE_SECRET_RE.search(patch))
        or bool(ENV_SECRET_LINE_RE.search(patch))
    )
    if strong_secret_signal:
        risks.append("Possible secret leakage in patch")
        risk_score += 4
        high_found = True
    elif SECURITY_WORDING_RE.search(patch):
        notes.append("Contains security-related wording in docs; verify no real secrets are included.")

    if any(marker in upper_patch for marker in TODO_MARKERS):
        notes.append("Patch contains TODO/FIXME markers")
        risk_score += 1

    if "NOQA" in upper_patch or "# TYPE: IGNORE" in upper_patch:
        notes.append("Patch disables checks in changed code")
        risk_score += 1

    return risks, notes, risk_score, high_found


def _risk_level(risk_score: int, has_high_signal: bool) -> str:
    if has_high_signal or risk_score >= 5:
        return "high"
    if risk_score >= 2:
        return "medium"
    return "low"


def build_pr_review(
    files: list[dict[str, object]],
    *,
    head_sha: str | None = None,
    repo: str | None = None,
) -> dict[str, object]:
    """Build a PR review summary with file links and patch-based risk heuristics."""
    file_count = len(files)
    total_additions = sum(int(item.get("additions", 0) or 0) for item in files)
    total_deletions = sum(int(item.get("deletions", 0) or 0) for item in files)

    files_changed: list[dict[str, object]] = []
    paths: list[str] = []
    risks: list[str] = []
    notes: list[str] = []
    risk_score = 0
    high_signal = False

    for item in files:
        path = _normalize_path(item)
        if not path:
            continue
        paths.append(path)
        status = str(item.get("status", "modified"))
        add = int(item.get("additions", 0) or 0)
        delete = int(item.get("deletions", 0) or 0)
        link = _file_link(path, repo, head_sha)
        files_changed.append(
            {
                "path": path,
                "status": status,
                "add": add,
                "del": delete,
                "link": link,
            }
        )

        path_lower = path.lower()
        if path_lower.startswith(".github/workflows/"):
            risks.append("CI/CD changed: verify workflows")
            risk_score += 2
        if path_lower == "pyproject.toml" or path_lower.startswith("requirements"):
            risks.append("Dependencies changed: verify install and tests")
            risk_score += 2
        if any(token in path_lower for token in ("auth", "security", "crypto")):
            risks.append("Security-sensitive area changed")
            risk_score += 2
        if path_lower.startswith("tests/"):
            notes.append("Tests updated: check that coverage remains meaningful")
        if path_lower.startswith("scripts/"):
            notes.append("Automation scripts changed")

        patch = item.get("patch")
        if isinstance(patch, str) and patch:
            patch_risks, patch_notes, patch_score, patch_high = _scan_patch_for_signals(patch)
            risks.extend(patch_risks)
            notes.extend(patch_notes)
            risk_score += patch_score
            high_signal = high_signal or patch_high

    risks = list(dict.fromkeys(risks))
    notes = list(dict.fromkeys(notes))

    risk_level = _risk_level(risk_score, high_signal)

    suggested_tests: list[str] = []
    has_python = any(path.lower().endswith(".py") for path in paths)
    workflows_changed = any(path.lower().startswith(".github/workflows/") for path in paths)
    security_changed = any(any(token in path.lower() for token in ("auth", "security", "crypto")) for path in paths)
    has_conflict_markers = any("Merge conflict markers present" in item for item in risks)

    if has_conflict_markers:
        suggested_tests.append("Resolve merge conflict markers and re-run /repobrain review")

    if _is_docs_only(paths):
        suggested_tests.append("No tests required (optional).")
    else:
        if has_python:
            suggested_tests.append("Run ruff check .")
            suggested_tests.append("Run pytest -q")
        if workflows_changed:
            suggested_tests.append("Run /repobrain verify")
            suggested_tests.append("Check Actions logs for workflow changes")
        if security_changed:
            suggested_tests.append("Perform manual security review for changed auth/security paths")

    if not risks:
        risks = ["No obvious high-risk patterns detected"]
    if not suggested_tests:
        suggested_tests = ["Run standard CI checks before merge"]

    summary_text = (
        f"{file_count} files changed, +{total_additions}/-{total_deletions} lines. "
        f"Estimated risk: {risk_level.upper()}."
    )

    files_block: list[str] = []
    for item in files_changed:
        path = str(item["path"])
        status = str(item["status"])
        add = int(item["add"])
        delete = int(item["del"])
        link = item.get("link")
        if isinstance(link, str) and link:
            files_block.append(f"- [`{path}`]({link}) ({status}, +{add}/-{delete})")
        else:
            files_block.append(f"- `{path}` ({status}, +{add}/-{delete})")

    return {
        "summary_text": summary_text,
        "files_changed": files_changed,
        "files_block": files_block,
        "risks": risks,
        "risk_level": risk_level,
        "suggested_tests": suggested_tests,
        "notes": notes,
        # Backward-compatible aliases for existing callers/tests.
        "next_steps": suggested_tests,
        "audit_summary": {
            "route": "REVIEW",
            "files": file_count,
            "risk_level": risk_level,
        },
    }
