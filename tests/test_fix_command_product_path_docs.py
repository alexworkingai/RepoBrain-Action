from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sprint_73_doc_exists_and_records_fix_statuses() -> None:
    path = ROOT / "docs" / "architecture" / "SPRINT_73_FIX_COMMAND_PRODUCT_PATH.md"
    text = path.read_text(encoding="utf-8")

    assert "Sprint 73 productizes `/repobrain fix`" in text
    for status in (
        "PROPOSAL_READY",
        "NO_ACTION_NEEDED",
        "NEEDS_MORE_INFORMATION",
        "UNSUPPORTED_SCOPE",
        "BLOCKED_BY_SAFETY",
        "ERROR_SANITIZED",
    ):
        assert status in text


def test_sprint_73_doc_records_no_patch_and_no_mutation_guarantee() -> None:
    text = (ROOT / "docs" / "architecture" / "SPRINT_73_FIX_COMMAND_PRODUCT_PATH.md").read_text(
        encoding="utf-8"
    )

    assert "patch_authorized=false" in text
    assert "patch_applied=false" in text
    assert "files_modified=false" in text
    assert "branch_created=false" in text
    assert "commit_created=false" in text
    assert "pr_created=false" in text
    assert "no v5" in text.lower()
    assert "repobrain-community" in text


def test_indexes_link_sprint_73_fix_product_path() -> None:
    migration = (ROOT / "docs" / "architecture" / "TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md").read_text(
        encoding="utf-8"
    )
    coverage = (ROOT / "docs" / "architecture" / "TOPOCORE_V6_TEST_COVERAGE_INDEX.md").read_text(
        encoding="utf-8"
    )

    assert "SPRINT_73_FIX_COMMAND_PRODUCT_PATH.md" in migration
    assert "tests/test_fix_command_product_path.py" in coverage
