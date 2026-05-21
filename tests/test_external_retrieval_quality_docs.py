from pathlib import Path


def test_sprint_71_doc_exists_and_records_external_quality_results() -> None:
    text = Path("docs/architecture/SPRINT_71_EXTERNAL_RETRIEVAL_EVIDENCE_QUALITY.md").read_text(
        encoding="utf-8"
    )

    assert "Issue Quality Results" in text
    assert "PR Quality Results" in text
    assert "EXTERNAL_RETRIEVAL_QUALITY_PASSED" in text
    assert "`auto` / `v6`" in text
    assert "no `v5`" in text
    assert "no `repobrain-community`" in text
    assert "no patch/autofix" in text


def test_sprint_71_doc_records_workflow_evidence_fix() -> None:
    text = Path("docs/architecture/SPRINT_71_EXTERNAL_RETRIEVAL_EVIDENCE_QUALITY.md").read_text(
        encoding="utf-8"
    )

    assert ".github/workflows/repobrain.yml" in text
    assert "workflow files are now part of the default retrieval scan" in Path(
        "docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md"
    ).read_text(encoding="utf-8")


def test_indexes_link_sprint_71_quality_doc() -> None:
    migration = Path("docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md").read_text(
        encoding="utf-8"
    )
    coverage = Path("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md").read_text(
        encoding="utf-8"
    )

    assert "SPRINT_71_EXTERNAL_RETRIEVAL_EVIDENCE_QUALITY.md" in migration
    assert "tests/test_external_retrieval_quality_docs.py" in coverage
