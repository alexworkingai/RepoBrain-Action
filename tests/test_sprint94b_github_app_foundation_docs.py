from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_sprint94b_foundation_docs_and_templates_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_94B_GITHUB_APP_INSTALLATION_FOUNDATION.md").exists()
    assert (ROOT / "docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md").exists()
    assert (ROOT / "docs/examples/repobrain_control_repo_github_app_auth_check.yml").exists()
    assert (ROOT / "docs/contracts/GITHUB_APP_INSTALLATION_IDENTITY_V1.md").exists()


def test_sprint94b_architecture_doc_sets_github_app_identity_without_marketplace() -> None:
    architecture = _read("docs/architecture/SPRINT_94B_GITHUB_APP_INSTALLATION_FOUNDATION.md")

    assert "github app installation identity" in architecture
    assert "not github marketplace" in architecture
    assert "not billing" in architecture
    assert "not external hosted api deployment" in architecture
    assert "github app gives installation identity" in architecture
    assert "github app avoids owner-generated partner tokens" in architecture
    assert "webhooks are disabled or deferred in 94b" in architecture
    assert "no custom domain" in architecture
    assert "no paid or free-tier hosting" in architecture
    assert "no hosted api endpoint" in architecture
    assert "no tunnel" in architecture
    assert "sprint_94b_github_app_installation_foundation_ready" in architecture


def test_control_repo_setup_and_contract_keep_private_key_and_tokens_private() -> None:
    control = _read("docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md")
    contract = _read("docs/contracts/GITHUB_APP_INSTALLATION_IDENTITY_V1.md")

    assert "repobrain_github_app_private_key" in control
    assert "repobrain_github_app_id" in control
    assert "must not store" in control
    assert "partner personal access tokens" in control
    assert "owner-generated onboarding tokens" in control
    assert "never print the token" in control
    assert "never persist the token to artifacts" in control

    assert "repobrain.github_app_installation_identity.v1" in contract
    assert "do not expose private key" in contract
    assert "do not expose installation token" in contract
    assert "do not expose raw jwt" in contract
    assert "do not expose authorization header" in contract


def test_readme_onboarding_and_examples_keep_hosted_mode_experimental_and_partner_surface_clean() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    workflow = _read("docs/examples/repobrain_partner_self_service_workflow.yml")
    auth_check = _read("docs/examples/repobrain_control_repo_github_app_auth_check.yml")

    assert "sprint 94b adds the github app installation foundation" in readme
    assert "trusted partner beta is not ready until sprint 94e validation" in readme
    assert "`hosted_api` mode requires a real external runtime" in readme
    assert "github marketplace is not the immediate route" in readme

    assert "github app is the intended beta identity layer" in quickstart
    assert "it is not marketplace billing" in quickstart
    assert "the github app private key belongs only in the private control repo" in quickstart
    assert "trusted beta partners must not be told to create fake `repobrain_hosted_api_url` values" in quickstart

    assert "partner repos must not provide topocore token for the default github-native beta path" in install
    assert "partner repos must not provide owner token for the default github-native beta path" in install
    assert "partner repos must not store the github app private key" in install
    assert "do not install from marketplace for this stage" in install

    assert "api_url: https://repobrain.example.invalid" in workflow
    assert "do not use the hosted path as the default trusted beta setup" in workflow
    assert "github app provides installation identity and scoped repo access" in workflow
    assert "this planned path is being implemented in sprints 94c-94e" in workflow

    assert "workflow_dispatch" in auth_check
    assert "repobrain_github_app_private_key" in auth_check
    assert "do not print tokens" in auth_check


def test_94b_docs_preserve_command_surface_and_topocore_boundary_without_overclaim() -> None:
    architecture = _read("docs/architecture/SPRINT_94B_GITHUB_APP_INSTALLATION_FOUNDATION.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    for text in (architecture, quickstart, install):
        assert "/repobrain score" in text
        assert "/repobrain audit" in text
        assert "/repobrain audit --profile premium" in text
        assert "topocore is a separate team and system" in text or "topocore remains a separate team and system" in text
        assert "repobrain does not implement topocore internals" in text

    assert "trusted partner beta is not ready until sprint 94e validation" in quickstart
    assert "trusted partner beta is not ready until sprint 94e validation" in install
