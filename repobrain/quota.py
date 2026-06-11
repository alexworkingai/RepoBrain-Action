from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any

from repobrain.hosted_api_contract import PARTNER_QUOTA_VERSION


def _utc_now(now: datetime | None = None) -> datetime:
    return now.astimezone(timezone.utc) if now is not None else datetime.now(timezone.utc)


def _next_utc_reset(now: datetime) -> datetime:
    tomorrow = (now + timedelta(days=1)).date()
    return datetime.combine(tomorrow, time.min, tzinfo=timezone.utc)


@dataclass(frozen=True)
class PartnerQuotaPolicy:
    version: str = PARTNER_QUOTA_VERSION
    plan: str = "partner_pilot_auto"
    profile: str = "partner_pilot_default"
    audit_score_runs_per_day: int = 20
    ask_runs_per_day: int = 20
    premium_narrative_runs_per_day: int = 5


@dataclass(frozen=True)
class QuotaDecision:
    version: str
    status: str
    profile: str
    remaining: int
    reset_at: str
    allowed: bool
    retryable: bool
    plan: str

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("allowed", None)
        payload.pop("retryable", None)
        return payload


class InMemoryQuotaStore:
    def __init__(self, policy: PartnerQuotaPolicy | None = None) -> None:
        self.policy = policy or PartnerQuotaPolicy()
        self._usage: dict[tuple[str, str, str], int] = {}

    def evaluate_and_consume(
        self,
        *,
        tenant_id: str,
        route: str,
        profile: str,
        now: datetime | None = None,
    ) -> QuotaDecision:
        current = _utc_now(now)
        reset_at = _next_utc_reset(current)
        window_key = current.date().isoformat()
        checks = self._quota_buckets_for(route=route, profile=profile)
        if not checks:
            checks = [("audit_score", self.policy.audit_score_runs_per_day)]

        remaining_after: list[int] = []
        for bucket, limit in checks:
            used = self._usage.get((tenant_id, bucket, window_key), 0)
            if used >= limit:
                return QuotaDecision(
                    version=PARTNER_QUOTA_VERSION,
                    status="exceeded",
                    profile=self.policy.profile,
                    remaining=0,
                    reset_at=reset_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                    allowed=False,
                    retryable=False,
                    plan=self.policy.plan,
                )
            remaining_after.append(limit - used - 1)

        for bucket, _limit in checks:
            key = (tenant_id, bucket, window_key)
            self._usage[key] = self._usage.get(key, 0) + 1

        return QuotaDecision(
            version=PARTNER_QUOTA_VERSION,
            status="ok",
            profile=self.policy.profile,
            remaining=min(remaining_after) if remaining_after else 0,
            reset_at=reset_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            allowed=True,
            retryable=False,
            plan=self.policy.plan,
        )

    def _quota_buckets_for(self, *, route: str, profile: str) -> list[tuple[str, int]]:
        route_norm = str(route or "").strip().lower()
        profile_norm = str(profile or "").strip().lower()
        checks: list[tuple[str, int]] = []
        if route_norm in {"audit", "score"}:
            checks.append(("audit_score", self.policy.audit_score_runs_per_day))
        elif route_norm == "ask":
            checks.append(("ask", self.policy.ask_runs_per_day))
        else:
            checks.append(("audit_score", self.policy.audit_score_runs_per_day))
        if profile_norm == "premium":
            checks.append(("premium_narrative", self.policy.premium_narrative_runs_per_day))
        return checks
