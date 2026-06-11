from __future__ import annotations

from datetime import datetime, timezone

from repobrain.quota import InMemoryQuotaStore, PartnerQuotaPolicy


def test_default_partner_pilot_quota_exists() -> None:
    policy = PartnerQuotaPolicy()

    assert policy.plan == "partner_pilot_auto"
    assert policy.audit_score_runs_per_day == 20
    assert policy.ask_runs_per_day == 20
    assert policy.premium_narrative_runs_per_day == 5


def test_first_audit_run_leaves_19_remaining() -> None:
    store = InMemoryQuotaStore()
    decision = store.evaluate_and_consume(
        tenant_id="tenant-1",
        route="audit",
        profile="partner-pilot",
        now=datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc),
    )

    assert decision.allowed is True
    assert decision.status == "ok"
    assert decision.remaining == 19


def test_quota_exceeded_blocks_before_processing() -> None:
    store = InMemoryQuotaStore()
    now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
    for _ in range(20):
        decision = store.evaluate_and_consume(
            tenant_id="tenant-1",
            route="audit",
            profile="partner-pilot",
            now=now,
        )
        assert decision.allowed is True
    exceeded = store.evaluate_and_consume(
        tenant_id="tenant-1",
        route="audit",
        profile="partner-pilot",
        now=now,
    )

    assert exceeded.allowed is False
    assert exceeded.status == "exceeded"
    assert exceeded.remaining == 0


def test_premium_path_has_tighter_quota() -> None:
    store = InMemoryQuotaStore()
    now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
    for _ in range(5):
        decision = store.evaluate_and_consume(
            tenant_id="tenant-2",
            route="audit",
            profile="premium",
            now=now,
        )
        assert decision.allowed is True
    exceeded = store.evaluate_and_consume(
        tenant_id="tenant-2",
        route="audit",
        profile="premium",
        now=now,
    )

    assert exceeded.allowed is False
    assert exceeded.status == "exceeded"

