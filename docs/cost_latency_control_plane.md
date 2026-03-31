# Cost / Latency Control Plane v1

Sprint 57 introduces a narrow execution-profile policy layer for LLM execution.

## Scope

- Profiles: `cheap`, `balanced`, `premium`
- Canonical audit/evidence truth for profile request/use and policy reason
- No routing architecture redesign
- No primary PR UI surface expansion

## Canonical fields

Adapter-contract fields:

- `llm_adapter_execution_profile_requested`
- `llm_adapter_execution_profile_used`
- `llm_adapter_execution_profile_reason_code`
- `llm_adapter_execution_profile_reason_short`
- `llm_adapter_budget_sensitivity`
- `llm_adapter_latency_sensitivity`
- `llm_adapter_profile_policy_outcome`
- `llm_adapter_profile_override_applied`
- `llm_adapter_profile_model_alignment`

Compatibility aliases:

- `llm_execution_profile_requested`
- `llm_execution_profile_used`
- `llm_execution_profile_reason_code`
- `llm_execution_profile_reason_short`
- `llm_budget_sensitivity`
- `llm_latency_sensitivity`
- `llm_profile_policy_outcome`
- `llm_profile_override_applied`
- `llm_profile_model_alignment`

## Environment controls

- `RB_LLM_EXECUTION_PROFILE` = `cheap|balanced|premium` (default: `balanced`)
- `RB_LLM_BUDGET_SENSITIVITY` = `low|normal|high|not_available` (default: `not_available`)
- `RB_LLM_LATENCY_SENSITIVITY` = `low|normal|high|not_available` (default: `not_available`)

## Semantics

- `balanced` is the default profile and preserves existing behavior.
- `cheap` prefers lower-tier model selection when safe.
- `premium` prefers high-tier model selection for retrieval-plus-LLM execution.
- Review/fix guardrail: `cheap` is normalized to `balanced` for governed safety in review/fix synthesis.

Profiles are policy intents, not hard guarantees of a specific provider/model.

## Auditability

Evidence Pack exports profile decision truth via:

- `execution_summary` (requested/used profile and policy reason)
- `model_summary` (profile policy outcome and model-alignment status)

If a field is not canonically available, the runtime keeps explicit bounded defaults (`n/a`, `not_available`, etc.) rather than synthesizing values.
