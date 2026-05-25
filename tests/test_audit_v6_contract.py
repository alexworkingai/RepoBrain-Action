from __future__ import annotations

from pathlib import Path

from repobrain.audit_contract import AUDIT_V6_CONTRACT_VERSION, build_audit_score_request_v1
from repobrain.audit_scoring import CATEGORY_SPECS, score_repository_audit


def _make_repo(root: Path) -> None:
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / "LICENSE").write_text("custom", encoding="utf-8")
    (root / "VERSION").write_text("0.1.0", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("changelog", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        "[tool.ruff]\nline-length = 100\n[tool.mypy]\npython_version = '3.12'\n",
        encoding="utf-8",
    )
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_demo.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "name: ci\non:\n  push:\npermissions:\n  contents: read\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs" / "security.md").write_text("security posture", encoding="utf-8")
    (root / ".topocore-v6").mkdir()
    (root / ".topocore-v6" / "secret.py").write_text("hidden", encoding="utf-8")
    (root / "artifacts").mkdir()
    (root / "artifacts" / "ignored.txt").write_text("ignore", encoding="utf-8")


def test_builds_valid_audit_score_request_v1(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    report = score_repository_audit(
        repo_root=tmp_path,
        query="Focus on D:\\ARIADNA_Minsk demo readiness with ghp_secret_value",
        github_context={
            "repository": "owner/repo",
            "event_name": "issue_comment",
            "is_pr": True,
            "pr_number": 12,
            "changed_files": ["README.md", ".topocore-v6/secret.py"],
        },
    )

    request = build_audit_score_request_v1(
        repo_root=tmp_path,
        report=report,
        github_context={
            "repository": "owner/repo",
            "event_name": "issue_comment",
            "is_pr": True,
            "pr_number": 12,
            "changed_files": ["README.md", ".topocore-v6/secret.py"],
        },
        query="Focus on D:\\ARIADNA_Minsk demo readiness with ghp_secret_value",
    )

    assert request["contract_version"] == AUDIT_V6_CONTRACT_VERSION
    assert request["repo_metadata"]["owner"] == "owner"
    assert request["repo_metadata"]["repo"] == "repo"
    assert request["constraints"]["no_mutation"] is True
    assert request["constraints"]["no_patch"] is True
    assert request["constraints"]["no_branch_commit_pr"] is True
    assert len(request["static_baseline"]["category_scores"]) == len(CATEGORY_SPECS)
    assert sum(item["max"] for item in request["static_baseline"]["category_scores"]) == 100
    assert "[redacted-path]" in request["audit_focus"]["query"]
    assert "ghp_" not in request["audit_focus"]["query"]
    assert len(request["evidence_manifest"]) <= 16
    evidence_paths = [item["path"] for item in request["evidence_manifest"]]
    assert ".topocore-v6/secret.py" not in evidence_paths
    assert "artifacts/ignored.txt" not in evidence_paths
    assert all(".topocore-v6" not in path for path in evidence_paths)

