from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").lower()


def test_94d_docs_and_template_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md").exists()
    assert (ROOT / "docs/examples/repobrain_control_repo_queue_worker.yml").exists()
    assert (ROOT / "docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md").exists()


def test_94d_docs_keep_marketplace_and_hosted_api_truth_explicit() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    worker_doc = _read("docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md")

    assert "marketplace is not the immediate route" in readme
    assert "marketplace is not the immediate route" in quickstart
    assert "marketplace is not the current onboarding route" in install
    assert "hosted_api remains experimental/future" not in worker_doc
    assert "hosted_api" in readme
    assert "experimental and future external-runtime mode" in quickstart
    assert "do not require a domain, tunnel, or external hosted api" in quickstart
    assert "do not require domain registration, tunnels, or external hosting subscriptions" in install
    assert "does not claim" in worker_doc


def test_94d_docs_state_live_trusted_partner_validation_is_still_94e() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    architecture_94c = _read("docs/architecture/SPRINT_94C_GITHUB_NATIVE_REQUEST_QUEUE.md")
    architecture_94d = _read("docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md")
    queue_contract = _read("docs/contracts/GITHUB_NATIVE_REQUEST_QUEUE_V1.md")

    assert "trusted partner beta is not ready until sprint 94e validation" in readme
    assert "trusted partner beta is not ready until sprint 94e validation" in quickstart
    assert "trusted partner beta is not ready until sprint 94e validation" in install
    assert "94e = live trusted partner validation" in architecture_94c
    assert "sprint 94e performs trusted partner beta validation" in architecture_94d
    assert "94e performs live trusted partner validation" in queue_contract


def test_94d_docs_keep_partner_secret_and_topocore_boundary_rules_explicit() -> None:
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    control = _read("docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md")
    worker_doc = _read("docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md")

    assert "do not add a topocore token" in quickstart
    assert "do not add a github app private key" in quickstart
    assert "partner repos must not store the github app private key" in install
    assert "partner repos must not store topocore tokens for the github-native beta path" in install
    assert "configure topocore entrypoint only in the private control repo" in control
    assert "the private repobrain control repo is the runtime location for the sprint 94d worker foundation" in control
    assert "topocore is a separate team and system" in worker_doc
    assert "repobrain does not implement topocore internals" in worker_doc


def test_94d_docs_keep_commands_stable_and_queue_worker_private() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    template = _read("docs/examples/repobrain_control_repo_queue_worker.yml")

    assert "/repobrain score" in readme
    assert "/repobrain audit" in readme
    assert "/repobrain audit --profile premium" in quickstart
    assert "/repobrain audit --profile premium" in install
    assert "worker runs only in the owner-controlled private repobrain control repo" in _read(
        "docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md"
    )
    assert "this public repobrain-action repo does not contain topocore internals" in template
    assert "do not use hosted_api" in template
    assert "marketplace" in template
