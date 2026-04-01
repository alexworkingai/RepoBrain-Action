from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping


MODEL_ADAPTER_CONTRACT_VERSION = "llm_model_adapter_v1"


def _as_str(value: Any, default: str = "n/a") -> str:
    text = str(value or "").strip()
    return text or default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _as_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _model_family(model_id: str) -> str:
    model = _as_str(model_id, "not_used")
    if model in {"n/a", "not_used", "not used", "unknown"}:
        return "not_used"
    short = model.split("/", 1)[-1].strip().lower()
    for suffix in ("-mini", "-nano", "-small", "-preview"):
        if short.endswith(suffix):
            return short[: -len(suffix)]
    return short


@dataclass(frozen=True)
class ModelAdapterMetadata:
    contract_version: str
    provider: str
    provider_class: str
    request_mode: str
    execution_mode: str
    llm_intent: str
    llm_used: bool
    policy_allowed: bool
    requested_model_id: str
    preferred_model_id: str
    selected_model_id: str
    final_model_id: str
    model_family: str
    downgrade_occurred: bool
    downgrade_reason: str
    provider_http_status: int | None
    provider_error_type: str
    execution_profile_requested: str
    execution_profile_used: str
    execution_profile_reason_code: str
    execution_profile_reason_short: str
    budget_sensitivity: str
    latency_sensitivity: str
    profile_policy_outcome: str
    profile_override_applied: bool
    profile_model_alignment: str

    def as_audit_fields(self) -> dict[str, Any]:
        return {
            "llm_adapter_contract_version": self.contract_version,
            "llm_adapter_provider": self.provider,
            "llm_adapter_provider_class": self.provider_class,
            "llm_adapter_request_mode": self.request_mode,
            "llm_adapter_execution_mode": self.execution_mode,
            "llm_adapter_intent": self.llm_intent,
            "llm_adapter_llm_used": self.llm_used,
            "llm_adapter_policy_allowed": self.policy_allowed,
            "llm_adapter_requested_model_id": self.requested_model_id,
            "llm_adapter_preferred_model_id": self.preferred_model_id,
            "llm_adapter_selected_model_id": self.selected_model_id,
            "llm_adapter_final_model_id": self.final_model_id,
            "llm_adapter_model_family": self.model_family,
            "llm_adapter_downgrade_occurred": self.downgrade_occurred,
            "llm_adapter_downgrade_reason": self.downgrade_reason,
            "llm_adapter_provider_http_status": self.provider_http_status,
            "llm_adapter_provider_error_type": self.provider_error_type,
            "llm_adapter_execution_profile_requested": self.execution_profile_requested,
            "llm_adapter_execution_profile_used": self.execution_profile_used,
            "llm_adapter_execution_profile_reason_code": self.execution_profile_reason_code,
            "llm_adapter_execution_profile_reason_short": self.execution_profile_reason_short,
            "llm_adapter_budget_sensitivity": self.budget_sensitivity,
            "llm_adapter_latency_sensitivity": self.latency_sensitivity,
            "llm_adapter_profile_policy_outcome": self.profile_policy_outcome,
            "llm_adapter_profile_override_applied": self.profile_override_applied,
            "llm_adapter_profile_model_alignment": self.profile_model_alignment,
            # Canonical aliases for non-adapter consumers.
            "llm_provider": self.provider,
            "llm_model_family": self.model_family,
            "llm_model_requested_id": self.requested_model_id,
            "llm_model_selected_id": self.selected_model_id,
            "llm_model_final_id": self.final_model_id,
            "llm_execution_profile_requested": self.execution_profile_requested,
            "llm_execution_profile_used": self.execution_profile_used,
            "llm_execution_profile_reason_code": self.execution_profile_reason_code,
            "llm_execution_profile_reason_short": self.execution_profile_reason_short,
            "llm_budget_sensitivity": self.budget_sensitivity,
            "llm_latency_sensitivity": self.latency_sensitivity,
            "llm_profile_policy_outcome": self.profile_policy_outcome,
            "llm_profile_override_applied": self.profile_override_applied,
            "llm_profile_model_alignment": self.profile_model_alignment,
        }


def _provider_class(provider: str) -> str:
    lowered = provider.lower()
    if lowered == "github_models":
        return "github_models_chat_completions"
    if lowered in {"openai", "azure_openai"}:
        return "openai_compatible"
    return "unknown"


def _execution_profile(value: Any, *, default: str = "balanced") -> str:
    normalized = _as_str(value, default).lower()
    if normalized in {"cheap", "balanced", "premium"}:
        return normalized
    return default


def _sensitivity(value: Any) -> str:
    normalized = _as_str(value, "not_available").lower()
    if normalized in {"low", "normal", "high", "not_available"}:
        return normalized
    return "not_available"


def build_model_adapter_metadata(
    llm_meta: Mapping[str, Any] | None,
    *,
    provider_hint: str | None = None,
) -> ModelAdapterMetadata:
    meta = dict(llm_meta or {})
    provider = _as_str(meta.get("llm_provider", ""), default="")
    if not provider:
        provider = _as_str(provider_hint or "", default="")
    if not provider:
        provider = _as_str(os.getenv("RB_LLM_PROVIDER", ""), default="unknown")
    profile_requested = _execution_profile(
        meta.get("llm_execution_profile_requested", os.getenv("RB_LLM_EXECUTION_PROFILE", "balanced")),
        default="balanced",
    )
    profile_used = _execution_profile(
        meta.get("llm_execution_profile_used", profile_requested),
        default=profile_requested,
    )
    profile_reason_code = _as_str(
        meta.get(
            "llm_execution_profile_reason_code",
            "profile_applied" if profile_requested == profile_used else "profile_overridden",
        ),
        "n/a",
    )
    profile_reason_short = _as_str(
        meta.get(
            "llm_execution_profile_reason_short",
            "Execution profile applied from configured request."
            if profile_requested == profile_used
            else "Execution profile adjusted by runtime guardrail.",
        ),
        "n/a",
    )
    budget_sensitivity = _sensitivity(
        meta.get("llm_budget_sensitivity", os.getenv("RB_LLM_BUDGET_SENSITIVITY", "not_available"))
    )
    latency_sensitivity = _sensitivity(
        meta.get("llm_latency_sensitivity", os.getenv("RB_LLM_LATENCY_SENSITIVITY", "not_available"))
    )
    profile_policy_outcome = _as_str(
        meta.get(
            "llm_profile_policy_outcome",
            "profile_applied" if profile_requested == profile_used else "guardrail_override",
        ),
        "n/a",
    )
    profile_override_applied = _as_bool(
        meta.get("llm_profile_override_applied", profile_requested != profile_used)
    )
    profile_model_alignment = _as_str(
        meta.get("llm_profile_model_alignment", "not_evaluated"),
        "not_evaluated",
    )

    requested_model_id = _as_str(
        meta.get("llm_primary_model_id", meta.get("llm_preferred_model_id", "not used")),
        "not_used",
    )
    preferred_model_id = _as_str(meta.get("llm_preferred_model_id", requested_model_id), "not_used")
    selected_model_id = _as_str(
        meta.get("llm_effective_model_id", meta.get("llm_model_used", requested_model_id)),
        requested_model_id,
    )
    final_model_id = _as_str(
        meta.get("llm_final_synthesis_model_id", meta.get("llm_model_used", selected_model_id)),
        selected_model_id,
    )
    llm_used = _as_bool(meta.get("llm_used", False))
    if not llm_used:
        requested_model_id = "not_used"
        preferred_model_id = "not_used"
        selected_model_id = "not_used"
        final_model_id = "not_used"

    explicit_downgrade = _as_bool(meta.get("llm_intermediate_downgrade_occurred", False))
    selected_different = (
        requested_model_id not in {"not_used", "n/a"}
        and selected_model_id not in {"not_used", "n/a"}
        and requested_model_id != selected_model_id
    )
    final_different = (
        selected_model_id not in {"not_used", "n/a"}
        and final_model_id not in {"not_used", "n/a"}
        and selected_model_id != final_model_id
    )
    downgrade_occurred = bool(llm_used and (explicit_downgrade or selected_different or final_different))
    downgrade_reason = _as_str(
        meta.get(
            "llm_intermediate_downgrade_reason",
            meta.get("llm_model_downgrade_reason", "n/a"),
        ),
        "n/a",
    )
    if downgrade_occurred and downgrade_reason == "n/a":
        downgrade_reason = "model_selection_changed"

    return ModelAdapterMetadata(
        contract_version=MODEL_ADAPTER_CONTRACT_VERSION,
        provider=provider,
        provider_class=_provider_class(provider),
        request_mode=_as_str(meta.get("llm_request_mode", "n/a")),
        execution_mode=_as_str(meta.get("execution_mode", "retrieval_only")),
        llm_intent=_as_str(meta.get("llm_intent", "none")),
        llm_used=llm_used,
        policy_allowed=_as_bool(meta.get("llm_policy_allowed", True)),
        requested_model_id=requested_model_id,
        preferred_model_id=preferred_model_id,
        selected_model_id=selected_model_id,
        final_model_id=final_model_id,
        model_family=_model_family(final_model_id),
        downgrade_occurred=downgrade_occurred,
        downgrade_reason=downgrade_reason,
        provider_http_status=_as_int_or_none(meta.get("llm_provider_http_status")),
        provider_error_type=_as_str(meta.get("llm_provider_error_type", "n/a")),
        execution_profile_requested=profile_requested,
        execution_profile_used=profile_used,
        execution_profile_reason_code=profile_reason_code,
        execution_profile_reason_short=profile_reason_short,
        budget_sensitivity=budget_sensitivity,
        latency_sensitivity=latency_sensitivity,
        profile_policy_outcome=profile_policy_outcome,
        profile_override_applied=profile_override_applied,
        profile_model_alignment=profile_model_alignment,
    )
