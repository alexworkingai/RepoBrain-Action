# TopoCore v6 Audit Scoring Contract

## 1. Purpose

This document defines the safe RepoBrain-side runtime contract between `RepoBrain-Action` and private `TopoCore v6` for deep audit scoring.

## 2. Boundary

- `RepoBrain-Action` never receives TopoCore source code.
- TopoCore v6 source remains private.
- This contract is a runtime and API boundary only.
- No TopoCore source-code license is granted through this contract.
- No public TopoCore distribution is implemented here.

## 3. Contract Version

- `topocore.audit_score.v1`

## 4. Request Schema

RepoBrain sends `AuditScoreRequestV1` with the following bounded fields:

- `contract_version`: `topocore.audit_score.v1`
- `repo_metadata`
  - `owner`
  - `repo`
  - `default_branch` if known
  - `event_type`
  - `is_pr`
  - `pr_number` if known
  - `head_sha` if known
- `audit_focus`
  - sanitized raw focus or query text
- `static_baseline`
  - `overall_score`
  - `readiness_band`
  - `category_scores`
  - `category_max_weights`
  - `confidence`
  - `limitations`
- `evidence_manifest`
  - bounded list of safe evidence items with:
    - `path`
    - `kind`
    - `reason`
    - `is_changed_file`
    - `safe_excerpt`
- `repo_signals`
  - `has_tests`
  - `has_ci`
  - `has_docs`
  - `has_release_files`
  - `has_security_policy`
  - `risky_permissions_detected`
  - `dependency_manifest_count`
  - `workflow_count`
  - `docs_count`
  - `test_file_count`
- `constraints`
  - `no_mutation: true`
  - `no_patch: true`
  - `no_branch_commit_pr: true`
  - `no_security_approval_claim: true`
  - `no_merge_approval_claim: true`
  - bounded response and output-size limits

## 5. Response Schema

TopoCore may return `AuditScoreResponseV1` with the following bounded fields:

- `contract_version`: `topocore.audit_score.v1`
- `status`
  - `ok`
  - `partial`
  - `unsupported`
  - `error_sanitized`
- `overall_score`: integer `0-100`
- `readiness_band`
  - `STRONG`
  - `GOOD`
  - `NEEDS_ATTENTION`
  - `WEAK`
- `category_scores`
  - same 10 categories
  - each includes:
    - `score`
    - `max`
    - `label`
    - `rationale`
    - `evidence_paths`
- `score_adjustments`
  - bounded list of category deltas with reasons and evidence
- `critical_blockers`
- `top_improvements`
- `roadmap`
  - `30_days`
  - `60_days`
  - `90_days`
- `confidence`
- `limitations`
- `safety`
  - `patch_authorized: false`
  - `patch_applied: false`
  - `files_modified: false`
  - `branch_created: false`
  - `commit_created: false`
  - `pr_created: false`
  - `no_security_approval: true`
  - `no_merge_approval: true`
- `diagnostics`
  - backend or model mode if applicable
  - capability version
  - sanitized warnings

## 6. Validation And Guardrails

RepoBrain-side validation rejects or downgrades responses that violate any of the following:

- score bounds must stay within documented limits
- category names and max weights must match the 10-category public scoring model
- overall score must stay within `0-100`
- readiness band mismatches are recorded as warnings
- evidence paths must be sanitized and bounded
- no `.topocore-v6` evidence
- no local machine paths
- no token values or private key material
- no raw stack traces
- no unsafe claims such as merge approval or security approval
- no patch or mutation authorization
- list sizes remain bounded

## 7. Failure Modes

The contract supports the following safe failure paths:

- capability unavailable
  - RepoBrain keeps static scoring and reports `audit_v6_capability_unavailable_static_scoring`
- invalid response
  - RepoBrain rejects the response and keeps static scoring with `audit_v6_contract_rejected_static_scoring`
- TopoCore import unavailable
  - RepoBrain keeps static scoring and does not claim `v6`
- permission or token issue
  - RepoBrain keeps static scoring and renders sanitized backend evidence only
- sanitized error
  - no raw traceback, no environment dump, no secret exposure

## 8. Backend Evidence Semantics

RepoBrain renders backend evidence in four honest modes:

- static mode
  - `resolved_backend=not_applicable`
  - `fallback_reason=audit_static_scoring`
- capability unavailable mode
  - `resolved_backend=not_applicable`
  - `fallback_reason=audit_v6_capability_unavailable_static_scoring`
- v6-enriched mode
  - `resolved_backend=v6`
  - `fallback_used=no`
  - `fallback_reason=none`
- rejected response mode
  - `resolved_backend=v6_rejected`
  - `fallback_reason=audit_v6_contract_rejected_static_scoring`

RepoBrain never reports `v6` unless the runtime actually invoked and accepted a valid `v6` audit response.

## 9. Security

- no source exposure
- no `.topocore-v6` evidence
- no environment dump
- no secret values
- no raw stack traces
- `private_checkout` remains beta-only
- no patch or autofix behavior is enabled by this contract

## 10. Implementation Status

- Sprint 81 implements the RepoBrain-side contract, request builder, response validator, optional capability seam, and output-mode handling.
- Sprint 82 adds a real private `run_audit_score_v1` provider behind the same contract without exposing TopoCore source through RepoBrain-Action.
- RepoBrain still treats static scoring as the fallback truth whenever the private capability is missing, invalid, or rejected by the contract guard.
- Sprint 82 live Elen-MCP smoke accepted the private response and rendered `v6-enriched scoring` with `resolved_backend=v6` and `fallback_reason=none`.
- Public distribution remains blocked by the separate TopoCore distribution strategy.
