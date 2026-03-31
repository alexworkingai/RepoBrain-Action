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
            # Canonical aliases for non-adapter consumers.
            "llm_provider": self.provider,
            "llm_model_family": self.model_family,
            "llm_model_requested_id": self.requested_model_id,
            "llm_model_selected_id": self.selected_model_id,
            "llm_model_final_id": self.final_model_id,
        }


def _provider_class(provider: str) -> str:
    lowered = provider.lower()
    if lowered == "github_models":
        return "github_models_chat_completions"
    if lowered in {"openai", "azure_openai"}:
        return "openai_compatible"
    return "unknown"


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
    )
