from __future__ import annotations

from pathlib import Path

from repobrain.audit_scoring import category_weight_total, score_repository_audit


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RANK_ORDER = (
    "mature_repo_fixture",
    "read_mostly_workflow_repo",
    "ci_but_no_tests_repo",
    "docs_only_repo",
    "risky_permissions_repo",
    "sparse_repo",
)


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _build_sparse_repo(root: Path) -> None:
    _write(root, "main.py", "print('hello')\n")


def _build_docs_only_repo(root: Path) -> None:
    _write(root, "README.md", "# Demo\n")
    _write(root, "docs/architecture.md", "Architecture overview.\n")
    _write(root, "docs/onboarding.md", "Setup guide.\n")
    _write(root, "docs/troubleshooting.md", "Troubleshooting notes.\n")
    _write(root, "pyproject.toml", "[project]\nname='demo'\n[tool.ruff]\nline-length = 100\n")
    _write(root, "LICENSE", "custom\n")
    _write(root, "src/main.py", "def main() -> int:\n    return 1\n")


def _build_ci_but_no_tests_repo(root: Path) -> None:
    _build_docs_only_repo(root)
    _write(
        root,
        ".github/workflows/ci.yml",
        "name: ci\non: [push]\npermissions:\n  contents: read\n  models: read\n  issues: write\n  pull-requests: read\n  checks: read\n  statuses: read\n  actions: read\njobs:\n  qa:\n    runs-on: ubuntu-latest\n    steps:\n      - run: python -V\n",
    )


def _build_read_mostly_workflow_repo(root: Path) -> None:
    _build_ci_but_no_tests_repo(root)
    _write(root, "tests/test_demo.py", "def test_ok() -> None:\n    assert True\n")


def _build_risky_permissions_repo(root: Path) -> None:
    _write(root, "README.md", "# Risky Demo\n")
    _write(root, "docs/troubleshooting.md", "Runtime drift note.\n")
    _write(root, "pyproject.toml", "[project]\nname='risky'\n[tool.ruff]\nline-length = 100\n")
    _write(root, "src/main.py", "def main() -> int:\n    return 2\n")
    _write(
        root,
        ".github/workflows/ci.yml",
        "name: ci\non:\n  pull_request_target:\npermissions:\n  contents: write\n  models: read\n  issues: write\n  pull-requests: write\n  checks: write\n  statuses: read\n  actions: read\njobs:\n  qa:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo risky\n",
    )


def _build_mature_repo_fixture(root: Path) -> None:
    _build_read_mostly_workflow_repo(root)
    _write(root, "VERSION", "0.1.0\n")
    _write(root, "CHANGELOG.md", "# Changelog\n")
    _write(root, "action.yml", "name: Demo Action\n")
    _write(root, ".github/CODEOWNERS", "* @team\n")
    _write(root, ".github/ISSUE_TEMPLATE/bug.yml", "name: bug\n")
    _write(root, ".github/pull_request_template.md", "## Summary\n")
    _write(root, "docs/security/policy.md", "Security posture.\n")
    _write(root, "docs/release/process.md", "Release process.\n")
    _write(root, "uv.lock", "# lock\n")


def _build_private_checkout_boundary_repo(root: Path) -> None:
    _build_mature_repo_fixture(root)
    _write(root, ".topocore-v6/private/runtime.py", "SECRET = 'private'\n")
    _write(root, "artifacts/generated.md", "# generated\n")
    _write(root, "reports/score.md", "# report\n")
    _write(root, ".pytest_cache/state.txt", "cache\n")
    _write(root, ".codex-skill-install-tmp/tmp.md", "# tmp\n")
    _write(root, "node_modules/demo/index.js", "console.log('x')\n")
    _write(root, "dist/bundle.js", "console.log('bundle')\n")
    _write(root, "build/output.txt", "generated\n")


def _fixture_report(tmp_path: Path, name: str) -> dict[str, object]:
    root = tmp_path / name
    root.mkdir(parents=True, exist_ok=True)
    builders = {
        "sparse_repo": _build_sparse_repo,
        "docs_only_repo": _build_docs_only_repo,
        "ci_but_no_tests_repo": _build_ci_but_no_tests_repo,
        "read_mostly_workflow_repo": _build_read_mostly_workflow_repo,
        "risky_permissions_repo": _build_risky_permissions_repo,
        "mature_repo_fixture": _build_mature_repo_fixture,
        "private_checkout_boundary_repo": _build_private_checkout_boundary_repo,
    }
    builders[name](root)
    return score_repository_audit(repo_root=root)


def test_benchmark_expected_rank_order_is_documented() -> None:
    assert EXPECTED_RANK_ORDER == (
        "mature_repo_fixture",
        "read_mostly_workflow_repo",
        "ci_but_no_tests_repo",
        "docs_only_repo",
        "risky_permissions_repo",
        "sparse_repo",
    )


def test_benchmark_fixtures_rank_credibly_and_stably(tmp_path: Path) -> None:
    fixture_names = list(EXPECTED_RANK_ORDER) + ["private_checkout_boundary_repo"]
    first_pass = {name: _fixture_report(tmp_path / "pass1", name) for name in fixture_names}
    second_pass = {name: _fixture_report(tmp_path / "pass2", name) for name in fixture_names}

    assert category_weight_total() == 100

    for name in fixture_names:
        assert 0 <= int(first_pass[name]["overall_score"]) <= 100
        assert 0 <= int(second_pass[name]["overall_score"]) <= 100
        assert int(first_pass[name]["overall_score"]) == int(second_pass[name]["overall_score"])
        first_categories = {item["key"]: int(item["score"]) for item in first_pass[name]["categories"]}
        second_categories = {item["key"]: int(item["score"]) for item in second_pass[name]["categories"]}
        assert first_categories == second_categories

    observed = sorted(
        ((name, int(first_pass[name]["overall_score"])) for name in EXPECTED_RANK_ORDER),
        key=lambda item: item[1],
        reverse=True,
    )
    assert [name for name, _ in observed] == list(EXPECTED_RANK_ORDER)


def test_benchmark_penalties_and_positive_signals_apply_as_expected(tmp_path: Path) -> None:
    mature = _fixture_report(tmp_path, "mature_repo_fixture")
    sparse = _fixture_report(tmp_path, "sparse_repo")
    docs_only = _fixture_report(tmp_path, "docs_only_repo")
    ci_no_tests = _fixture_report(tmp_path, "ci_but_no_tests_repo")
    read_mostly = _fixture_report(tmp_path, "read_mostly_workflow_repo")
    risky = _fixture_report(tmp_path, "risky_permissions_repo")

    def category(report: dict[str, object], key: str) -> dict[str, object]:
        return next(item for item in report["categories"] if item["key"] == key)

    assert int(mature["overall_score"]) > int(sparse["overall_score"])
    assert int(mature["overall_score"]) > int(docs_only["overall_score"])
    assert int(read_mostly["overall_score"]) > int(risky["overall_score"])
    assert int(ci_no_tests["overall_score"]) < int(read_mostly["overall_score"])

    assert int(category(ci_no_tests, "testing")["score"]) < int(category(read_mostly, "testing")["score"])
    assert int(category(docs_only, "documentation")["score"]) == 8
    assert int(category(docs_only, "release_ops")["score"]) < int(category(mature, "release_ops")["score"])
    assert int(category(risky, "security")["score"]) < int(category(read_mostly, "security")["score"])
    assert int(category(risky, "governance")["score"]) < int(category(read_mostly, "governance")["score"])
    assert int(category(read_mostly, "security")["score"]) >= 8

    assert str(docs_only["readiness_band"]) != "STRONG"
    assert str(sparse["confidence"]) == "low"
    assert "No workflow files were available" in "\n".join(str(item) for item in sparse["limitations"])


def test_boundary_fixture_excludes_private_checkout_and_generated_surfaces(tmp_path: Path) -> None:
    report = _fixture_report(tmp_path, "private_checkout_boundary_repo")
    mature = _fixture_report(tmp_path, "mature_repo_fixture")

    evidence_paths: list[str] = []
    for item in report["categories"]:
        evidence_paths.extend(str(path) for path in item.get("evidence_paths", []))
    evidence_paths.extend(str(path) for path in report["evidence_summary"]["key_files"])

    for fragment in (
        ".topocore-v6/",
        "artifacts/",
        "reports/",
        ".pytest_cache/",
        ".codex-skill-install-tmp/",
        "node_modules/",
        "dist/",
        "build/",
    ):
        assert all(fragment not in path for path in evidence_paths)

    assert int(report["overall_score"]) == int(mature["overall_score"])


def test_benchmark_report_mentions_limitations() -> None:
    report_text = (ROOT / "docs/release/AUDIT_BENCHMARK_REPORT.md").read_text(encoding="utf-8").lower()

    assert "limitations" in report_text
    assert "not formal certification" in report_text
    assert "mature_repo_fixture" in report_text
    assert "sparse_repo" in report_text
