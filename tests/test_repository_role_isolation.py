from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.github_flow import _maybe_refine_operational_ask_answer


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_consumer_repo_ask_does_not_describe_action_repo_modules(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write(tmp_path / ".github" / "workflows" / "repobrain.yml", "name: RepoBrain\n")
    _write(tmp_path / "src" / "mcpServer.ts", "export const server = true;\n")
    _write(tmp_path / "README.md", "# Target Product\n")

    control_plane_root = tmp_path / "control"
    _write(control_plane_root / "pyproject.toml", "[project]\nname='repobrain-control'\n")
    _write(
        control_plane_root / "docs" / "release" / "PUBLIC_READINESS_ASSESSMENT.md",
        "- current public readiness decision: `SPRINT_92F_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING`\n",
    )
    _write(control_plane_root / "docs" / "release" / "INSTALLED_PACKAGE_LIVE_PROOF.md", "- `INSTALLED_PACKAGE_LIVE_PROOF_PASSED`\n")
    _write(control_plane_root / "docs" / "security" / "REPO_GOVERNANCE_MODEL.md", "- `PROTECTED_MAIN_BASELINE_ENABLED`\n")
    monkeypatch.setenv("GITHUB_ACTION_PATH", str(control_plane_root))

    answer_text, _, _ = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question="Analyze this repository as an MCP product.",
        answer_text="placeholder",
        next_steps="placeholder",
        audit_summary={"route_final": "FAST", "llm_used": False},
        github_context={"repository": "owner/consumer-repo"},
    )

    assert "RepoBrain-Action currently" not in answer_text
    assert "repobrain/" not in answer_text.lower()
    assert "target repository" in answer_text.lower() or "target-repo" in answer_text.lower()
