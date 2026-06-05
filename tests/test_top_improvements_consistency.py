from __future__ import annotations

from repobrain.audit_scoring import _build_roadmap, _build_top_improvements


def test_maxed_dependency_hygiene_is_not_rendered_as_generic_improvement() -> None:
    inventory = {
        "test_paths": [],
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


def test_maxed_categories_are_excluded_from_normal_improvement_targets() -> None:
    inventory = {
        "test_paths": [],
        "workflow_paths": [".github/workflows/ci.yml"],
        "workflow_permission_classification": "safe_read_mostly",
        "dangerous_permissions": [],
        "has_readme": True,
        "has_install_docs": True,
        "lint_paths": ["pyproject.toml"],
        "type_paths": ["pyproject.toml"],
        "has_version": False,
        "has_changelog": False,
        "has_codeowners": False,
        "has_issue_templates": False,
        "has_pr_template": False,
        "architecture_paths": ["docs/architecture/ARCH.md"],
        "manifest_paths": ["pyproject.toml"],
        "code_paths": ["repobrain/github_flow.py"],
        "docs_paths": ["README.md"],
    }
    categories = [
        {"title": "AI-readiness / repository intelligence", "score": 7, "max_score": 7},
        {"title": "Dependency hygiene", "score": 8, "max_score": 8},
        {"title": "Documentation and onboarding", "score": 8, "max_score": 8},
        {"title": "Security posture", "score": 12, "max_score": 12},
        {"title": "Architecture and modularity", "score": 15, "max_score": 15},
        {"title": "Code quality and maintainability", "score": 12, "max_score": 12},
        {"title": "GitHub governance", "score": 3, "max_score": 8},
        {"title": "Testing and validation", "score": 8, "max_score": 12},
        {"title": "Release and operations readiness", "score": 5, "max_score": 8},
        {"title": "CI/CD and automation", "score": 8, "max_score": 10},
    ]

    improvements = _build_top_improvements(inventory=inventory, categories=categories)
    joined = " | ".join(str(item.get("title", "")) for item in improvements).lower()
    categories_present = {str(item.get("category", "")) for item in improvements}

    assert "dependency hygiene" not in joined
    assert "ai-readiness" not in joined
    assert "documentation and onboarding" not in joined
    assert "security posture" not in joined
    assert "architecture and modularity" not in joined
    assert "code quality and maintainability" not in joined
    assert "GitHub governance" in categories_present
    assert "Testing and validation" in categories_present
    assert "Release and operations readiness" in categories_present


def test_roadmap_prioritizes_non_maxed_categories() -> None:
    categories = [
        {"title": "AI-readiness / repository intelligence", "score": 7, "max_score": 7},
        {"title": "Dependency hygiene", "score": 8, "max_score": 8},
        {"title": "GitHub governance", "score": 3, "max_score": 8},
        {"title": "Testing and validation", "score": 8, "max_score": 12},
        {"title": "Release and operations readiness", "score": 4, "max_score": 8},
        {"title": "CI/CD and automation", "score": 8, "max_score": 10},
    ]
    top_improvements = [
        {"category": "AI-readiness / repository intelligence", "title": "Improve AI-readiness coverage", "expected_score_impact": "low"},
        {"category": "Dependency hygiene", "title": "Improve dependency hygiene", "expected_score_impact": "medium"},
        {"category": "GitHub governance", "title": "Improve GitHub governance controls and documentation", "expected_score_impact": "high"},
        {"category": "Testing and validation", "title": "Raise testing and validation confidence", "expected_score_impact": "high"},
        {"category": "Release and operations readiness", "title": "Raise release and operations readiness confidence", "expected_score_impact": "high"},
        {"category": "CI/CD and automation", "title": "Strengthen CI/CD validation coverage", "expected_score_impact": "medium"},
    ]

    roadmap = _build_roadmap(
        critical_blockers=[],
        top_improvements=top_improvements,
        categories=categories,
    )
    combined = " | ".join([*roadmap["30_days"], *roadmap["60_days"], *roadmap["90_days"]]).lower()

    assert "github governance" in combined
    assert "testing and validation" in combined
    assert "release and operations readiness" in combined
    assert "ci/cd" in combined
    assert "ai-readiness" not in combined
    assert "dependency hygiene" not in combined
