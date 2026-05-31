from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint87_architecture_doc_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_87_INSTALLED_PACKAGE_RUNTIME_PROOF.md").exists()


def test_public_readiness_docs_reflect_runtime_proof_state() -> None:
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md")
    approval = _read("docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md")
    report = _read("docs/release/ENTERPRISE_P0_HARDENING_REPORT.md")

    combined = "\n".join((readiness, approval, report)).lower()
    assert (
        "public_switch_ready_after_runtime_proof" in combined
        or "public_blocked_by_runtime_proof" in combined
        or "public_blocked_by_package_delivery" in combined
        or "public_blocked_by_token_scope" in combined
        or "public_blocked_by_artifact_security" in combined
        or "public_blocked_by_validation" in combined
    )
    assert "marketplace" in combined
    assert "public switch" in combined
