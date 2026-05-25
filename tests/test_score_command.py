from __future__ import annotations

import sys
import types
from pathlib import Path

from repobrain.audit_scoring import CATEGORY_SPECS
from repobrain.commands import parse_command
from repobrain.github_flow import _build_score_markdown


def _make_repo(root: Path) -> None:
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / "LICENSE").write_text("custom", encoding="utf-8")
    (root / "VERSION").write_text("0.1.0", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("changelog", encoding="utf-8")
    (root / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")
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


def _valid_categories() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for category in CATEGORY_SPECS:
        score = max(1, category.max_score - 1)
        items.append(
            {
                "key": category.key,
                "score": score,
                "max": category.max_score,
                "label": "GOOD" if score < category.max_score else "STRONG",
                "rationale": f"Validated rationale for {category.title}.",
                "evidence_paths": ["README.md"],
            }
        )
    return items


def _fake_topocore_module(*, response: dict[str, object] | None = None) -> types.ModuleType:
    class FakeFacade:
        audit_score_contract_version = "topocore.audit_score.v1"

        def health(self) -> dict[str, object]:
            return {"status": "ok"}

        def decide_external(self, request: object) -> object:
            return types.SimpleNamespace(
                status="ready",
                action="proceed",
                reference_hash="ref-123",
                selected_count=1,
                blocked=False,
                confidence_band="high",
                message_code="READY",
            )

        def run_audit_score_v1(self, request: dict[str, object]) -> dict[str, object]:
            assert request["constraints"]["no_mutation"] is True
            return dict(response or {})

    class EngineQuery:
        def __init__(self, *, text: str, signature: list[int] | None = None) -> None:
            self.text = text
            self.signature = signature

    class EngineCandidate:
        def __init__(self, **kwargs: object) -> None:
            self.payload = kwargs

    class EngineRequest:
        def __init__(self, **kwargs: object) -> None:
            self.payload = kwargs

    class ExternalDecisionView:
        pass

    module = types.ModuleType("topocore_v6")
    module.__version__ = "0.0.fake"
    module.create_topocore = lambda: FakeFacade()
    module.EngineQuery = EngineQuery
    module.EngineCandidate = EngineCandidate
    module.EngineRequest = EngineRequest
    module.ExternalDecisionView = ExternalDecisionView
    return module


def _valid_response() -> dict[str, object]:
    return {
        "contract_version": "topocore.audit_score.v1",
        "status": "ok",
        "overall_score": 86,
        "readiness_band": "STRONG",
        "category_scores": _valid_categories(),
        "score_adjustments": [
            {
                "category": "documentation",
                "delta": 2,
                "reason": "Stronger docs coverage detected.",
                "evidence_paths": ["README.md"],
            }
        ],
        "critical_blockers": [],
        "top_improvements": [
            {
                "title": "Broaden test coverage",
                "category": "Testing and validation",
                "rationale": "More tests would improve confidence.",
                "expected_score_impact": "medium",
                "affected_files": ["tests/test_demo.py"],
            }
        ],
        "roadmap": {
            "30_days": ["Broaden test coverage"],
            "60_days": ["Expand release notes"],
            "90_days": ["Deepen governance automation"],
        },
        "confidence": "high",
        "limitations": ["Informational only."],
        "safety": {
            "patch_authorized": False,
            "patch_applied": False,
            "files_modified": False,
            "branch_created": False,
            "commit_created": False,
            "pr_created": False,
            "no_security_approval": True,
            "no_merge_approval": True,
        },
        "diagnostics": {
            "backend_mode": "audit_v6_enriched",
            "capability_version": "topocore.audit_score.v1",
            "sanitized_warnings": [],
        },
    }


def test_parse_score_commands() -> None:
    assert parse_command("/repobrain score") == {"cmd": "score", "query": ""}
    assert parse_command("/repobrain score Focus on partner-demo readiness.") == {
        "cmd": "score",
        "query": "Focus on partner-demo readiness.",
    }


def test_issue_score_is_supported_and_compact(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    audit: dict[str, object] = {}

    markdown = _build_score_markdown(
        repo_root=tmp_path,
        query="",
        tky_mode="local",
        github_context_seed={"repository": "owner/repo"},
        audit=audit,
    )

    assert "# RepoBrain Repository Score" in markdown
    assert "## Score card" in markdown
    assert "## Category snapshot" in markdown
    assert "Use `/repobrain audit` for the full evidence report." in markdown
    assert audit["route_final"] == "SCORE"
    assert audit["command"] == "score"
    assert audit["patch_applied"] is False


def test_pr_score_is_supported(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    audit: dict[str, object] = {}

    markdown = _build_score_markdown(
        repo_root=tmp_path,
        query="Focus on this PR in repository-readiness context.",
        tky_mode="local",
        github_context_seed={
            "repository": "owner/repo",
            "is_pr": True,
            "pr_number": 17,
            "changed_files": ["docs/readme.md"],
            "files": [{"filename": "docs/readme.md", "status": "modified"}],
        },
        audit=audit,
    )

    assert "Requested focus: Focus on this PR in repository-readiness context." in markdown
    assert audit["scope_status"] == "repository_score_summary_with_pr_context"


def test_score_uses_v6_enriched_mode_when_valid_capability_exists(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    sys.modules["topocore_v6"] = _fake_topocore_module(response=_valid_response())
    audit: dict[str, object] = {}

    markdown = _build_score_markdown(
        repo_root=tmp_path,
        query="",
        tky_mode="local",
        github_context_seed={"repository": "owner/repo"},
        audit=audit,
    )

    sys.modules.pop("topocore_v6", None)
    assert "Audit mode: `v6-enriched scoring`" in markdown
    assert "Static baseline:" in markdown
    assert audit["resolved_backend"] == "v6"
    assert audit["backend_mode"] == "audit_v6_enriched_score_summary"
    assert audit["fallback_reason"] == "none"


def test_score_keeps_static_fallback_when_capability_is_unavailable(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    sys.modules.pop("topocore_v6", None)
    audit: dict[str, object] = {}

    markdown = _build_score_markdown(
        repo_root=tmp_path,
        query="",
        tky_mode="local",
        github_context_seed={"repository": "owner/repo"},
        audit=audit,
    )

    assert "static scoring with v6 contract-ready guard" in markdown
    assert audit["resolved_backend"] == "not_applicable"
    assert audit["fallback_reason"] == "audit_v6_capability_unavailable_static_scoring"


def test_score_rejects_invalid_v6_response_safely(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    invalid = _valid_response()
    invalid["overall_score"] = 101
    sys.modules["topocore_v6"] = _fake_topocore_module(response=invalid)
    audit: dict[str, object] = {}

    markdown = _build_score_markdown(
        repo_root=tmp_path,
        query="",
        tky_mode="local",
        github_context_seed={"repository": "owner/repo"},
        audit=audit,
    )

    sys.modules.pop("topocore_v6", None)
    assert "rejected v6 response" in markdown.lower()
    assert audit["resolved_backend"] == "v6_rejected"
    assert audit["fallback_reason"] == "audit_v6_contract_rejected_static_scoring"
