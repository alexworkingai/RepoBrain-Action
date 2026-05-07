# Sprint 0 Repo Boundary Inventory

## Purpose

This Sprint 0 document is a read-only repository-boundary inventory for `RepoBrain-Action` after the public external runtime responsibility moved to `repobrain-community`.

This sprint does not delete, move, or rewrite runtime code. It records what appears still required here, what appears duplicated, what appears stale, and what likely belongs in another repository.

## Current Repository Role Summary

### RepoBrain-Action

Current practical role after Sprint 78:

- historical/core repository for the primary GitHub mode runtime
- ownership of `action.yml`, local/runtime Python packages, governance logic, TKYA/TopoCore contracts, readiness tooling, and regression tests
- home of current-truth cross-repo docs such as capability matrix, user/operator guides, packaging boundaries, and governance references
- owner of the external CLI ask-only surface (`scripts/run_github.py --mode external`, `repobrain.external_flow`)

### repobrain-community

Current practical role after Sprint 78:

- public runtime host for external GitHub foundation
- reusable GitHub workflow host
- public install kit and templates
- public README/examples/community onboarding
- canonical live surface for `/repobrain doctor`, `/repobrain help`, `/repobrain ask ...`, `/repobrain review`, `/repobrain fix`

### elen-mcp-prod_v2

Current practical role after Sprint 78:

- third-party validation repository
- live validation PR surface
- repo-local guidance and validation-marker content
- place where public-host behavior is exercised on real PRs

## Current Public Command Truth After Sprint 78

Supported external GitHub foundation command meanings:

- `/repobrain doctor` = bounded setup health card
- `/repobrain help` = command truth and boundaries
- `/repobrain ask <question>` = repo/PR/guidance-aware bounded answer
- `/repobrain review` = bounded read-only Review Candidate
- `/repobrain fix` = bounded Fix-Lite Candidate manual-only patch suggestion

Mandatory non-claims that remain true:

- no autofix
- no patch application
- no file modification
- no commit creation
- no branch pushing
- no PR creation
- no full review parity
- no security verdict
- no safe-to-merge claim
- no approval/rejection verdict
- no autonomous repair behavior

## Areas Inspected In RepoBrain-Action

Root and packaging surface:

- `README.md`
- `pyproject.toml`
- `action.yml`
- `.repobrain.yml`

Workflow surface:

- `.github/workflows/repobrain.yml`
- `.github/workflows/repobrain_external_foundation.yml`
- `.github/workflows/repobrain_comment_post_test.yml`
- `.github/workflows/repobrain_local_test.yml`
- `.github/workflows/repobrain_remote_stub_test.yml`
- supporting CI/check workflows by listing

Runtime / script surface:

- `repobrain/external_flow.py`
- `scripts/run_github.py`
- `scripts/check_install_readiness.py`
- broader `repobrain/` and `scripts/` trees by listing for ownership context

Documentation surface reviewed directly:

- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`
- `docs/packaging/repobrain_external_github_foundation_template.yml`
- `docs/packaging/INSTALLATION_SHAPE.md`
- `docs/packaging/VALIDATION_CHECKLIST.md`
- `docs/packaging/PREFLIGHT_CHECKLIST.md`
- `docs/benchmarks/current_capabilities_matrix.md`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- `docs/trials/external_repo_trial_01_elen_mcp.md`
- `docs/startup/READINESS_MATRIX.md`
- `docs/startup/STARTUP_READINESS.md`
- `docs/startup/EXTERNAL_EVALUATION_PATH.md`
- `docs/startup/EVALUATOR_GUIDE.md`
- `docs/strategy/PROVEN_CAPABILITIES_SUMMARY.md`
- `docs/repobrain_template.yml`
- `docs/onboarding/github_app_setup.md`
- `docs/onboarding/permissions.md`

Test surface reviewed directly:

- `tests/test_external_github_foundation_workflow.py`
- `tests/test_external_flow.py`
- `tests/test_install_readiness.py`
- `tests/test_retrieval_snapshot_workflow_cache.py`

## Classification Summary

### KEEP

#### 1. Primary GitHub mode runtime and action packaging

Paths / areas:

- `action.yml`
- `.github/workflows/repobrain.yml`
- `repobrain/`
- `scripts/run_github.py`

Reason:

- This is still the primary runtime surface owned by `RepoBrain-Action`.
- The main GitHub mode runtime, composite action packaging, audit/evidence generation, patch governance, and TKYA/TopoCore contracts are still centered here.

Risk of changing/removing:

- High. This would directly affect the primary runtime and break current acceptance guarantees.

Suggested next sprint if action is needed:

- None in refactor phase unless there is a separate runtime-design sprint with dedicated acceptance scope.

#### 2. External CLI ask-only surface

Paths / areas:

- `repobrain/external_flow.py`
- external branch inside `scripts/run_github.py`
- `tests/test_external_flow.py`

Reason:

- The CLI external mode remains explicitly owned here and still has a distinct contract from the public GitHub foundation host.

Risk of changing/removing:

- Medium to high. It would erase the ask-only external CLI path that current docs and tests still rely on.

Suggested next sprint if action is needed:

- Separate external-CLI strategy sprint, not Sprint 0.

#### 3. Readiness tooling and onboarding contract

Paths / areas:

- `scripts/check_install_readiness.py`
- `docs/onboarding/github_app_setup.md`
- `docs/onboarding/permissions.md`
- `tests/test_install_readiness.py`
- readiness generation portions inside `.github/workflows/repobrain.yml`

Reason:

- This is still core shared governance/onboarding logic, even though `repobrain-community` has its own self-contained public host implementation.
- The readiness contract is also used by the primary runtime/operator path here.

Risk of changing/removing:

- High. It would break operator onboarding and regression coverage.

Suggested next sprint if action is needed:

- Only consider extraction if there is an explicit shared-library plan across repos.

#### 4. Governance, TKYA, TopoCore, capability matrix, and regression tests

Paths / areas:

- `docs/governance/`
- `docs/tkya_contract.md`
- `docs/tkya_evidence_pack.md`
- `docs/topocore_v5_architecture.md`
- `docs/topocore_v5_complete_guide.md`
- `docs/benchmarks/current_capabilities_matrix.md`
- broad regression suites in `tests/`

Reason:

- These are part of the historical/core repository role and still belong here.

Risk of changing/removing:

- High. These are cross-cutting contracts and regression anchors.

Suggested next sprint if action is needed:

- None for movement. Only truth-alignment cleanups as needed.

### MOVE_TO_REPOBRAIN_COMMUNITY_CANDIDATE

#### 1. Public external GitHub foundation template copy

Path:

- `docs/packaging/repobrain_external_github_foundation_template.yml`

Reason:

- This file is public install-kit material and points directly at `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`.
- Canonical public onboarding already lives in `repobrain-community/templates/repobrain.yml`.

Risk of changing/removing:

- Medium. Docs/tests inside `RepoBrain-Action` reference this path today.

Suggested next sprint if action is needed:

- Sprint 1 boundary cleanup: either move ownership to `repobrain-community` and leave only a reference link here, or keep a generated snapshot with explicit non-canonical labeling.

#### 2. Public external GitHub foundation runbook

Path:

- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`

Reason:

- This is effectively public install/runbook material for the community-hosted external GitHub surface.
- It may still be useful here as cross-repo documentation, but ownership looks closer to `repobrain-community`.

Risk of changing/removing:

- Medium. Referenced by README, user guide, and operator docs.

Suggested next sprint if action is needed:

- Sprint 1 boundary cleanup with human decision: either migrate canonical install/runbook content to `repobrain-community` and retain only a boundary/overview doc here, or explicitly mark this copy as secondary.

### MOVE_TO_VALIDATION_REPO_CANDIDATE

#### 1. Live validation repo-specific trial runbook

Path:

- `docs/trials/external_repo_trial_01_elen_mcp.md`

Reason:

- This file is tied to a specific third-party validation repository and an older trial protocol.
- It is operationally closer to the validation repo than to the long-term core role of `RepoBrain-Action`.

Risk of changing/removing:

- Low to medium. Historical context may still matter, but canonical live validation instructions likely belong with the validation surface.

Suggested next sprint if action is needed:

- Sprint 1 validation-surface cleanup: migrate active validation instructions to `elen-mcp-prod_v2` or archive here as historical-only.

#### 2. Live validation narrative/report for Elen-MCP trial

Path:

- `docs/benchmarks/external_trial_01_elen_mcp_report.md`

Reason:

- This is a repo-specific external trial artifact with stale Sprint 59 truth.
- It belongs more naturally with validation evidence/archive than with current public/core truth.

Risk of changing/removing:

- Low to medium. Useful historically, but hazardous if treated as current truth.

Suggested next sprint if action is needed:

- Sprint 1 validation archival cleanup: move to validation-repo archive or mark historical/obsolete here.

### DELETE_CANDIDATE

#### 1. Legacy duplicated external foundation runtime workflow

Path:

- `.github/workflows/repobrain_external_foundation.yml`

Reason:

- This workflow is an old ask-only/unsupported-copy implementation inside `RepoBrain-Action`.
- Public external runtime responsibility moved to `repobrain-community`, which now hosts the canonical reusable workflow.
- Keeping this file in `RepoBrain-Action` creates a strong stale/duplicate surface risk.

Risk of changing/removing:

- Medium to high. Remove only after confirming no internal process still relies on it for historical/manual checks.

Suggested next sprint if action is needed:

- Sprint 1 duplicate-runtime cleanup with explicit verification that no internal workflows/docs still rely on this legacy file.

#### 2. Old direct-action workflow template snapshot

Path:

- `docs/repobrain_template.yml`

Reason:

- This template still uses placeholder `OWNER/REPO@v0.1.0` action wiring and does not match the canonical public install shape through `repobrain-community`.
- It reads like a superseded install artifact rather than a required current surface.

Risk of changing/removing:

- Medium. If any docs still intentionally reference it as a non-public example, that needs to be clarified first.

Suggested next sprint if action is needed:

- Sprint 1 packaging cleanup: delete if confirmed unreferenced, otherwise relabel clearly as historical/internal-only.

### NEEDS_HUMAN_DECISION

#### 1. Operator/startup/packaging docs that still serve as cross-repo summaries but contain stale truth

Paths / areas:

- `docs/OPERATOR_QUICKSTART.md`
- `docs/packaging/INSTALLATION_SHAPE.md`
- `docs/packaging/VALIDATION_CHECKLIST.md`
- `docs/packaging/PREFLIGHT_CHECKLIST.md`
- `docs/startup/READINESS_MATRIX.md`
- `docs/startup/STARTUP_READINESS.md`
- `docs/startup/EXTERNAL_EVALUATION_PATH.md`
- `docs/startup/EVALUATOR_GUIDE.md`
- `docs/strategy/PROVEN_CAPABILITIES_SUMMARY.md`

Reason:

- These are not obviously public-runtime host assets, so they may still belong in `RepoBrain-Action`.
- But many of them still describe external review/fix as unsupported or ask-only.
- The issue is not simple deletion; it is deciding whether to refresh, archive, or split current-truth from historical-stage documentation.

Risk of changing/removing:

- Medium to high. These docs are cross-referenced and may still be used for operator/strategy context.

Suggested next sprint if action is needed:

- Sprint 1 truth-freeze cleanup with explicit archival policy for historical startup/trial docs.

#### 2. External foundation doc tests in RepoBrain-Action

Paths / areas:

- `tests/test_external_github_foundation_workflow.py`

Reason:

- The test is currently validating documentation/template truth rather than runtime code in this repo.
- That is still useful, but ownership should be revisited if canonical public examples move fully into `repobrain-community`.

Risk of changing/removing:

- Medium. Removing too early would lose boundary-regression coverage.

Suggested next sprint if action is needed:

- Sprint 1 or 2: decide whether these tests should remain as cross-repo contract checks or move to a docs-sync/validation strategy.

## Top Boundary Conclusions

1. `RepoBrain-Action` should continue to own primary runtime code, governance, readiness logic, TKYA/TopoCore contracts, and regression coverage.
2. The canonical public external GitHub foundation host and install kit clearly belong in `repobrain-community`.
3. `RepoBrain-Action` still contains duplicated or stale public external-surface material, especially one legacy workflow and multiple stale docs.
4. Validation-repo-specific runbooks and trial narratives are poor fits for long-term core ownership if they continue to drift from current public truth.
5. The highest-risk cleanup items are not runtime Python files; they are duplicated workflows/templates and stale docs that can misstate the accepted public boundary.
