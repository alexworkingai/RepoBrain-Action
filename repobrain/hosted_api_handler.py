from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from repobrain.hosted_api_contract import (
    GITHUB_ACTION_AUDIT_REQUEST_VERSION,
    build_error_response,
    build_success_response,
    sanitize_request_for_logs,
    validate_github_action_audit_request,
    HostedApiContractError,
    MAX_MARKDOWN_CHARS,
)
from repobrain.hosted_topocore_adapter import (
    HostedTopoCoreAuditAdapter,
    HostedTopoCoreAuditRequest,
    HostedTopoCoreUnavailableError,
    UnavailableHostedTopoCoreAuditAdapter,
)
from repobrain.oidc_verify import (
    GitHubOidcVerificationError,
    GitHubOidcVerifier,
    validate_claims_match_identity,
)
from repobrain.quota import InMemoryQuotaStore
from repobrain.tenant_store import InMemoryTenantStore


@dataclass(frozen=True)
class HostedApiHandlerConfig:
    expected_audience: str = "repobrain-api"
    service_name: str = "RepoBrain Hosted API"
    default_plan: str = "partner_pilot_auto"


def handle_github_action_audit_request(
    request_json: Mapping[str, Any],
    *,
    config: HostedApiHandlerConfig | None = None,
    verifier: GitHubOidcVerifier | None = None,
    tenant_store: InMemoryTenantStore | None = None,
    quota_store: InMemoryQuotaStore | None = None,
    topocore_adapter: HostedTopoCoreAuditAdapter | None = None,
) -> dict[str, Any]:
    cfg = config or HostedApiHandlerConfig()
    verifier = verifier or GitHubOidcVerifier()
    tenant_store = tenant_store or InMemoryTenantStore()
    quota_store = quota_store or InMemoryQuotaStore()
    topocore_adapter = topocore_adapter or UnavailableHostedTopoCoreAuditAdapter()

    try:
        request = validate_github_action_audit_request(request_json)
        _ = sanitize_request_for_logs(request)
        if request["version"] != GITHUB_ACTION_AUDIT_REQUEST_VERSION:
            raise HostedApiContractError(
                "INVALID_REQUEST_VERSION",
                "Hosted audit request version is invalid.",
            )

        identity = request["identity"]
        self_service = identity.get("self_service", {}) if isinstance(identity.get("self_service"), Mapping) else {}
        if not bool(self_service.get("enabled", False)):
            raise HostedApiContractError(
                "SELF_SERVICE_DISABLED",
                "RepoBrain self-service mode is disabled for this request.",
            )
        if not bool(self_service.get("terms_accepted", False)):
            raise HostedApiContractError(
                "TERMS_NOT_ACCEPTED",
                "RepoBrain self-service terms must be accepted before hosted processing.",
            )
        oidc_jwt = str(request.get("oidc_jwt", "") or "").strip()
        if not oidc_jwt:
            raise HostedApiContractError(
                "OIDC_MISSING_TOKEN",
                "GitHub OIDC token is missing.",
            )

        verified_claims = verifier.verify_token(
            oidc_jwt,
            expected_audience=str(identity.get("oidc", {}).get("audience", cfg.expected_audience) or cfg.expected_audience),
        )
        validate_claims_match_identity(verified_claims, identity)

        tenant = tenant_store.upsert_from_verified_claims(
            claims=verified_claims,
            identity=dict(identity),
            terms_accepted=True,
            plan=cfg.default_plan,
        )
        command = request["command"]
        quota_decision = quota_store.evaluate_and_consume(
            tenant_id=tenant.tenant_id,
            route=str(command.get("route", "") or "").strip().lower(),
            profile=str(command.get("profile", "") or "").strip(),
        )
        if not quota_decision.allowed:
            raise HostedApiContractError(
                "QUOTA_EXCEEDED",
                "RepoBrain partner-pilot quota was exceeded for this repository.",
            )

        topocore_request = HostedTopoCoreAuditRequest(
            tenant=tenant.to_public_dict(),
            identity=dict(identity),
            command=dict(command),
            evidence=dict(request["evidence"]),
        )
        topocore_result = topocore_adapter.run_audit(topocore_request)
        markdown = " ".join(str(topocore_result.markdown or "").split())[:MAX_MARKDOWN_CHARS].strip()
        report = {
            "format": str(topocore_result.report_format or "repobrain.audit_report.v1"),
            "score": int(topocore_result.score),
            "band": str(topocore_result.band or "WEAK"),
            "markdown": markdown,
        }
        return build_success_response(
            tenant={
                "tenant_id": tenant.tenant_id,
                "repository_id": tenant.repository_id,
                "repository": tenant.repository,
                "plan": tenant.plan,
                "auto_provisioned": tenant.auto_provisioned,
                "manual_approval_required": tenant.manual_approval_required,
            },
            quota=quota_decision.to_public_dict(),
            report=report,
        )
    except HostedApiContractError as exc:
        return build_error_response(
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
        )
    except GitHubOidcVerificationError as exc:
        return build_error_response(
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
        )
    except HostedTopoCoreUnavailableError:
        return build_error_response(
            code="TOPOCORE_UNAVAILABLE",
            message="Private hosted TopoCore runtime is unavailable.",
            retryable=True,
        )
    except Exception:
        return build_error_response(
            code="INTERNAL_ERROR_REDACTED",
            message="RepoBrain hosted processing failed with a redacted internal error.",
            retryable=False,
        )
