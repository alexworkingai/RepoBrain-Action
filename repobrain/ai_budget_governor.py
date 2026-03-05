from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
from typing import Any


def _env_true(name: str, default: bool = False) -> bool:
    value = __import__("os").environ.get(name, "")
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = __import__("os").environ.get(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class QuotaSignal:
    remaining_requests: int | None
    reset_time_utc_iso: str | None
    remaining_is_estimate: bool
    usage_estimated: bool
    ratelimit_headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BudgetPolicy:
    stop_at_remaining: bool = True
    min_remaining_buffer: int = 2
    max_llm_calls_per_run: int = 6
    max_embed_calls_per_run: int = 10
    disable_reduce_when_remaining_lt: int = 3
    switch_to_mini_when_remaining_lt: int = 5
    disable_embed_when_remaining_lt: int = 3
    estimate_mode_conservative: bool = True
    max_tokens_per_run_llm: int = 12_000
    max_tokens_per_run_embed: int = 200_000
    time_budget_s: int = 240

    @classmethod
    def from_env(cls) -> BudgetPolicy:
        return cls(
            stop_at_remaining=_env_true("RB_AI_STOP_AT_REMAINING", default=True),
            min_remaining_buffer=max(0, _env_int("RB_AI_MIN_REMAINING_BUFFER", 2)),
            max_llm_calls_per_run=max(1, _env_int("RB_AI_MAX_LLM_CALLS_PER_RUN", 6)),
            max_embed_calls_per_run=max(1, _env_int("RB_AI_MAX_EMBED_CALLS_PER_RUN", 10)),
            disable_reduce_when_remaining_lt=max(
                0, _env_int("RB_AI_DISABLE_REDUCE_WHEN_REMAINING_LT", 3)
            ),
            switch_to_mini_when_remaining_lt=max(
                0, _env_int("RB_AI_SWITCH_TO_MINI_WHEN_REMAINING_LT", 5)
            ),
            disable_embed_when_remaining_lt=max(
                0, _env_int("RB_AI_DISABLE_EMBED_WHEN_REMAINING_LT", 3)
            ),
            estimate_mode_conservative=_env_true("RB_AI_ESTIMATE_MODE_CONSERVATIVE", default=True),
            max_tokens_per_run_llm=max(1, _env_int("RB_AI_MAX_TOKENS_PER_RUN_LLM", 12_000)),
            max_tokens_per_run_embed=max(1, _env_int("RB_AI_MAX_TOKENS_PER_RUN_EMBED", 200_000)),
            time_budget_s=max(1, _env_int("RB_AI_TIME_BUDGET_S", 240)),
        )


@dataclass(frozen=True)
class GovernorDecision:
    allow: bool
    reason: str
    switch_to_mini: bool = False
    disable_reduce: bool = False
    disable_embeddings: bool = False
    max_calls: int | None = None
    budget_action: str = "n/a"


class AIBudgetGovernor:
    """Unified run-level governor for LLM + embeddings budgets and quota signals."""

    def __init__(self, policy: BudgetPolicy) -> None:
        self.policy = policy
        self.started_at = time.perf_counter()

        self.llm_calls_count = 0
        self.llm_tokens_total = 0
        self.llm_last_remaining: int | None = None
        self.llm_last_reset: str | None = None
        self.llm_remaining_is_estimate = True
        self.llm_usage_estimated = True

        self.embed_calls_count = 0
        self.embed_tokens_total = 0
        self.embed_last_remaining: int | None = None
        self.embed_last_reset: str | None = None
        self.embed_remaining_is_estimate = True
        self.embed_usage_estimated = True

        self._decisions_log: list[dict[str, Any]] = []

    def _record(self, component: str, decision: GovernorDecision, context: dict[str, Any]) -> None:
        self._decisions_log.append(
            {
                "component": component,
                "allow": decision.allow,
                "reason": decision.reason,
                "budget_action": decision.budget_action,
                "switch_to_mini": decision.switch_to_mini,
                "disable_reduce": decision.disable_reduce,
                "disable_embeddings": decision.disable_embeddings,
                "max_calls": decision.max_calls,
                "context": context,
            }
        )

    def _time_budget_exceeded(self) -> bool:
        elapsed = time.perf_counter() - self.started_at
        return elapsed >= float(self.policy.time_budget_s)

    def observe_llm_signal(self, signal: QuotaSignal, usage: dict[str, Any]) -> None:
        self.llm_calls_count += 1
        self.llm_tokens_total += int(usage.get("tokens_total", 0) or 0)
        self.llm_last_remaining = signal.remaining_requests
        self.llm_last_reset = signal.reset_time_utc_iso
        self.llm_remaining_is_estimate = bool(signal.remaining_is_estimate)
        self.llm_usage_estimated = bool(signal.usage_estimated)

    def observe_embed_signal(self, signal: QuotaSignal, usage: dict[str, Any]) -> None:
        self.embed_calls_count += 1
        self.embed_tokens_total += int(usage.get("tokens_total", 0) or 0)
        self.embed_last_remaining = signal.remaining_requests
        self.embed_last_reset = signal.reset_time_utc_iso
        self.embed_remaining_is_estimate = bool(signal.remaining_is_estimate)
        self.embed_usage_estimated = bool(signal.usage_estimated)

    def can_call_llm(self, next_call_cost_est: int, tier: str, intent: str) -> GovernorDecision:
        context = {
            "next_call_cost_est": int(next_call_cost_est),
            "tier": str(tier),
            "intent": str(intent),
        }
        if self._time_budget_exceeded():
            decision = GovernorDecision(
                allow=False,
                reason="time_budget_exceeded",
                budget_action="llm_disabled_time_budget",
            )
            self._record("llm", decision, context)
            return decision

        if self.llm_calls_count >= self.policy.max_llm_calls_per_run:
            decision = GovernorDecision(
                allow=False,
                reason="llm_calls_budget_exceeded",
                budget_action="llm_calls_capped",
            )
            self._record("llm", decision, context)
            return decision

        projected_tokens = self.llm_tokens_total + int(next_call_cost_est)
        if projected_tokens > self.policy.max_tokens_per_run_llm:
            decision = GovernorDecision(
                allow=False,
                reason="llm_tokens_budget_exceeded",
                budget_action="llm_tokens_capped",
            )
            self._record("llm", decision, context)
            return decision

        remaining = self.llm_last_remaining
        if remaining is not None:
            if self.policy.stop_at_remaining and remaining <= 0:
                decision = GovernorDecision(
                    allow=False,
                    reason="llm_remaining_exhausted",
                    budget_action="llm_disabled_remaining_zero",
                )
                self._record("llm", decision, context)
                return decision
            if remaining <= self.policy.min_remaining_buffer:
                decision = GovernorDecision(
                    allow=False,
                    reason="llm_remaining_buffer",
                    budget_action="llm_disabled_buffer_guard",
                )
                self._record("llm", decision, context)
                return decision

        switch_to_mini = False
        disable_reduce = False
        actions: list[str] = []
        max_calls: int | None = None

        if remaining is not None:
            if remaining < self.policy.switch_to_mini_when_remaining_lt and str(tier).lower() == "high":
                switch_to_mini = True
                actions.append("model_downgraded_to_mini")
            if remaining < self.policy.disable_reduce_when_remaining_lt:
                disable_reduce = True
                actions.append("reduce_disabled_remaining_low")
            max_calls = max(0, remaining - self.policy.min_remaining_buffer)
        elif self.policy.estimate_mode_conservative:
            if str(tier).lower() == "high":
                switch_to_mini = True
                actions.append("model_downgraded_to_mini_estimate_mode")
            if intent in {"review", "patch", "fix"}:
                disable_reduce = True
                actions.append("reduce_disabled_estimate_mode")

        decision = GovernorDecision(
            allow=True,
            reason="ok",
            switch_to_mini=switch_to_mini,
            disable_reduce=disable_reduce,
            disable_embeddings=False,
            max_calls=max_calls,
            budget_action="; ".join(actions) if actions else "n/a",
        )
        self._record("llm", decision, context)
        return decision

    def can_call_embed(self, next_call_cost_est: int) -> GovernorDecision:
        context = {"next_call_cost_est": int(next_call_cost_est)}
        if self._time_budget_exceeded():
            decision = GovernorDecision(
                allow=False,
                reason="time_budget_exceeded",
                disable_embeddings=True,
                budget_action="embeddings_disabled_time_budget",
            )
            self._record("embed", decision, context)
            return decision

        if self.embed_calls_count >= self.policy.max_embed_calls_per_run:
            decision = GovernorDecision(
                allow=False,
                reason="embed_calls_budget_exceeded",
                disable_embeddings=True,
                budget_action="embeddings_calls_capped",
            )
            self._record("embed", decision, context)
            return decision

        projected_tokens = self.embed_tokens_total + int(next_call_cost_est)
        if projected_tokens > self.policy.max_tokens_per_run_embed:
            decision = GovernorDecision(
                allow=False,
                reason="embed_tokens_budget_exceeded",
                disable_embeddings=True,
                budget_action="embeddings_tokens_capped",
            )
            self._record("embed", decision, context)
            return decision

        remaining = self.embed_last_remaining
        if remaining is not None:
            if self.policy.stop_at_remaining and remaining <= 0:
                decision = GovernorDecision(
                    allow=False,
                    reason="embed_remaining_exhausted",
                    disable_embeddings=True,
                    budget_action="embeddings_disabled_remaining_zero",
                )
                self._record("embed", decision, context)
                return decision
            if remaining <= self.policy.min_remaining_buffer:
                decision = GovernorDecision(
                    allow=False,
                    reason="embed_remaining_buffer",
                    disable_embeddings=True,
                    budget_action="embeddings_disabled_buffer_guard",
                )
                self._record("embed", decision, context)
                return decision
            if remaining < self.policy.disable_embed_when_remaining_lt:
                decision = GovernorDecision(
                    allow=False,
                    reason="embed_remaining_low",
                    disable_embeddings=True,
                    budget_action="embeddings_disabled_remaining_low",
                )
                self._record("embed", decision, context)
                return decision

        decision = GovernorDecision(
            allow=True,
            reason="ok",
            disable_embeddings=False,
            budget_action="n/a",
        )
        self._record("embed", decision, context)
        return decision

    def summary(self) -> dict[str, Any]:
        reason_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        for item in self._decisions_log:
            reason = str(item.get("reason", "unknown") or "unknown")
            action = str(item.get("budget_action", "n/a") or "n/a")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            action_counts[action] = action_counts.get(action, 0) + 1
        return {
            "policy": asdict(self.policy),
            "decisions_log_summary": {
                "decisions_total": len(self._decisions_log),
                "reason_counts": reason_counts,
                "budget_action_counts": action_counts,
            },
            "final_state": {
                "llm_calls_count": self.llm_calls_count,
                "llm_tokens_total": self.llm_tokens_total,
                "llm_last_remaining": self.llm_last_remaining,
                "llm_last_reset": self.llm_last_reset,
                "embed_calls_count": self.embed_calls_count,
                "embed_tokens_total": self.embed_tokens_total,
                "embed_last_remaining": self.embed_last_remaining,
                "embed_last_reset": self.embed_last_reset,
            },
        }


def build_governor_from_env() -> AIBudgetGovernor:
    return AIBudgetGovernor(BudgetPolicy.from_env())
