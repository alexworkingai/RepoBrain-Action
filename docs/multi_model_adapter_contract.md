# Multi-Model Adapter Contract v1

This document defines RepoBrain's canonical model/provider metadata contract for runtime, audit, and evidence export.

## Scope

Sprint 56 introduces a **narrow adapter contract** for model identity and downgrade truth.
It does not introduce a new routing engine.

## Contract ID

- `llm_model_adapter_v1`

## Canonical audit fields

- `llm_adapter_contract_version`
- `llm_adapter_provider`
- `llm_adapter_provider_class`
- `llm_adapter_request_mode`
- `llm_adapter_execution_mode`
- `llm_adapter_intent`
- `llm_adapter_llm_used`
- `llm_adapter_policy_allowed`
- `llm_adapter_requested_model_id`
- `llm_adapter_preferred_model_id`
- `llm_adapter_selected_model_id`
- `llm_adapter_final_model_id`
- `llm_adapter_model_family`
- `llm_adapter_downgrade_occurred`
- `llm_adapter_downgrade_reason`
- `llm_adapter_provider_http_status`
- `llm_adapter_provider_error_type`

Canonical compatibility aliases are also emitted:

- `llm_provider`
- `llm_model_family`
- `llm_model_requested_id`
- `llm_model_selected_id`
- `llm_model_final_id`

## Semantics

- **requested**: primary model requested by runtime policy.
- **selected**: effective model selected for generation.
- **final**: final synthesis model reflected in output/audit.
- **model_family**: stable normalized family derived from final model id.
- **downgrade_occurred**: true when selected/final differ from requested or explicit downgrade is recorded.

If LLM is not used, model-id fields are `not_used`.

## Public-safe behavior

Evidence Pack public-safe output includes adapter summary fields and excludes raw prompt/candidate/diff content.
