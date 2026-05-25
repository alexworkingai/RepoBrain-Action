# Sprint 79 - Audit Calibration And Doctor/Status Diagnostics

## 1. Purpose

Sprint 79 calibrates the `/repobrain audit` MVP and implements `/repobrain doctor` and `/repobrain status`.
It follows Sprint 78 audit MVP work.
It does not change runtime policy or enable mutation.

## 2. Baseline

- latest `main` before Sprint 79:
  - `1920ef5 Record audit MVP live evidence`
- Sprint 78 status:
  - `AUDIT_MVP_PASSED`
- known Sprint 78 gaps:
  - audit calibration
  - cleaner UX
  - doctor/status not implemented
  - score roadmap-only

## 3. Audit Calibration

- calibration changes:
  - expanded generated/private/runtime directory exclusions
  - embedded config detection in manifests improves code-quality calibration
  - audit anchors and requested-focus rendering were compacted to avoid duplication
- excluded dirs:
  - `.topocore-v6/`
  - `.codex-skill-install-tmp/`
  - `.venv/`, `venv/`
  - `node_modules/`
  - `dist/`
  - `build/`
  - `.pytest_cache/`
  - `__pycache__/`
  - `.mypy_cache/`
  - `.ruff_cache/`
  - `artifacts/`
  - `reports/`
- scoring adjustments:
  - pyproject/package-manifest embedded lint/type/format config now counts
  - hidden/private/generated paths do not contribute evidence or score
- output UX changes:
  - one requested-focus line
  - one runtime diagnostics block
  - shorter audit-anchor block
- no overfitting:
  - calibration was based on deterministic heuristic gaps and evidence-boundary fixes, not Elen-MCP-specific score targeting

## 4. Status Command

- command behavior:
  - `/repobrain status`
  - `/repobrain status <optional note>`
- supported scopes:
  - issue: supported
  - PR: supported
- output sections:
  - version/context summary
  - supported command surface
  - backend policy
  - workflow snapshot
  - safety policy
  - install hints
  - runtime/safety anchors
- backend report-only reason:
  - `status_report_only`
- safety:
  - informational only
  - no mutation
  - no secret exposure

## 5. Doctor Command

- command behavior:
  - `/repobrain doctor`
  - `/repobrain doctor <optional focus>`
- supported scopes:
  - issue: supported
  - PR: supported
- diagnostic checks:
  - workflow/action context
  - permissions baseline
  - TopoCore v6 setup hints
  - backend policy
  - command surface
  - fork/private boundary policy
- status labels:
  - `PASS`
  - `WARN`
  - `FAIL`
  - `UNKNOWN`
- limitations:
  - report-only diagnostics
  - no secret/env dump
  - no direct private-checkout replay
- backend report-only reason:
  - `doctor_diagnostic_report`
- safety:
  - informational only
  - no mutation
  - no secret exposure

## 6. Help / Command Surface

- supported commands after Sprint 79:
  - `/repobrain help`
  - `/repobrain ask`
  - `/repobrain locate`
  - `/repobrain explain`
  - `/repobrain review`
  - `/repobrain verify`
  - `/repobrain fix`
  - `/repobrain audit`
  - `/repobrain doctor`
  - `/repobrain status`
- unsupported/roadmap:
  - `/repobrain score`
- fix-lite guidance:
  - `fix-lite is not a product command. Use /repobrain fix.`

## 7. Unit Test Coverage

- audit calibration tests:
  - exclusion boundaries
  - read-mostly workflow calibration
  - no duplicated focus/runtime sections
- doctor tests:
  - parser
  - issue/PR support
  - token-name-safe rendering
  - no env dump
- status tests:
  - parser
  - issue/PR support
  - version/policy rendering
  - no secret exposure
- docs tests:
  - command guide
  - install/troubleshooting references
  - Sprint 79 doc/index coverage
- safety tests:
  - report-only backend markers
  - no mutation markers
  - no v5 fallback

## 8. External Live Results

Issue audit:

- pending live evidence after merge to `main`

Issue doctor:

- pending live evidence after merge to `main`

Issue status:

- pending live evidence after merge to `main`

Optional PR results:

- pending / not yet run

## 9. Defects / Gaps

- fixed now:
  - audit duplicate focus/runtime presentation
  - narrow exclusion boundary list
  - missing doctor command
  - missing status command
- deferred:
  - `/repobrain score`
  - deeper v6-backed scoring
  - benchmark-grade calibration suite
- blockers:
  - none yet recorded before live validation

## 10. Product Status

- pending final live validation

## 11. Next Step

If Sprint 79 passes, recommend:

- Sprint 80 - Audit Benchmark And Microsoft/GitHub Demo Report

## 12. Non-Goals

- no `v5`
- no `repobrain-community`
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no public TopoCore distribution implementation
- no `/repobrain score` implementation
