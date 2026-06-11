from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_partner_self_service_quickstart_exists_and_marks_phase1_as_foundation_only() -> None:
    text = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md").lower()

    assert "phase 1" in text
    assert "foundation" in text
    assert "not a completed production path yet" in text or "not yet fully live" in text
    assert "sprint 93b implements" in text
    assert "sprint 93c" in text


def test_partner_self_service_quickstart_does_not_require_owner_token_or_manual_registration() -> None:
    text = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md").lower()

    assert "no repobrain owner-generated secret" in text or "no repobrain owner token" in text
    assert "no repobrain-issued partner token" in text
    assert "no manual partner registration" in text
    assert "no manual partner metadata intake" in text
    assert "request a token from the repobrain owner" not in text


def test_partner_self_service_quickstart_does_not_instruct_installing_topocore() -> None:
    text = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md").lower()

    assert "do not install or download topocore" in text
    assert "topocore v6 remains private and server-side" in text or "topocore remains private and server-side" in text
    assert ".topocore-v6" not in text
    assert "pip install" not in text


def test_partner_self_service_workflow_example_has_id_token_and_no_owner_secret() -> None:
    text = _read("docs/examples/repobrain_partner_self_service_workflow.yml")
    lowered = text.lower()

    assert "id-token: write" in lowered
    assert "contents: read" in lowered
    assert "issues: write" in lowered
    assert "pull-requests: write" in lowered
    assert "terms_accepted" in text
    assert "self_service_mode" in text
    assert "TOPOCORE_V6_REPO_TOKEN" not in text
    assert "TOPOCORE_V6_ARTIFACT_TOKEN" not in text
    assert ".topocore-v6" not in text
    assert "actions/checkout@v5" in text


def test_architecture_note_states_thin_client_and_private_server_side_runtime() -> None:
    text = _read("docs/architecture/SPRINT_93A_SELF_SERVICE_PARTNER_FOUNDATION.md").lower()

    assert "public thin client" in text
    assert "private hosted and server-side runtime" in text
    assert "partners must not receive topocore source, package, or container" in text
    assert "must not install topocore" in text
    assert "no github app in phase 1" in text


def test_architecture_note_lists_93b_to_93e_handoff_and_defers_later_phases() -> None:
    text = _read("docs/architecture/SPRINT_93A_SELF_SERVICE_PARTNER_FOUNDATION.md").lower()

    assert "sprint 93b now provides" in text
    assert "sprint 93c should implement" in text
    assert "sprint 93d should implement" in text
    assert "sprint 93e should implement" in text
    assert "billing or subscription workflows" in text


def test_action_yml_exposes_optional_non_breaking_self_service_inputs() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    inputs = action["inputs"]

    for key in ("profile", "terms_accepted", "api_url", "oidc_audience", "self_service_mode"):
        assert key in inputs
        assert inputs[key]["required"] is False

    assert inputs["profile"]["default"] == "partner-pilot"
    assert inputs["terms_accepted"]["default"] == "false"
    assert inputs["api_url"]["default"] == ""
    assert inputs["oidc_audience"]["default"] == "repobrain-api"
    assert inputs["self_service_mode"]["default"] == "false"


def test_readme_surfaces_self_service_foundation_without_overclaim() -> None:
    text = _read("README.md").lower()

    assert "phase 1 self-service" in text
    assert "thin public client direction" in text
    assert "private hosted/server-side runtime direction" in text
    assert "not claimed as fully live" in text or "not yet claimed as fully live" in text
