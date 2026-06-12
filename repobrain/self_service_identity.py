from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping

from repobrain import __version__ as REPOBRAIN_VERSION
from repobrain.oidc import OIDC_REQUIRED_MESSAGE, OidcTokenResult, normalize_oidc_audience


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    raw = str(value or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def _clean_optional(value: str | None) -> str:
    return str(value or "").strip()


def _value_or_none(value: str | None) -> str | None:
    text = _clean_optional(value)
    return text or None


@dataclass(frozen=True)
class SelfServiceConfig:
    enabled: bool = False
    terms_accepted: bool = False
    profile: str = "default"
    api_url: str = ""
    oidc_audience: str = "repobrain-api"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "SelfServiceConfig":
        env = environ or os.environ
        profile = _clean_optional(env.get("RB_SELF_SERVICE_PROFILE")) or "default"
        return cls(
            enabled=_parse_bool(env.get("RB_SELF_SERVICE_MODE"), default=False),
            terms_accepted=_parse_bool(env.get("RB_SELF_SERVICE_TERMS_ACCEPTED"), default=False),
            profile=profile,
            api_url=_clean_optional(env.get("RB_SELF_SERVICE_API_URL")),
            oidc_audience=normalize_oidc_audience(env.get("RB_SELF_SERVICE_OIDC_AUDIENCE")),
        )


def build_github_identity_envelope(
    *,
    event_payload: dict[str, Any] | None,
    command_context: dict[str, Any] | None,
    self_service: SelfServiceConfig,
    oidc_result: OidcTokenResult,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = environ or os.environ
    payload = event_payload if isinstance(event_payload, dict) else {}
    repository = payload.get("repository", {})
    repo_full_name = _clean_optional(env.get("GITHUB_REPOSITORY"))
    repo_owner = _clean_optional(env.get("GITHUB_REPOSITORY_OWNER"))
    repo_name = ""
    if repo_full_name and "/" in repo_full_name:
        repo_owner = repo_owner or repo_full_name.split("/", 1)[0]
        repo_name = repo_full_name.split("/", 1)[1]
    if isinstance(repository, dict):
        repo_full_name = repo_full_name or _clean_optional(repository.get("full_name"))
        repo_owner = repo_owner or _clean_optional(
            repository.get("owner", {}).get("login") if isinstance(repository.get("owner"), dict) else ""
        )
        repo_name = repo_name or _clean_optional(repository.get("name"))
    visibility = "unknown"
    if isinstance(repository, dict):
        if "private" in repository:
            visibility = "private" if bool(repository.get("private")) else "public"
        else:
            visibility = _clean_optional(repository.get("visibility")) or "unknown"

    command = command_context if isinstance(command_context, dict) else {}
    command_name = _clean_optional(command.get("name")) or "unknown"
    command_raw = _clean_optional(command.get("raw"))
    command_profile = _clean_optional(command.get("profile")) or self_service.profile
    execution_profile_override = _clean_optional(command.get("execution_profile_override")) or "none"

    return {
        "version": "repobrain.github_oidc_identity.v1",
        "provider": "github_actions_oidc",
        "oidc": oidc_result.redacted_dict(),
        "repository": {
            "full_name": repo_full_name or "unknown",
            "owner": repo_owner or "unknown",
            "name": repo_name or "unknown",
            "id": _value_or_none(env.get("GITHUB_REPOSITORY_ID")),
            "owner_id": _value_or_none(env.get("GITHUB_REPOSITORY_OWNER_ID")),
            "visibility": visibility,
        },
        "workflow": {
            "workflow": _value_or_none(env.get("GITHUB_WORKFLOW")),
            "workflow_ref": _value_or_none(env.get("GITHUB_WORKFLOW_REF")),
            "workflow_sha": _value_or_none(env.get("GITHUB_WORKFLOW_SHA")),
            "job": _value_or_none(env.get("GITHUB_JOB")),
            "run_id": _value_or_none(env.get("GITHUB_RUN_ID")),
            "run_number": _value_or_none(env.get("GITHUB_RUN_NUMBER")),
            "run_attempt": _value_or_none(env.get("GITHUB_RUN_ATTEMPT")),
            "event_name": _value_or_none(env.get("GITHUB_EVENT_NAME")),
            "ref": _value_or_none(env.get("GITHUB_REF")),
            "sha": _value_or_none(env.get("GITHUB_SHA")),
            "actor": _value_or_none(env.get("GITHUB_ACTOR")),
            "actor_id": _value_or_none(env.get("GITHUB_ACTOR_ID")),
        },
        "action": {
            "repository": _value_or_none(env.get("GITHUB_ACTION_REPOSITORY")) or "alexworkingai/RepoBrain-Action",
            "ref": _value_or_none(env.get("GITHUB_ACTION_REF")),
            "version": REPOBRAIN_VERSION,
        },
        "command": {
            "name": command_name,
            "profile": command_profile,
            "raw": command_raw,
            "execution_profile_override": execution_profile_override,
        },
        "self_service": {
            "enabled": bool(self_service.enabled),
            "terms_accepted": bool(self_service.terms_accepted),
            "mode": self_service.profile,
            "api_url_configured": bool(self_service.api_url),
        },
    }


def validate_self_service_requirements(
    *,
    self_service: SelfServiceConfig,
    oidc_result: OidcTokenResult,
    identity_envelope: dict[str, Any],
) -> tuple[bool, str | None, str]:
    if not self_service.enabled:
        return True, None, "self_service_disabled"
    if not self_service.terms_accepted:
        return (
            False,
            'RepoBrain self-service mode requires `terms_accepted: "true"` in the workflow.',
            "terms_not_accepted",
        )
    if not oidc_result.token_present:
        return False, OIDC_REQUIRED_MESSAGE, "oidc_required"

    repository = identity_envelope.get("repository", {})
    workflow = identity_envelope.get("workflow", {})
    command = identity_envelope.get("command", {})
    required_ok = all(
        [
            str(repository.get("full_name", "") or "").strip() not in {"", "unknown"},
            str(workflow.get("event_name", "") or "").strip() not in {"", "unknown"},
            str(workflow.get("run_id", "") or "").strip() not in {"", "unknown"},
            str(command.get("name", "") or "").strip() not in {"", "unknown"},
        ]
    )
    if not required_ok:
        return (
            False,
            "RepoBrain self-service mode requires GitHub workflow identity metadata. Re-run inside "
            "a GitHub Actions workflow and retry.",
            "identity_metadata_missing",
        )
    return True, None, "self_service_ready"
