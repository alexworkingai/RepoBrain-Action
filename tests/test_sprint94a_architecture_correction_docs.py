from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_sprint94a_architecture_doc_exists_and_sets_github_native_direction() -> None:
    architecture = _read("docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md")

    assert "correction summary" in architecture
    assert "github-native beta control plane" in architecture
    assert "github app installation token" in architecture
    assert "private repobrain control repository worker" in architecture
    assert "`hosted_api` is experimental and future external-runtime mode" in architecture
    assert "topocore remains a separate team and system" in architecture
    assert "repobrain does not implement topocore internals" in architecture
    assert "sprint_94a_github_native_beta_architecture_correction_ready" in architecture


def test_readme_and_onboarding_do_not_present_fake_hosted_setup_as_default_beta() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    assert "`hosted_api` mode requires a real external runtime and is not the default github-native beta path" in readme
    assert "trusted and developer beta are expected to use github app installation identity plus a private control worker" in readme
    assert "github marketplace is not the immediate route" in readme
    assert "trusted partners should wait for github app and control-worker beta instructions from sprints 94b-94e" in quickstart
    assert "trusted beta partners must not be told to create fake `repobrain_hosted_api_url` values" in quickstart
    assert "do not create fake hosted endpoint values for partner onboarding" in install
    assert "this flow is being implemented in sprints 94b-94e" in install


def test_topocore_boundary_and_historical_93e_truth_are_corrected() -> None:
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    runbook = _read("docs/release/SPRINT_93E_TRUSTED_PARTNER_VALIDATION_RUNBOOK.md")
    evidence = _read("docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md")

    assert "repobrain does not implement topocore internals" in quickstart
    assert "redirect future trusted beta validation to sprint 94e github-native control-plane validation" in runbook
    assert "phase_1_trusted_partner_self_service_ready_not_claimed" in runbook
    assert "final hosted phase1 pass claimed" not in runbook
    assert "final_hosted_phase1_pass_claimed" in evidence
