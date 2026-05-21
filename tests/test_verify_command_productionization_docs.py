from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sprint_72_doc_exists_and_records_verify_semantics() -> None:
    path = ROOT / "docs" / "architecture" / "SPRINT_72_VERIFY_COMMAND_PRODUCTIONIZATION.md"
    text = path.read_text(encoding="utf-8")

    assert path.exists()
    assert "PASS" in text
    assert "WARN" in text
    assert "FAIL" in text
    assert "PENDING" in text
    assert "NOT_RUN" in text
    assert "UNKNOWN" in text


def test_sprint_72_doc_records_external_live_results_and_safety() -> None:
    text = (
        ROOT / "docs" / "architecture" / "SPRINT_72_VERIFY_COMMAND_PRODUCTIONIZATION.md"
    ).read_text(encoding="utf-8")

    assert "Elen-MCP-v.2.2.0" in text
    assert "verify_report_only" in text
    assert "no patch/autofix" in text
    assert "no repobrain-community" in text
    assert "no v5" in text


def test_sprint_72_indexes_link_verify_productionization() -> None:
    migration_text = (
        ROOT / "docs" / "architecture" / "TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md"
    ).read_text(encoding="utf-8")
    coverage_text = (
        ROOT / "docs" / "architecture" / "TOPOCORE_V6_TEST_COVERAGE_INDEX.md"
    ).read_text(encoding="utf-8")

    assert "SPRINT_72_VERIFY_COMMAND_PRODUCTIONIZATION.md" in migration_text
    assert "tests/test_verify_command_productionization.py" in coverage_text
