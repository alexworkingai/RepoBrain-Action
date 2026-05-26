# Structural Maintainability Plan

## Current Hotspot Table

| Module | Approximate size | Risk |
|---|---:|---|
| `repobrain/github_flow.py` | 9000+ lines | orchestration concentration, policy drift risk, harder review surface |
| `repobrain/output_md.py` | 3000+ lines | rendering concentration, formatting regression risk |
| `repobrain/audit_scoring.py` | 1000+ lines | scoring logic density, calibration coupling |
| `repobrain/config.py` | 1000+ lines | config sprawl and accidental policy complexity |
| `repobrain/topocore_v6_adapter.py` | 900+ lines | boundary-layer complexity and failure-mode concentration |

## Why Each Hotspot Is Risky

Large modules increase:

- review difficulty
- accidental behavior coupling
- harder policy verification
- slower onboarding
- higher regression risk near release/public-switch gates

## Safe Decomposition Order

1. `github_flow.py`
2. `output_md.py`
3. `topocore_v6_adapter.py`
4. `audit_scoring.py`
5. `config.py`

## No Behavior-Change Principle

Refactors should:

- preserve command routing
- preserve audit/score backend evidence
- preserve no-mutation behavior
- preserve output truth
- land with targeted regression tests

## Proposed Module Boundaries

Possible low-risk future splits:

- `github_flow.py`
  - command routing
  - runtime evidence assembly
  - publication helpers
  - permission/runtime summaries
- `output_md.py`
  - audit renderer
  - score renderer
  - doctor/status renderer
  - shared evidence/safety cards
- `topocore_v6_adapter.py`
  - capability detection
  - runtime mode resolution
  - contract invocation
  - diagnostics helpers
- `audit_scoring.py`
  - inventory scan
  - category scoring
  - blockers/improvements synthesis
- `config.py`
  - env specs
  - config loading
  - policy defaults

## Test Strategy

- freeze current behavior with focused tests before extraction
- move one helper/module boundary at a time
- re-run full validation after each extraction wave

## Thresholds And Warnings

Suggested warning thresholds:

- 800+ lines: warn
- 1500+ lines: high-priority decomposition candidate
- 3000+ lines: critical maintainability hotspot

## Sprint 87/88 Refactor Candidates

- extract shared runtime/safety cards from `output_md.py`
- extract non-routing helpers from `github_flow.py`
- split `topocore_v6_adapter.py` into runtime-mode and contract modules
- isolate config/env policy tables from behavior logic
