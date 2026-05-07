# Stale External Surface Candidates

This file records current-stale, duplicated, or boundary-confusing external-surface candidates found in `RepoBrain-Action` during Refactor Sprint 0.

It is inventory only. No runtime behavior was changed here.

## 1. Legacy Reusable External Runtime Workflow Candidate

### Candidate

- `.github/workflows/repobrain_external_foundation.yml`

### Why it is stale or boundary-confusing

- `RepoBrain-Action` no longer owns the canonical public external GitHub foundation runtime.
- The file still contains an older ask-only command boundary and direct `RepoBrain-Action` runtime invocation.

### Evidence snippets

- `.github/workflows/repobrain_external_foundation.yml:52`
  - `if [[ "$cmd" == "help" || "$cmd" == "ask" ]]; then`
- `.github/workflows/repobrain_external_foundation.yml:91`
  - `RepoBrain external GitHub mode foundation currently supports only `/repobrain help` and `/repobrain ask`.`
- `.github/workflows/repobrain_external_foundation.yml:128`
  - `uses: alexworkingai/RepoBrain-Action@main`

### Suggested classification

- `DELETE_CANDIDATE`

## 2. Old Direct Action Template Candidate

### Candidate

- `docs/repobrain_template.yml`

### Why it is stale or boundary-confusing

- This template points to a direct published action placeholder instead of the accepted public community host.
- It does not match the canonical community install kit shape.

### Evidence snippets

- `docs/repobrain_template.yml:37`
  - `# Replace OWNER/REPO with your published action repository.`
- `docs/repobrain_template.yml:38`
  - `uses: OWNER/REPO@v0.1.0`

### Suggested classification

- `DELETE_CANDIDATE`

## 3. Community-Owned Install Template Copy Candidate

### Candidate

- `docs/packaging/repobrain_external_github_foundation_template.yml`

### Why it is stale or boundary-confusing

- This is public install-kit material, but the canonical install template now lives in `repobrain-community/templates/repobrain.yml`.
- Keeping a second template copy in `RepoBrain-Action` increases sync burden.

### Evidence snippets

- `docs/packaging/repobrain_external_github_foundation_template.yml:36`
  - `uses: alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`
- `tests/test_external_github_foundation_workflow.py:7`
  - `template = Path("docs/packaging/repobrain_external_github_foundation_template.yml")...`

### Suggested classification

- `MOVE_TO_REPOBRAIN_COMMUNITY_CANDIDATE`

## 4. Public External Foundation Runbook Candidate

### Candidate

- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`

### Why it is stale or boundary-confusing

- This file documents the public community-hosted external install/runbook surface.
- It may still be useful here as a boundary reference, but ownership looks closer to `repobrain-community`.

### Evidence snippets

- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md:28`
  - `reusable host: alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`

### Suggested classification

- `MOVE_TO_REPOBRAIN_COMMUNITY_CANDIDATE`

## 5. Stale Current-Truth Packaging Doc: Installation Shape

### Candidate

- `docs/packaging/INSTALLATION_SHAPE.md`

### Why it is stale

- It still says external GitHub mode foundation supports only help/ask and that review/fix are unsupported.
- That contradicts accepted Sprint 78 truth.

### Evidence snippets

- `docs/packaging/INSTALLATION_SHAPE.md:23`
  - `Current supported commands:`
- `docs/packaging/INSTALLATION_SHAPE.md:24-25`
  - `/repobrain help`
  - `/repobrain ask ...`
- `docs/packaging/INSTALLATION_SHAPE.md:28-29`
  - `Current unsupported commands:`
  - `/repobrain review`
  - `/repobrain fix`

### Suggested classification

- `NEEDS_HUMAN_DECISION`

## 6. Stale Current-Truth Packaging Doc: Validation Checklist

### Candidate

- `docs/packaging/VALIDATION_CHECKLIST.md`

### Why it is stale

- It still requires review/fix to block explicitly in the external GitHub mode foundation path.

### Evidence snippets

- `docs/packaging/VALIDATION_CHECKLIST.md:25-29`
  - `External GitHub mode foundation`
  - `1. /repobrain help succeeds ...`
  - `2. /repobrain ask ... succeeds ...`
  - `3. /repobrain review and /repobrain fix are blocked explicitly.`

### Suggested classification

- `NEEDS_HUMAN_DECISION`

## 7. Stale Current-Truth Packaging Doc: Preflight Checklist

### Candidate

- `docs/packaging/PREFLIGHT_CHECKLIST.md`

### Why it is stale

- It still tells operators to understand a help/ask-only external foundation boundary.

### Evidence snippets

- `docs/packaging/PREFLIGHT_CHECKLIST.md:21`
  - `Operator understands help/ask-only boundary.`

### Suggested classification

- `NEEDS_HUMAN_DECISION`

## 8. Stale Current-Truth Operator Doc

### Candidate

- `docs/OPERATOR_QUICKSTART.md`

### Why it is stale

- It still instructs external GitHub mode foundation validation as help/ask plus negative review check.

### Evidence snippets

- `docs/OPERATOR_QUICKSTART.md:41-49`
  - `Run:`
  - `/repobrain help`
  - `/repobrain ask ...`
  - `Negative check:`
  - `/repobrain review`
- `docs/OPERATOR_QUICKSTART.md:52-54`
  - `Expected:`
  - `explicit unsupported boundary comment`
  - `no false review/fix support claim`

### Suggested classification

- `NEEDS_HUMAN_DECISION`

## 9. Stale Startup/Readiness Summary Docs

### Candidates

- `docs/startup/READINESS_MATRIX.md`
- `docs/startup/STARTUP_READINESS.md`
- `docs/startup/EXTERNAL_EVALUATION_PATH.md`
- `docs/startup/EVALUATOR_GUIDE.md`
- `docs/strategy/PROVEN_CAPABILITIES_SUMMARY.md`

### Why they are stale

These files still describe the external foundation as ask-only or review/fix unsupported.

### Evidence snippets

- `docs/startup/READINESS_MATRIX.md:6`
  - `third-party GitHub-native help/ask path | review/fix unsupported`
- `docs/startup/STARTUP_READINESS.md:12-13`
  - `external GitHub mode foundation (third-party help/ask)`
- `docs/startup/STARTUP_READINESS.md:27`
  - `External review/fix is unsupported.`
- `docs/startup/EXTERNAL_EVALUATION_PATH.md:33-39`
  - `optional negative check: /repobrain review`
  - `explicit unsupported behavior for out-of-scope commands`
- `docs/startup/EVALUATOR_GUIDE.md:20`
  - `Validate external GitHub mode foundation on a third-party repo (help, ask, and explicit unsupported review block).`
- `docs/strategy/PROVEN_CAPABILITIES_SUMMARY.md:19-20`
  - `third-party GitHub-native /repobrain help and /repobrain ask are supported.`
  - `/repobrain review and /repobrain fix are explicitly unsupported and block honestly.`

### Suggested classification

- `NEEDS_HUMAN_DECISION`

## 10. Validation-Repo-Specific Trial Runbook Candidate

### Candidate

- `docs/trials/external_repo_trial_01_elen_mcp.md`

### Why it is stale or misplaced

- It is specific to `alexworkingai/Elen-MCP-v.2.2.0` and still encodes older external-review/fix unsupported assumptions.
- It is closer to validation-repo history than to core current-truth docs.

### Evidence snippets

- `docs/trials/external_repo_trial_01_elen_mcp.md:3-7`
  - `trial id: external-repo-trial-01`
  - `target repository: alexworkingai/Elen-MCP-v.2.2.0`
- `docs/trials/external_repo_trial_01_elen_mcp.md:39-45`
  - `negative check: ... --command review ...`
  - `review and fix are expected to block as unsupported in external mode.`

### Suggested classification

- `MOVE_TO_VALIDATION_REPO_CANDIDATE`

## 11. Validation-Repo-Specific Trial Narrative Candidate

### Candidate

- `docs/benchmarks/external_trial_01_elen_mcp_report.md`

### Why it is stale or misplaced

- It is a repo-specific trial report with old Sprint 59 truth.
- It also contains mojibake in the title line.

### Evidence snippets

- `docs/benchmarks/external_trial_01_elen_mcp_report.md:1`
  - `# External Trial #01 Report вЂ” alexworkingai/Elen-MCP-v.2.2.0`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md:14`
  - `External review path is blocked explicitly as unsupported`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md:20`
  - `It does not claim external parity for review/fix yet.`

### Suggested classification

- `MOVE_TO_VALIDATION_REPO_CANDIDATE`

## 12. Current-Truth Docs That Still Look Required Here

### KEEP signals found

These do not look stale or misplaced based on Sprint 78 truth:

- `README.md`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/benchmarks/current_capabilities_matrix.md`
- `docs/onboarding/github_app_setup.md`
- `docs/onboarding/permissions.md`
- `scripts/check_install_readiness.py`
- `scripts/run_github.py`
- `repobrain/external_flow.py`
- `tests/test_install_readiness.py`
- `tests/test_external_flow.py`
- `tests/test_external_github_foundation_workflow.py`

These still align with either:

- the primary runtime owned here,
- the external CLI ask-only contract owned here,
- or current-truth cross-repo documentation and tests.
