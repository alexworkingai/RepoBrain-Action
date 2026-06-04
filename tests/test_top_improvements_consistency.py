from __future__ import annotations

from repobrain.audit_scoring import _build_top_improvements


def test_maxed_dependency_hygiene_is_not_rendered_as_generic_improvement() -> None:
    inventory = {
        "test_paths": ["tests/test_sample.py"],
        "workflow_paths": [".github/workflows/ci.yml"],
        "workflow_permission_classification": "safe_read_mostly",
        "dangerous_permissions": [],
        "has_readme": True,
        "has_install_docs": True,
        "lint_paths": ["pyproject.toml"],
        "type_paths": [],
        "has_version": False,
        "has_changelog": False,
        "has_codeowners": False,
        "has_issue_templates": False,
        "has_pr_template": False,
        "architecture_paths": ["docs/architecture/ARCH.md"],
        "manifest_paths": [],
        "code_paths": ["repobrain/github_flow.py"],
        "docs_paths": ["README.md"],
    }
    categories = [
        {"title": "Dependency hygiene", "score": 8, "max_score": 8},
        {"title": "GitHub governance", "score": 3, "max_score": 8},
        {"title": "Release and operations readiness", "score": 4, "max_score": 8},
    ]

    improvements = _build_top_improvements(inventory=inventory, categories=categories)
    titles = " | ".join(str(item.get("title", "")) for item in improvements)

    assert "Make dependency manifests explicit and reproducible." not in titles
    assert any(str(item.get("category", "")) == "GitHub governance" for item in improvements)

