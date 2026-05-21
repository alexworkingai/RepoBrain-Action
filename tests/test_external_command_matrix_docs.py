from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_70_doc_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_70_EXTERNAL_COMMAND_MATRIX_ELEN_MCP.md").exists()


def test_sprint_70_doc_records_external_matrix_and_v6_truth() -> None:
    text = _read("docs/architecture/SPRINT_70_EXTERNAL_COMMAND_MATRIX_ELEN_MCP.md").lower()

    assert "elen-mcp" in text
    assert "external command matrix" in text
    assert "resolved backend" in text
    assert "resolved `v6`" in text or "resolved backend: `v6`" in text or "resolved backend | `v6`" in text
    assert "no `v5`" in text
    assert "no `repobrain-community`" in text
    assert "no patch/autofix" in text
    assert "external_command_matrix_passed" in text


def test_indexes_link_sprint_70() -> None:
    migration = _read("docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md").lower()
    coverage = _read("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md").lower()

    assert "sprint_70_external_command_matrix_elen_mcp.md" in migration
    assert "sprint 70" in coverage
    assert "external command matrix" in coverage
