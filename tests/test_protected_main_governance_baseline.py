from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_governance_docs_record_protected_main_baseline_and_deferred_checks() -> None:
    governance = _read("docs/security/REPO_GOVERNANCE_MODEL.md")
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md")

    assert "PROTECTED_MAIN_BASELINE_ENABLED" in governance
    assert "required checks" in governance.lower()
    assert "deferred" in governance.lower()
    assert "protected main" in readiness.lower()
