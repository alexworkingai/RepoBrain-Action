from __future__ import annotations

from pathlib import Path

from repobrain.audit_scoring import CATEGORY_SPECS
from repobrain.audit_contract import _sanitize_repo_path, _sanitize_text, build_audit_score_request_v1


def _category_payload() -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for category in CATEGORY_SPECS:
        payload.append(
            {
                "key": category.key,
                "score": max(1, category.max_score - 1),
                "label": "GOOD",
                "rationale": f"Rationale for {category.title}",
                "evidence_paths": ["README.md"],
            }
        )
    return payload


def test_safe_repo_relative_paths_are_preserved() -> None:
    examples = [
        "README.md",
        "docs/example.md",
        "tests/test_example.py",
        ".github/workflows/repobrain.yml",
        "src/module.py",
        "repobrain/output_md.py",
    ]

    for path in examples:
        assert _sanitize_repo_path(path) == path
        assert _sanitize_text(f"Evidence: {path}") == f"Evidence: {path}"


def test_windows_and_posix_absolute_paths_are_redacted() -> None:
    assert _sanitize_repo_path(r"D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action\repobrain\output_md.py") == ""
    assert "[redacted-path]" in _sanitize_text(r"See D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action\repobrain\output_md.py")
    assert _sanitize_repo_path("/home/user/project/src/module.py") == ""
    assert "[redacted-path]" in _sanitize_text("See /home/user/project/src/module.py")


def test_private_checkout_tokens_and_tracebacks_are_redacted() -> None:
    assert _sanitize_repo_path(".topocore-v6/src/private.py") == ""
    assert "[redacted-path]" in _sanitize_text("Evidence .topocore-v6/src/private.py")
    assert "ghp_abc123" not in _sanitize_text("token ghp_abc123")
    traceback_line = 'File "C:/Users/example/private.py", line 1, in boom'
    sanitized = _sanitize_text(traceback_line)
    assert "C:/Users/example/private.py" not in sanitized
    assert "[redacted-path]" in sanitized


def test_generated_and_private_dirs_are_excluded_from_request_evidence(tmp_path: Path) -> None:
    report = {
        "overall_score": 60,
        "readiness_band": "NEEDS_ATTENTION",
        "confidence": "medium",
        "limitations": [],
        "categories": _category_payload(),
        "evidence_summary": {
            "key_files": [
                "README.md",
                ".topocore-v6/src/private.py",
                "artifacts/diag.json",
                "reports/output.md",
                "build/tmp.js",
                "src/module.py",
            ],
            "workflows_considered": [".github/workflows/repobrain.yml"],
            "docs_considered": ["docs/guide.md"],
            "tests_considered": ["tests/test_demo.py"],
            "manifests_considered": ["pyproject.toml"],
        },
        "critical_blockers": [],
        "top_improvements": [],
    }

    request = build_audit_score_request_v1(
        repo_root=tmp_path,
        report=report,
        github_context={"repository": "owner/repo"},
        query="focus",
    )

    paths = [item["path"] for item in request["evidence_manifest"]]
    assert "README.md" in paths
    assert "src/module.py" in paths
    assert ".github/workflows/repobrain.yml" in paths
    assert ".topocore-v6/src/private.py" not in paths
    assert "artifacts/diag.json" not in paths
    assert "reports/output.md" not in paths
    assert "build/tmp.js" not in paths
