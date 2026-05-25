# Sprint 81 Deep v6 Audit Scoring Contract

## 1. Purpose

Sprint 81 defines and implements the safe v6 audit scoring contract on the RepoBrain side.
It follows Sprint 80 benchmark and demo readiness work.
It does not expose TopoCore source code or change TopoCore distribution strategy.

## 2. Baseline

- latest main before Sprint 81:
  - `1025619 Record audit benchmark live evidence`
- Sprint 80 status:
  - `AUDIT_BENCHMARK_DEMO_READY`
- current limitation before Sprint 81:
  - audit remained a static MVP scorer
  - backend resolved `not_applicable`
  - fallback reason `audit_static_scoring`

## 3. Contract Design

- contract name:
  - `topocore.audit_score.v1`
- request schema:
  - static baseline score, categories, confidence, limitations, sanitized focus, bounded evidence manifest, repo signals, and hard no-mutation constraints
- response schema:
  - bounded overall score, category scores, adjustments, blockers, improvements, roadmap, confidence, limitations, safety flags, and sanitized diagnostics
- guardrails:
  - score and category bounds
  - category-set validation
  - no secret values
  - no `.topocore-v6` evidence
  - no local machine paths
  - no raw stack traces
  - no patch or mutation claims
  - no merge or security approval claims

## 4. Implementation Summary

Files changed in the RepoBrain runtime path:

- `repobrain/audit_contract.py`
- `repobrain/audit_v6.py`
- `repobrain/github_flow.py`
- `repobrain/output_md.py`
- `repobrain/topocore_v6_adapter.py`
- `scripts/probe_topocore_v6_contract.py`

Main implementation pieces:

- request builder:
  - builds `AuditScoreRequestV1` from the static audit baseline and bounded evidence
- response validator:
  - validates contract version, category set, score bounds, safety flags, and unsafe-content guardrails
- optional capability seam:
  - uses `run_audit_score_v1(request)` only when the facade actually exposes it
- output modes:
  - static scoring MVP
  - static scoring with v6 contract-ready guard
  - static scoring with rejected v6 response
  - v6-enriched scoring
- probe update:
  - contract probe now reports whether `audit_score_v1` capability is present

## 5. Test Coverage

Sprint 81 adds coverage for:

- request builder shape and sanitization
- response validation and rejection cases
- fake v6 integration for valid enriched responses
- honest fallback when capability is unavailable
- honest rejection when a v6 response violates contract bounds
- backend evidence truth across static, capability-unavailable, rejected, and v6-enriched modes
- docs and index updates for the new contract surface

## 6. External Live Result

- issue URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/28`
- run URL:
  - audit: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26392391412`
  - doctor: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26392392231`
  - status: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26392393618`
- conclusion:
  - audit: `success`
  - doctor: `success`
  - status: `success`
- audit mode:
  - `static scoring with v6 contract-ready guard`
- score:
  - `78 / 100`
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `not_applicable`
  - fallback used: `not_applicable`
  - fallback reason: `audit_v6_capability_unavailable_static_scoring`
- safety result:
  - no mutation
  - no patch/autofix
  - no secret exposure
  - no private checkout evidence surfaced
  - doctor result: `PASS`
  - status result: `success`

## 7. TopoCore v6 Capability Status

- `REAL_V6_AUDIT_CAPABILITY_NOT_AVAILABLE`

## 8. Product Status

- `V6_AUDIT_CONTRACT_READY_STATIC_RUNTIME`

## 9. Next Step

If the contract is ready but real private capability is absent:

- Sprint 82 - Implement private TopoCore v6 audit scoring capability or adapter-side provider

If live `v6` enrichment proves real and stable:

- Sprint 82 - Audit Score alias and v6 audit UX hardening

Recommended preference:

- Sprint 82 - Implement private TopoCore v6 audit scoring capability or adapter-side provider

## 10. Non-Goals

- no v5
- no repobrain-community
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no public TopoCore distribution
- no TopoCore source changes unless explicitly approved
- no Microsoft partnership claim
