from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_sprint93e_runbook_and_evidence_capture_pending_truth_and_both_repos() -> None:
    runbook = _read("docs/release/SPRINT_93E_TRUSTED_PARTNER_VALIDATION_RUNBOOK.md")
    evidence = _read("docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md")

    assert "alexworkingai/elen-mcp-v.2.2.0" in runbook
    assert "alexworkingai/repobrain-community" in runbook
    assert "/repobrain audit --profile premium" in runbook
    assert "ensure only one workflow responds during validation" in runbook
    assert "sprint_93e_hardening_ready_live_validation_pending" in runbook
    assert "repobrain-93e-self-service-validation" in runbook
    assert "repobrain-93e-community-self-service-validation" in runbook
    assert "repobrain_hosted_api_url" in runbook
    assert "mcp_issue_pass" in evidence
    assert "community_pr_pass" in evidence
    assert "no_duplicate_responder_pass" in evidence
    assert "sprint_93e_hardening_ready_live_validation_pending" in evidence


def test_sprint93e_readme_and_onboarding_reference_validation_artifacts_without_overclaim() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    assert "trusted-partner validation runbook" in readme
    assert "validation evidence template" in readme
    assert "sprint_93e_hardening_ready_live_validation_pending" in readme

    assert "final trusted-partner live validation still remains pending" in quickstart
    assert "docs/release/sprint_93e_trusted_partner_validation_runbook.md" in quickstart
    assert "docs/repobrain_93e_community_self_service_smoke.md" in quickstart
    assert "marketplace readiness" in quickstart
    assert "final trusted-partner pass without live issue and pr validation" in quickstart

    assert "trusted partner self-service path" in install
    assert "do not request or paste a repobrain owner-generated token" in install
    assert "do not install or download topocore in the partner repository" in install
    assert "runtime-dependent external pilot path" in install
    assert "if you are validating the sprint 93e thin-client self-service path" in install


def test_sprint93e_architecture_and_community_smoke_docs_exist_and_preserve_phase_truth() -> None:
    architecture = _read("docs/architecture/SPRINT_93E_FINAL_HARDENING_AND_TRUSTED_VALIDATION.md")
    smoke = _read("docs/repobrain_93e_community_self_service_smoke.md")
    alias = _read("docs/architecture/SPRINT_93D_END_TO_END_SELF_SERVICE_WORKFLOW.md")

    assert "sprint_93e_hardening_ready_live_validation_pending" in architecture
    assert "hosted client rejects unexpected redirect responses" in architecture
    assert "repobrain-community" in architecture
    assert "do not claim unrestricted public launch" in architecture
    assert "issue commands" in smoke
    assert "no duplicate responders" in smoke
    assert "/repobrain audit --profile premium" in smoke
    assert "companion alias" in alias
