from __future__ import annotations


def _normalize_path(file_item: dict[str, object]) -> str:
    return str(file_item.get("filename", "")).strip()


def _risk_flags(files: list[dict[str, object]]) -> list[str]:
    risks: list[str] = []
    lowered_paths = [_normalize_path(item).lower() for item in files]

    if any(path.startswith(".github/workflows/") for path in lowered_paths):
        risks.append("CI/CD changed: verify workflows")
    if any(path == "pyproject.toml" or path.startswith("requirements") for path in lowered_paths):
        risks.append("Dependencies changed: verify install & tests")
    if any(
        any(token in path for token in ("auth", "security", "crypto")) for path in lowered_paths
    ):
        risks.append("Security-sensitive area changed")
    if any(path.startswith("tests/") for path in lowered_paths):
        risks.append("Tests updated: ensure coverage")
    if any(path.startswith("scripts/") for path in lowered_paths):
        risks.append("Automation scripts changed")

    return risks or ["No obvious high-risk patterns detected"]


def build_pr_review(files: list[dict[str, object]]) -> dict[str, object]:
    """Build a lightweight PR review summary from GitHub PR files API items."""
    file_count = len(files)
    total_additions = sum(int(item.get("additions", 0) or 0) for item in files)
    total_deletions = sum(int(item.get("deletions", 0) or 0) for item in files)

    files_block = [
        (
            f"- `{_normalize_path(item)}` "
            f"({item.get('status', 'modified')}, +{int(item.get('additions', 0) or 0)}"
            f"/-{int(item.get('deletions', 0) or 0)})"
        )
        for item in files
    ]

    summary_text = (
        f"{file_count} files changed, +{total_additions}/-{total_deletions} total lines. "
        "Review focuses on changed paths and basic risk heuristics."
    )
    next_steps = [
        "Run `pytest -q`.",
        "Run `ruff check .`.",
        "Open changed files and verify behavior matches intent.",
    ]

    return {
        "summary_text": summary_text,
        "files_block": files_block,
        "risks": _risk_flags(files),
        "next_steps": next_steps,
        "audit_summary": {
            "files": file_count,
            "route": "REVIEW",
        },
    }
