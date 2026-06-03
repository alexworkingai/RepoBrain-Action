from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_governance_docs_record_pr119_merge_and_dependency_review_truth() -> None:
    governance = _read("docs/security/REPO_GOVERNANCE_MODEL.md").lower()
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()
    partner = _read("docs/release/PARTNER_TESTING_READINESS.md").lower()
    sprint = _read("docs/architecture/SPRINT_92E_CONSUMER_REPO_ASK_UX_FINAL_FIX.md").lower()

    combined = "\n".join((governance, readiness, partner, sprint))
    assert "pr #119" in combined
    assert "dependency graph enabled" in combined
    assert "dependency review passed" in combined
    assert "solo-owner" in combined
    assert "required checks" in combined
    assert "deferred" in combined
