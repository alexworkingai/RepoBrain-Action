from __future__ import annotations

from pathlib import Path
import shutil

from repobrain.audit_scoring import CATEGORY_SPECS, category_weight_total, score_repository_audit


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _category(report: dict[str, object], title: str) -> dict[str, object]:
    categories = report.get("categories", [])
    assert isinstance(categories, list)
    for item in categories:
        assert isinstance(item, dict)
        if item.get("title") == title:
            return item
    raise AssertionError(f"Missing category {title}")


def _build_sparse_repo(root: Path) -> None:
    _write(root, "main.py", "print('hello')\n")


def _build_strong_repo(root: Path) -> None:
    _write(
        root,
        "README.md",
        "# Demo repo\n\nRepository with docs, tests, CI, and release metadata.\n",
    )
    _write(
        root,
        "pyproject.toml",
        "[project]\nname='demo'\nversion='0.1.0'\n[tool.ruff]\nline-length = 100\n",
    )
    _write(root, "mypy.ini", "[mypy]\npython_version = 3.11\n")
    _write(root, ".editorconfig", "root = true\n[*]\ncharset = utf-8\n")
    _write(root, "src/demo/app.py", "def run() -> int:\n    return 1\n")
    _write(root, "tests/test_app.py", "from demo.app import run\n\ndef test_run():\n    assert run() == 1\n")
    _write(
        root,
        ".github/workflows/ci.yml",
        "name: ci\non:\n  push:\n  pull_request:\npermissions:\n  contents: read\n  checks: read\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest -q\n      - run: ruff check .\n",
    )
    _write(root, ".github/CODEOWNERS", "* @team\n")
    _write(root, ".github/ISSUE_TEMPLATE/bug.md", "---\nname: Bug\n")
    _write(root, ".github/pull_request_template.md", "## Summary\n")
    _write(root, "docs/architecture/OVERVIEW.md", "# Architecture\n")
    _write(root, "docs/onboarding/SETUP.md", "# Setup\n")
    _write(root, "VERSION", "0.1.0\n")
    _write(root, "CHANGELOG.md", "# Changelog\n")
    _write(root, "LICENSE", "custom license\n")


def test_category_weights_sum_to_100() -> None:
    assert category_weight_total() == 100
    assert sum(item.max_score for item in CATEGORY_SPECS) == 100


def test_overall_score_is_bounded_between_0_and_100(tmp_path: Path) -> None:
    _build_sparse_repo(tmp_path)
    report = score_repository_audit(repo_root=tmp_path)

    assert 0 <= int(report["overall_score"]) <= 100


def test_category_scores_are_bounded_by_each_maximum(tmp_path: Path) -> None:
    _build_strong_repo(tmp_path)
    report = score_repository_audit(repo_root=tmp_path)

    categories = report["categories"]
    assert isinstance(categories, list)
    for item in categories:
        assert isinstance(item, dict)
        assert 0 <= int(item["score"]) <= int(item["max_score"])


def test_missing_evidence_lowers_confidence_without_hallucinating(tmp_path: Path) -> None:
    _build_sparse_repo(tmp_path)
    report = score_repository_audit(repo_root=tmp_path)

    categories = report["categories"]
    assert isinstance(categories, list)
    assert any(isinstance(item, dict) and item.get("label") == "UNKNOWN" for item in categories)
    assert report["confidence"] in {"low", "medium"}
    assert "No runtime execution was performed" in "\n".join(report["limitations"])


def test_strong_fixture_scores_higher_than_sparse_fixture(tmp_path: Path) -> None:
    sparse = tmp_path / "sparse"
    strong = tmp_path / "strong"
    sparse.mkdir()
    strong.mkdir()
    _build_sparse_repo(sparse)
    _build_strong_repo(strong)

    sparse_report = score_repository_audit(repo_root=sparse)
    strong_report = score_repository_audit(repo_root=strong)

    assert int(strong_report["overall_score"]) > int(sparse_report["overall_score"])


def test_dangerous_workflow_permissions_lower_security_and_governance_scores(tmp_path: Path) -> None:
    safe_repo = tmp_path / "safe"
    unsafe_repo = tmp_path / "unsafe"
    safe_repo.mkdir()
    unsafe_repo.mkdir()
    _build_strong_repo(safe_repo)
    _build_strong_repo(unsafe_repo)
    _write(
        unsafe_repo,
        ".github/workflows/ci.yml",
        "name: ci\non:\n  pull_request_target:\npermissions:\n  contents: write\n  checks: write\n  pull-requests: write\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest -q\n",
    )

    safe_report = score_repository_audit(repo_root=safe_repo)
    unsafe_report = score_repository_audit(repo_root=unsafe_repo)

    assert int(_category(unsafe_report, "Security posture")["score"]) < int(
        _category(safe_report, "Security posture")["score"]
    )
    assert int(_category(unsafe_report, "GitHub governance")["score"]) <= int(
        _category(safe_report, "GitHub governance")["score"]
    )


def test_missing_tests_lowers_testing_score(tmp_path: Path) -> None:
    _build_strong_repo(tmp_path)
    shutil.rmtree(tmp_path / "tests")

    report = score_repository_audit(repo_root=tmp_path)

    assert int(_category(report, "Testing and validation")["score"]) < 8


def test_missing_docs_lowers_documentation_score(tmp_path: Path) -> None:
    _build_sparse_repo(tmp_path)
    report = score_repository_audit(repo_root=tmp_path)

    assert int(_category(report, "Documentation and onboarding")["score"]) <= 2


def test_release_files_improve_release_readiness_score(tmp_path: Path) -> None:
    base = tmp_path / "base"
    improved = tmp_path / "improved"
    base.mkdir()
    improved.mkdir()
    _build_sparse_repo(base)
    _build_sparse_repo(improved)
    _write(improved, "VERSION", "0.1.0\n")
    _write(improved, "CHANGELOG.md", "# Changelog\n")
    _write(improved, "LICENSE", "custom\n")

    base_report = score_repository_audit(repo_root=base)
    improved_report = score_repository_audit(repo_root=improved)

    assert int(_category(improved_report, "Release and operations readiness")["score"]) > int(
        _category(base_report, "Release and operations readiness")["score"]
    )


def test_report_includes_confidence_and_limitations(tmp_path: Path) -> None:
    _build_strong_repo(tmp_path)
    report = score_repository_audit(repo_root=tmp_path, query="Focus on demo readiness.")

    assert report["confidence"] in {"high", "medium", "low"}
    limitations = report["limitations"]
    assert isinstance(limitations, list)
    assert limitations
    assert report["executive_summary"]


def test_hidden_private_checkout_directory_is_not_scored_as_consumer_repo_evidence(tmp_path: Path) -> None:
    _build_sparse_repo(tmp_path)
    _write(tmp_path, ".topocore-v6/docs/SECRET_ARCHITECTURE.md", "# private\n")
    _write(tmp_path, ".topocore-v6/pyproject.toml", "[project]\nname='private'\n")

    report = score_repository_audit(repo_root=tmp_path)

    combined_paths = []
    for item in report["categories"]:
        assert isinstance(item, dict)
        combined_paths.extend(item.get("evidence_paths", []))
    combined_paths.extend(report["evidence_summary"]["key_files"])

    assert all(".topocore-v6/" not in str(path) for path in combined_paths)
