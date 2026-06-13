from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_sprint94c_docs_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_94C_GITHUB_NATIVE_REQUEST_QUEUE.md").exists()
    assert (ROOT / "docs/contracts/GITHUB_NATIVE_REQUEST_QUEUE_V1.md").exists()


def test_readme_and_partner_docs_present_github_app_queue_as_beta_queue_mode() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    workflow = _read("docs/examples/repobrain_partner_self_service_workflow.yml")
    architecture = _read("docs/architecture/SPRINT_94C_GITHUB_NATIVE_REQUEST_QUEUE.md")

    assert "github_app_queue" in readme
    assert "github_app_queue" in quickstart
    assert "github_app_queue" in install
    assert "transport_mode: github_app_queue" in workflow
    assert 'terms_accepted: "true"' in workflow
    assert "queue marker comment" in architecture
    assert "sprint_94c_github_native_request_queue_ready" in architecture


def test_94c_docs_keep_hosted_mode_future_and_require_94d_for_final_reports() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    contract = _read("docs/contracts/GITHUB_NATIVE_REQUEST_QUEUE_V1.md")

    assert "hosted_api" in readme
    assert "experimental and future external-runtime mode" in quickstart
    assert "do not require domain registration, tunnels, or external hosting subscriptions" in install
    assert "final score and audit reports require the private control worker in sprint 94d" in readme
    assert "final score and audit reports require the private control worker in sprint 94d" in install
    assert "receive final reports only after the sprint 94d private control worker exists" in quickstart
    assert "94d may later update or add" in contract


def test_94c_docs_do_not_claim_trusted_beta_ready_and_preserve_topocore_boundary() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    control = _read("docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md")

    for text in (readme, quickstart, install):
        assert "trusted partner beta is not ready until sprint 94e validation" in text
        assert "topocore is a separate team and system" in text or "topocore remains a separate team and system" in text
        assert "repobrain does not implement topocore internals" in text
    assert "sprint 94c adds the public-side queue marker and contract only" in control
    assert "final score and audit reports do not come from sprint 94c alone" in control
