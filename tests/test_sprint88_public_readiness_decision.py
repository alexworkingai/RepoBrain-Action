from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _public_readiness_next_step, _read_public_readiness_status


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint88_architecture_doc_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_88_ARTIFACT_ACCESS_FINAL_RUNTIME_PROOF.md").exists()


def test_sprint88_public_readiness_docs_reflect_owner_action_gate() -> None:
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()
    approval = _read("docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md").lower()
    hardening = _read("docs/release/ENTERPRISE_P0_HARDENING_REPORT.md").lower()
    runbook = _read("docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md").lower()

    combined = "\n".join((readiness, approval, hardening, runbook))
    assert "owner_action_required_token_issuance" in combined
    assert "topocore_v6_artifact_token" in combined
    assert "marketplace" in combined
    assert "public switch" in combined


def test_operational_readiness_parser_handles_owner_action_status() -> None:
    status = _read_public_readiness_status(ROOT)

    assert status == "OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE"
    next_step = _public_readiness_next_step(status)
    assert "minimum-scope artifact credential" in next_step.lower()
