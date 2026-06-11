from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from repobrain.hosted_api_contract import PARTNER_TENANT_VERSION
from repobrain.oidc_verify import VerifiedGitHubOidcClaims


def _utc_now_iso(now: datetime | None = None) -> str:
    current = now.astimezone(timezone.utc) if now is not None else datetime.now(timezone.utc)
    return current.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_tenant_id(*, owner_id: str, repository_id: str) -> str:
    return f"gh_owner_{owner_id}_repo_{repository_id}"


@dataclass(frozen=True)
class PartnerTenant:
    version: str
    tenant_id: str
    repository_id: str
    repository: str
    repository_owner: str
    repository_owner_id: str
    repository_visibility: str
    github_subject: str
    plan: str
    auto_provisioned: bool
    manual_approval_required: bool
    terms_accepted: bool
    first_seen_at: str
    last_seen_at: str
    last_workflow_ref: str
    last_workflow_sha: str
    last_actor: str
    last_actor_id: str
    last_event_name: str
    status: str

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


class InMemoryTenantStore:
    def __init__(self) -> None:
        self._tenants: dict[str, PartnerTenant] = {}

    def get(self, tenant_id: str) -> PartnerTenant | None:
        return self._tenants.get(str(tenant_id or "").strip())

    def upsert_from_verified_claims(
        self,
        *,
        claims: VerifiedGitHubOidcClaims,
        identity: dict[str, Any],
        terms_accepted: bool,
        plan: str = "partner_pilot_auto",
        now: datetime | None = None,
    ) -> PartnerTenant:
        tenant_id = build_tenant_id(
            owner_id=claims.repository_owner_id,
            repository_id=claims.repository_id,
        )
        existing = self._tenants.get(tenant_id)
        now_iso = _utc_now_iso(now)
        visibility = str(
            identity.get("repository", {}).get("visibility", claims.repository_visibility or "unknown")
            if isinstance(identity.get("repository"), dict)
            else (claims.repository_visibility or "unknown")
        )
        tenant = PartnerTenant(
            version=PARTNER_TENANT_VERSION,
            tenant_id=tenant_id,
            repository_id=claims.repository_id,
            repository=claims.repository,
            repository_owner=claims.repository_owner,
            repository_owner_id=claims.repository_owner_id,
            repository_visibility=visibility,
            github_subject=claims.subject,
            plan=plan,
            auto_provisioned=True,
            manual_approval_required=False,
            terms_accepted=bool(terms_accepted),
            first_seen_at=existing.first_seen_at if existing is not None else now_iso,
            last_seen_at=now_iso,
            last_workflow_ref=claims.workflow_ref,
            last_workflow_sha=claims.workflow_sha,
            last_actor=claims.actor,
            last_actor_id=claims.actor_id,
            last_event_name=claims.event_name,
            status="active",
        )
        self._tenants[tenant_id] = tenant
        return tenant
