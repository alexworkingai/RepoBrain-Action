from __future__ import annotations

from pathlib import Path
import json

import yaml

from repobrain.oidc import OidcTokenResult
from repobrain.self_service_identity import (
    SelfServiceConfig,
    build_github_identity_envelope,
    validate_self_service_requirements,
)


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_identity_envelope_includes_repository_and_workflow_metadata() -> None:
    envelope = build_github_identity_envelope(
        event_payload={"repository": {"full_name": "owner/repo", "name": "repo", "private": False}},
        command_context={"name": "audit", "raw": "/repobrain audit", "execution_profile_override": "premium"},
        self_service=SelfServiceConfig(
            enabled=True,
            terms_accepted=True,
            profile="partner-pilot",
            oidc_audience="repobrain-api",
        ),
        oidc_result=OidcTokenResult(
            available=True,
            audience="repobrain-api",
            token_present=True,
            token_redacted=True,
            error_code="none",
            message="GitHub OIDC token acquired.",
            token="header.payload.signature",
        ),
        environ={
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_REPOSITORY_ID": "123",
            "GITHUB_REPOSITORY_OWNER": "owner",
            "GITHUB_REPOSITORY_OWNER_ID": "456",
            "GITHUB_WORKFLOW": "RepoBrain",
            "GITHUB_WORKFLOW_REF": "owner/repo/.github/workflows/repobrain.yml@refs/heads/main",
            "GITHUB_WORKFLOW_SHA": "abc123",
            "GITHUB_JOB": "repobrain",
            "GITHUB_RUN_ID": "999",
            "GITHUB_RUN_NUMBER": "12",
            "GITHUB_RUN_ATTEMPT": "2",
            "GITHUB_EVENT_NAME": "issue_comment",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_SHA": "deadbeef",
            "GITHUB_ACTOR": "partner-user",
            "GITHUB_ACTOR_ID": "789",
            "GITHUB_ACTION_REPOSITORY": "alexworkingai/RepoBrain-Action",
            "GITHUB_ACTION_REF": "main",
        },
    )

    assert envelope["version"] == "repobrain.github_oidc_identity.v1"
    assert envelope["provider"] == "github_actions_oidc"
    assert envelope["repository"]["full_name"] == "owner/repo"
    assert envelope["repository"]["visibility"] == "public"
    assert envelope["workflow"]["run_id"] == "999"
    assert envelope["action"]["repository"] == "alexworkingai/RepoBrain-Action"
    assert envelope["command"]["profile"] == "partner-pilot"
    assert envelope["command"]["execution_profile_override"] == "premium"
    assert envelope["self_service"]["enabled"] is True
    assert envelope["oidc"]["token_present"] is True
    assert "header.payload.signature" not in json.dumps(envelope, sort_keys=True)


def test_identity_envelope_tolerates_missing_optional_metadata() -> None:
    envelope = build_github_identity_envelope(
        event_payload={},
        command_context={"name": "help", "raw": "/repobrain help"},
        self_service=SelfServiceConfig(),
        oidc_result=OidcTokenResult(
            available=False,
            audience="repobrain-api",
            token_present=False,
            token_redacted=True,
            error_code="oidc_unavailable",
            message="GitHub OIDC is unavailable.",
            token="",
        ),
        environ={"GITHUB_REPOSITORY": "owner/repo"},
    )

    assert envelope["repository"]["full_name"] == "owner/repo"
    assert envelope["workflow"]["run_id"] is None
    assert envelope["action"]["ref"] is None
    assert envelope["command"]["name"] == "help"
    assert envelope["oidc"]["available"] is False


def test_validate_self_service_requirements_respects_enabled_mode() -> None:
    base_envelope = {
        "repository": {"full_name": "owner/repo"},
        "workflow": {"event_name": "issue_comment", "run_id": "777"},
        "command": {"name": "audit"},
    }

    ok, message, status = validate_self_service_requirements(
        self_service=SelfServiceConfig(enabled=False),
        oidc_result=OidcTokenResult(
            available=False,
            audience="repobrain-api",
            token_present=False,
            token_redacted=True,
            error_code="oidc_unavailable",
            message="GitHub OIDC is unavailable.",
            token="",
        ),
        identity_envelope=base_envelope,
    )
    assert ok is True
    assert message is None
    assert status == "self_service_disabled"


def test_action_yml_maps_self_service_inputs_into_runtime_env() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    run_step = next(step for step in action["runs"]["steps"] if step.get("name") == "Run RepoBrain GitHub dry-run wiring")
    env = run_step["env"]

    assert env["RB_SELF_SERVICE_PROFILE"] == "${{ inputs.profile }}"
    assert env["RB_SELF_SERVICE_TERMS_ACCEPTED"] == "${{ inputs.terms_accepted }}"
    assert env["RB_SELF_SERVICE_API_URL"] == "${{ inputs.api_url }}"
    assert env["RB_SELF_SERVICE_OIDC_AUDIENCE"] == "${{ inputs.oidc_audience }}"
    assert env["RB_SELF_SERVICE_MODE"] == "${{ inputs.self_service_mode }}"


def test_self_service_docs_reflect_93b_without_overclaim() -> None:
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md").lower()
    architecture = _read("docs/architecture/SPRINT_93B_OIDC_IDENTITY_ENVELOPE.md").lower()
    architecture_93c = _read("docs/architecture/SPRINT_93C_HOSTED_API_TRUST_AND_PROVISIONING.md").lower()
    workflow = _read("docs/examples/repobrain_partner_self_service_workflow.yml").lower()

    assert "sprint 93b implements" in quickstart
    assert "hosted api verification is implemented as a sprint 93c boundary" in quickstart
    assert "automatic tenant provisioning is implemented as a sprint 93c boundary" in quickstart
    assert "fully live" in quickstart
    assert "oidc token acquisition" in architecture
    assert "tenant provisioning boundaries" in architecture or "hosted verification and tenant provisioning boundaries" in architecture
    assert "automatic tenant provisioning" in architecture_93c
    assert "repobrain.github_oidc_identity.v1" in architecture
    assert "not yet fully live" in quickstart or "not yet fully live" in architecture
    assert "id-token: write" in workflow
    assert "topocore_v6_repo_token" not in workflow
    assert "topocore_v6_artifact_token" not in workflow
