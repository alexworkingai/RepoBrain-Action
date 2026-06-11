from __future__ import annotations

from datetime import datetime, timedelta, timezone

from repobrain.oidc_verify import VerifiedGitHubOidcClaims
from repobrain.tenant_store import InMemoryTenantStore, build_tenant_id


def _claims() -> VerifiedGitHubOidcClaims:
    return VerifiedGitHubOidcClaims(
        issuer="https://token.actions.githubusercontent.com",
        audience="repobrain-api",
        subject="repo:owner/repo:ref:refs/heads/main",
        repository="owner/repo",
        repository_id="123",
        repository_owner="owner",
        repository_owner_id="456",
        run_id="999",
        run_number="3",
        run_attempt="1",
        actor="partner-user",
        actor_id="777",
        workflow="RepoBrain",
        workflow_ref="owner/repo/.github/workflows/repobrain.yml@refs/heads/main",
        workflow_sha="abc123",
        event_name="issue_comment",
        ref="refs/heads/main",
        sha="deadbeef",
    )


def _identity() -> dict[str, object]:
    return {"repository": {"visibility": "public"}}


def test_valid_first_request_auto_creates_tenant() -> None:
    store = InMemoryTenantStore()
    tenant = store.upsert_from_verified_claims(
        claims=_claims(),
        identity=_identity(),
        terms_accepted=True,
    )

    assert tenant.tenant_id == build_tenant_id(owner_id="456", repository_id="123")
    assert tenant.auto_provisioned is True
    assert tenant.manual_approval_required is False
    assert tenant.repository == "owner/repo"


def test_repeat_request_updates_last_seen_and_preserves_first_seen() -> None:
    store = InMemoryTenantStore()
    first_now = datetime(2026, 6, 11, 10, 0, tzinfo=timezone.utc)
    second_now = first_now + timedelta(hours=1)

    first = store.upsert_from_verified_claims(
        claims=_claims(),
        identity=_identity(),
        terms_accepted=True,
        now=first_now,
    )
    second = store.upsert_from_verified_claims(
        claims=_claims(),
        identity=_identity(),
        terms_accepted=True,
        now=second_now,
    )

    assert first.first_seen_at == second.first_seen_at
    assert second.last_seen_at != first.last_seen_at
    assert second.last_actor == "partner-user"

