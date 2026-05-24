# Sprint 78 - Audit MVP 100-Point Scoring

## 1. Purpose

Sprint 78 implements `/repobrain audit` as the first flagship repository-intelligence and 100-point scoring command.
It follows Sprint 77 product positioning and scoring-roadmap work.
It does not change runtime policy or enable mutation.

## 2. Baseline

- latest `main` before Sprint 78:
  - `0e96e1d Resolve public scrub license and TopoCore security gate`
- Sprint 77 status:
  - `PRIVATE_BETA_RC_CONFIRMED`
  - `PUBLIC_BLOCKED_BY_DISTRIBUTION_STRATEGY`
  - `TOPOCORE_SECURITY_POLICY_ADOPTED`

## 3. Audit Product Contract

- command spelling:
  - `/repobrain audit`
  - `/repobrain audit <focus>`
- supported scopes:
  - issue / repository context: supported
  - PR context: supported as repository audit with PR context included
- required output sections:
  - executive summary
  - overall score
  - category breakdown
  - critical blockers
  - top improvements
  - 30/60/90-day roadmap
  - evidence summary
  - confidence and limitations
  - runtime and safety diagnostics
- no-mutation promise:
  - `patch_authorized=false`
  - `patch_applied=false`
  - `files_modified=false`
  - `branch_created=false`
  - `commit_created=false`
  - `pr_created=false`
- status:
  - informational only
  - not merge approval
  - not security approval

## 4. Scoring Model

- category weights:
  - Architecture and modularity: 15
  - Code quality and maintainability: 12
  - Testing and validation: 12
  - Security posture: 12
  - CI/CD and automation: 10
  - Dependency hygiene: 8
  - Documentation and onboarding: 8
  - Release and operations readiness: 8
  - GitHub governance: 8
  - AI-readiness / repository intelligence: 7
- total:
  - `100`
- readiness bands:
  - `85-100 STRONG`
  - `70-84 GOOD`
  - `50-69 NEEDS_ATTENTION`
  - `0-49 WEAK`
- confidence model:
  - `high`
  - `medium`
  - `low`
- limitation model:
  - sampled evidence
  - no runtime execution performed
  - missing tests/CI/docs
  - PR context used only as repository-level supplemental evidence

## 5. Implementation Summary

- files added/changed:
  - command parser: `repobrain/commands.py`
  - scoring module: `repobrain/audit_scoring.py`
  - GitHub route: `repobrain/github_flow.py`
  - output renderer: `repobrain/output_md.py`
- route/parser:
  - `/repobrain audit` added as a supported command
- scoring module:
  - deterministic, bounded, repository-static MVP
  - no LLM-only scoring
  - category totals bounded to 100
- output renderer:
  - compact GitHub-comment-safe scorecard
  - evidence, blockers, improvements, roadmap, confidence, diagnostics, safety
- backend evidence behavior:
  - requested backend stays explicit
  - resolved backend remains honest
  - no `v5` fallback
  - no `repobrain-community`

## 6. Unit Test Coverage

- scoring tests:
  - category weights
  - score bounds
  - strong vs sparse fixture comparison
  - dangerous workflow penalty
  - missing tests/docs impact
- command routing tests:
  - `/repobrain audit`
  - `/repobrain audit <focus>`
  - issue support
  - PR-context support
  - help output truth
  - unsupported score/doctor/status/fix-lite truth
- output tests:
  - overall score
  - all categories
  - blockers and improvements
  - roadmap
  - evidence summary
  - backend diagnostics
  - no-mutation statement
- safety tests:
  - no patch
  - no branch/commit/PR creation
  - no v5 fallback
- docs tests:
  - command guide update
  - scoring model update
  - release notes update
  - test coverage index update

## 7. External Live Audit Result

Issue audit:

- issue URL:
  - pending live run
- run URL:
  - pending live run
- conclusion:
  - pending live run
- score:
  - pending live run
- readiness band:
  - pending live run
- backend requested/resolved:
  - pending live run
- fallback:
  - pending live run
- evidence count:
  - pending live run
- safety result:
  - pending live run

PR audit:

- PR URL:
  - pending live run or explicit deferral
- run URL:
  - pending live run or explicit deferral
- conclusion:
  - pending live run or explicit deferral
- PR metadata used:
  - pending live run or explicit deferral
- score:
  - pending live run or explicit deferral
- safety:
  - pending live run or explicit deferral

## 8. Defects / Gaps

- fixed now:
  - audit route and parser gap
  - no real repository scoring command existed before Sprint 78
  - roadmap-only positioning is now backed by an MVP command
- deferred:
  - `/repobrain score`
  - `/repobrain doctor`
  - `/repobrain status`
  - v6-backed deeper audit calibration
- blockers:
  - none recorded yet before local validation and live run

## 9. Product Status

- pending final classification:
  - `AUDIT_MVP_PASSED`
  - `AUDIT_MVP_PARTIAL`
  - `BLOCKED_ON_AUDIT_ROUTING`
  - `BLOCKED_ON_SCORING_MODEL`
  - `BLOCKED_ON_V6_BACKEND`
  - `BLOCKED_ON_EXTERNAL_LIVE_RUN`

## 10. Next Step

If Sprint 78 passes, recommend:

- Sprint 79 - Audit Calibration and Doctor/Status Diagnostics

or

- Sprint 79 - Implement `/repobrain doctor` and `/repobrain status`

## 11. Non-Goals

- no `v5`
- no `repobrain-community`
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no public TopoCore distribution implementation
