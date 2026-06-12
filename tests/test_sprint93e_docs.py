from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_sprint93e_runbook_and_evidence_mark_hosted_validation_historical() -> None:
    runbook = _read("docs/release/SPRINT_93E_TRUSTED_PARTNER_VALIDATION_RUNBOOK.md")
    evidence = _read("docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md")

    assert "alexworkingai/elen-mcp-v.2.2.0" in runbook
    assert "alexworkingai/repobrain-community" in runbook
    assert "hosted_api_runtime_gap_identified" in runbook
    assert "github_native_architecture_correction_required" in runbook
    assert "phase_1_trusted_partner_self_service_ready_not_claimed" in runbook
    assert "do not treat `repobrain_hosted_api_url` as the default trusted beta requirement" in runbook
    assert "future trusted beta validation to sprint 94e github-native control-plane validation" in runbook

    assert "hosted_api_runtime_gap_identified" in evidence
    assert "github_native_architecture_correction_required" in evidence
    assert "final_hosted_phase1_pass_claimed" in evidence
    assert "next validation target: sprint 94e github-native control-plane beta validation" in evidence


def test_sprint93e_readme_and_onboarding_reference_historical_artifacts_without_overclaim() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    assert "sprint 93e historical runbook" in readme
    assert "sprint 93e historical evidence template" in readme
    assert "sprint 94a reclassifies the hosted path as experimental and future-facing" in readme

    assert "historical sprint 93e note" in quickstart
    assert "superseded by sprint 94a architecture correction" in quickstart
    assert "marketplace ready" in quickstart
    assert "public launch ready" in quickstart

    assert "experimental hosted mode" in install
    assert "do not treat `repobrain_hosted_api_url` as a required current beta setup step" in install
    assert "wait for sprint 94b-94e github-native workflow instructions for the default beta path" in install


def test_sprint93e_architecture_note_and_alias_preserve_hardening_history_with_correction_notice() -> None:
    architecture = _read("docs/architecture/SPRINT_93E_FINAL_HARDENING_AND_TRUSTED_VALIDATION.md")
    alias = _read("docs/architecture/SPRINT_93D_END_TO_END_SELF_SERVICE_WORKFLOW.md")

    assert "correction notice" in architecture
    assert "`hosted_api` path was reclassified as experimental and future external-runtime mode" in architecture
    assert "hosted client rejects unexpected redirect responses" in architecture
    assert "future trusted beta validation is redirected to sprint 94e on the github-native control-plane architecture" in architecture
    assert "correction notice" in alias
