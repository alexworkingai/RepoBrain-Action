from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_topocore_v6_audit_contract_doc_exists_and_states_private_boundary() -> None:
    text = _read("docs/architecture/TOPOCORE_V6_AUDIT_SCORING_CONTRACT.md")

    assert "topocore.audit_score.v1" in text
    assert "TopoCore v6 source remains private" in text
    assert "private_checkout" in text
    assert "no patch or autofix" in text.lower()
    assert "no public topocore distribution is implemented" in text.lower()


def test_sprint_81_architecture_note_exists_and_records_contract_ready_truth() -> None:
    text = _read("docs/architecture/SPRINT_81_DEEP_V6_AUDIT_SCORING_CONTRACT.md")

    assert "Sprint 81 defines and implements the safe v6 audit scoring contract" in text
    assert "topocore.audit_score.v1" in text
    assert "V6_AUDIT_CONTRACT_READY_STATIC_RUNTIME" in text
    assert "NOT_TESTED_LIVE" in text or "REAL_V6_AUDIT_CAPABILITY_NOT_AVAILABLE" in text


def test_release_and_demo_docs_reflect_static_vs_v6_contract_truth() -> None:
    scoring = _read("docs/release/REPOBRAIN_V6_SCORING_MODEL.md")
    benchmark = _read("docs/release/AUDIT_BENCHMARK_REPORT.md")
    demo = _read("docs/release/MICROSOFT_GITHUB_DEMO_REPORT.md")
    combined = "\n".join((scoring, benchmark, demo))

    assert "topocore.audit_score.v1" in combined
    assert "run_audit_score_v1" in combined
    assert "does not claim `v6` enrichment unless" in combined
    assert "TopoCore v6 remains private" in combined
    assert "no patch/autofix" in combined.lower()


def test_contract_docs_do_not_claim_live_v6_without_evidence_or_unsafe_approval() -> None:
    combined = "\n".join(
        [
            _read("docs/architecture/TOPOCORE_V6_AUDIT_SCORING_CONTRACT.md"),
            _read("docs/architecture/SPRINT_81_DEEP_V6_AUDIT_SCORING_CONTRACT.md"),
            _read("docs/release/MICROSOFT_GITHUB_DEMO_REPORT.md"),
        ]
    ).lower()

    assert "safe-to-merge approval" not in combined
    assert "not a security approval" in combined or "no security approval" in combined
    assert "does not claim microsoft approval" in combined
    assert "official partnership" in combined or "no microsoft partnership claim" in combined


def test_test_coverage_index_links_sprint_81_contract_tests() -> None:
    text = _read("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md")

    assert "tests/test_audit_v6_contract.py" in text
    assert "tests/test_audit_v6_contract_guard.py" in text
    assert "tests/test_audit_v6_backend_integration.py" in text
    assert "tests/test_audit_v6_contract_docs.py" in text
