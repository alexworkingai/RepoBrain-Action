from __future__ import annotations

from repobrain.llm.model_adapter_contract import (
    MODEL_ADAPTER_CONTRACT_VERSION,
    build_model_adapter_metadata,
)


def test_model_adapter_metadata_tracks_requested_selected_final_and_family() -> None:
    meta = build_model_adapter_metadata(
        {
            "llm_used": True,
            "llm_provider": "github_models",
            "llm_policy_allowed": True,
            "llm_request_mode": "normal",
            "execution_mode": "retrieval_plus_llm",
            "llm_intent": "review",
            "llm_primary_model_id": "openai/gpt-4.1",
            "llm_preferred_model_id": "openai/gpt-4.1",
            "llm_effective_model_id": "openai/gpt-4.1-mini",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
            "llm_intermediate_downgrade_occurred": True,
            "llm_intermediate_downgrade_reason": "quota_pressure",
            "llm_provider_http_status": 200,
            "llm_provider_error_type": "n/a",
        }
    )

    fields = meta.as_audit_fields()
    assert fields["llm_adapter_contract_version"] == MODEL_ADAPTER_CONTRACT_VERSION
    assert fields["llm_adapter_provider"] == "github_models"
    assert fields["llm_adapter_provider_class"] == "github_models_chat_completions"
    assert fields["llm_adapter_requested_model_id"] == "openai/gpt-4.1"
    assert fields["llm_adapter_selected_model_id"] == "openai/gpt-4.1-mini"
    assert fields["llm_adapter_final_model_id"] == "openai/gpt-4.1"
    assert fields["llm_adapter_model_family"] == "gpt-4.1"
    assert fields["llm_adapter_downgrade_occurred"] is True
    assert fields["llm_adapter_downgrade_reason"] == "quota_pressure"
    assert fields["llm_adapter_execution_profile_requested"] == "balanced"
    assert fields["llm_adapter_execution_profile_used"] == "balanced"
    assert fields["llm_adapter_execution_profile_reason_code"] == "profile_applied"
    assert fields["llm_adapter_profile_override_applied"] is False


def test_model_adapter_metadata_marks_not_used_path() -> None:
    meta = build_model_adapter_metadata(
        {
            "llm_used": False,
            "llm_provider": "github_models",
            "llm_primary_model_id": "openai/gpt-4.1",
            "llm_effective_model_id": "openai/gpt-4.1-mini",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
        }
    )
    fields = meta.as_audit_fields()
    assert fields["llm_adapter_llm_used"] is False
    assert fields["llm_adapter_requested_model_id"] == "not_used"
    assert fields["llm_adapter_selected_model_id"] == "not_used"
    assert fields["llm_adapter_final_model_id"] == "not_used"
    assert fields["llm_adapter_model_family"] == "not_used"
    assert fields["llm_adapter_downgrade_occurred"] is False


def test_model_adapter_metadata_uses_provider_hint_when_meta_provider_missing() -> None:
    meta = build_model_adapter_metadata(
        {
            "llm_used": True,
            "llm_primary_model_id": "openai/gpt-4.1",
            "llm_effective_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
        },
        provider_hint="github_models",
    )
    fields = meta.as_audit_fields()
    assert fields["llm_adapter_provider"] == "github_models"
    assert fields["llm_provider"] == "github_models"


def test_model_adapter_metadata_tracks_execution_profile_contract_fields() -> None:
    meta = build_model_adapter_metadata(
        {
            "llm_used": True,
            "llm_provider": "github_models",
            "llm_execution_profile_requested": "cheap",
            "llm_execution_profile_used": "balanced",
            "llm_execution_profile_reason_code": "cheap_guardrail_review_fix",
            "llm_execution_profile_reason_short": "Cheap profile requested; review/fix synthesis kept balanced profile for governed safety.",
            "llm_budget_sensitivity": "high",
            "llm_latency_sensitivity": "low",
            "llm_profile_policy_outcome": "guardrail_override_to_balanced",
            "llm_profile_override_applied": True,
            "llm_profile_model_alignment": "balanced_high_tier_selected",
            "llm_primary_model_id": "openai/gpt-4.1",
            "llm_effective_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
        }
    )
    fields = meta.as_audit_fields()
    assert fields["llm_adapter_execution_profile_requested"] == "cheap"
    assert fields["llm_adapter_execution_profile_used"] == "balanced"
    assert fields["llm_adapter_execution_profile_reason_code"] == "cheap_guardrail_review_fix"
    assert fields["llm_adapter_budget_sensitivity"] == "high"
    assert fields["llm_adapter_latency_sensitivity"] == "low"
    assert fields["llm_adapter_profile_policy_outcome"] == "guardrail_override_to_balanced"
    assert fields["llm_adapter_profile_override_applied"] is True
    assert fields["llm_adapter_profile_model_alignment"] == "balanced_high_tier_selected"
    assert fields["llm_execution_profile_used"] == "balanced"
