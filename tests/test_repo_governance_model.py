from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_repo_governance_model_and_script_exist() -> None:
    assert (ROOT / "docs/security/REPO_GOVERNANCE_MODEL.md").exists()
    assert (ROOT / "scripts/check_repo_governance.py").exists()


def test_governance_model_documents_unknown_on_api_limitation() -> None:
    text = _read("docs/security/REPO_GOVERNANCE_MODEL.md").lower()

    assert "codeowners" in text
    assert "branch protection" in text
    assert "ruleset" in text
    assert "403" in text
    assert "unknown" in text
    assert "not `pass`" in text or "not pass" in text


def test_governance_script_preserves_non_mutating_unknown_semantics() -> None:
    text = _read("scripts/check_repo_governance.py")

    assert "GOVERNANCE_STATUS=" in text
    assert "UNKNOWN" in text
    assert "BRANCH_PROTECTION=" in text
    assert "RULESETS=" in text
    assert "CODEOWNERS=" in text
    assert "'gh'" in text
    assert "'api'" in text
