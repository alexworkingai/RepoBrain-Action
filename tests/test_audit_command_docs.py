from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_command_guide_documents_audit_as_supported() -> None:
    text = _read("docs/commands/REPOBRAIN_COMMANDS.md")

    assert "/repobrain audit" in text
    assert "repository-level" in text.lower()
    assert "100-point" in text.lower()


def test_scoring_model_doc_records_audit_mvp_implementation_status() -> None:
    text = _read("docs/release/REPOBRAIN_V6_SCORING_MODEL.md")

    assert "Sprint 78 implements the `/repobrain audit` MVP." in text
    assert "Implementation status" in text
    assert "/repobrain score" in text
    assert "/repobrain doctor" in text
    assert "/repobrain status" in text


def test_release_notes_mention_audit_mvp() -> None:
    text = _read("docs/release/RELEASE_NOTES_RC1.md")

    assert "/repobrain audit" in text
    assert "100-point" in text.lower()
    assert "no patch/autofix" in text.lower()


def test_sprint_78_architecture_note_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_78_AUDIT_MVP_100_POINT_SCORING.md").exists()


def test_test_coverage_index_links_audit_tests() -> None:
    text = _read("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md")

    assert "tests/test_audit_command_scoring.py" in text
    assert "tests/test_audit_command_github_flow.py" in text
    assert "tests/test_audit_command_docs.py" in text
