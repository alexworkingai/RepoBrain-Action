from __future__ import annotations

from pathlib import Path

from repobrain.audit_scoring import category_weight_total, score_repository_audit
from repobrain.github_flow import _build_audit_markdown


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _build_repo(root: Path) -> None:
    _write(root, "README.md", "# Demo\n")
    _write(root, "pyproject.toml", "[project]\nname='demo'\n[tool.ruff]\nline-length = 100\n")
    _write(root, "repobrain/app.py", "def run() -> int:\n    return 1\n")
    _write(root, "tests/test_app.py", "def test_ok():\n    assert True\n")
    _write(
        root,
        ".github/workflows/repobrain.yml",
        "name: repobrain\non:\n  issue_comment:\npermissions:\n  contents: read\n  issues: write\n  pull-requests: read\n  checks: read\n  statuses: read\n  actions: read\njobs:\n  qa:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest -q\n",
    )
    _write(root, "VERSION", "0.1.0\n")
    _write(root, "CHANGELOG.md", "# Changelog\n")
    _write(root, "LICENSE", "custom\n")


def test_category_weights_still_total_100() -> None:
    assert category_weight_total() == 100


def test_private_and_generated_directories_are_excluded_from_scoring_and_evidence(tmp_path: Path) -> None:
    _build_repo(tmp_path)
    _write(tmp_path, ".topocore-v6/docs/SECRET.md", "# private\n")
    _write(tmp_path, "artifacts/generated.md", "# generated\n")
    _write(tmp_path, "reports/report.md", "# generated\n")
    _write(tmp_path, ".codex-skill-install-tmp/tmp.md", "# generated\n")
    _write(tmp_path, "node_modules/demo/index.js", "console.log('x')\n")
    _write(tmp_path, "dist/bundle.js", "console.log('bundle')\n")
    _write(tmp_path, "build/out.txt", "generated\n")
    _write(tmp_path, ".pytest_cache/step.txt", "cache\n")

    report = score_repository_audit(repo_root=tmp_path)
    markdown = _build_audit_markdown(
        repo_root=tmp_path,
        query="Focus on diagnostics.",
        tky_mode="local",
        github_context_seed={},
        audit={},
    )

    evidence_paths: list[str] = []
    for item in report["categories"]:
        assert isinstance(item, dict)
        evidence_paths.extend(str(path) for path in item.get("evidence_paths", []))
    evidence_paths.extend(str(path) for path in report["evidence_summary"]["key_files"])

    forbidden_fragments = (
        ".topocore-v6/",
        "artifacts/",
        "reports/",
        ".codex-skill-install-tmp/",
        "node_modules/",
        "dist/",
        "build/",
        ".pytest_cache/",
    )
    for fragment in forbidden_fragments:
        assert all(fragment not in path for path in evidence_paths)
        assert fragment not in markdown


def test_read_mostly_workflow_avoids_dangerous_permission_penalty(tmp_path: Path) -> None:
    _build_repo(tmp_path)
    report = score_repository_audit(repo_root=tmp_path)

    security = next(item for item in report["categories"] if item["title"] == "Security posture")
    governance = next(item for item in report["categories"] if item["title"] == "GitHub governance")

    assert int(security["score"]) >= 8
    assert int(governance["score"]) >= 2


def test_audit_output_is_not_duplicative_and_keeps_static_limitations(tmp_path: Path) -> None:
    _build_repo(tmp_path)
    markdown = _build_audit_markdown(
        repo_root=tmp_path,
        query="Focus on repository quality.",
        tky_mode="local",
        github_context_seed={},
        audit={},
    )

    assert markdown.count("Requested focus:") == 1
    assert markdown.count("Overall score:") == 1
    assert markdown.count("Runtime and safety") >= 1
    assert "Not a merge/security/production approval." in markdown
