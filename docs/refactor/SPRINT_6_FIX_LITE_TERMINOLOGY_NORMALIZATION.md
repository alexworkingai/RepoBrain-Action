# Sprint 6: Fix-Lite Terminology Normalization

## Purpose

This sprint normalizes current-facing Fix-Lite wording so RepoBrain-Action uses
the same bounded phrase consistently:

- `Fix-Lite Candidate manual-only patch suggestion`

The change is limited to docs/tests truth normalization and does not change
runtime behavior.

## Repository States and Local Paths

- Primary repository:
  `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`
- Public external runtime repository:
  `D:\ARIADNA_Minsk\1MyProjects\repobrain-community`
- Third-party validation repository:
  `D:\ARIADNA_Minsk\1MyProjects\elen-mcp-prod_v2`

At Sprint 6 start:

- `RepoBrain-Action`: `codex/refactor-5-community-packaging-dedup`
- `repobrain-community`: `codex/sprint-78-fix-lite-candidate`
- `elen-mcp-prod_v2`: `test/sprint-73-guidance-live-validation`

## Current Sprint 78 Truth

External GitHub foundation supports:

- `/repobrain doctor`
- `/repobrain help`
- `/repobrain ask <question>`
- `/repobrain review`
- `/repobrain fix`

Current meanings:

- `doctor` = setup health card
- `help` = command truth and boundaries
- `ask` = repo/PR/guidance-aware bounded answer
- `review` = bounded read-only Review Candidate
- `fix` = bounded Fix-Lite Candidate manual-only patch suggestion

Mandatory Fix-Lite boundary:

- `No patch was applied. No files were modified.`

## Search Summary

Search paths included:

- `README.md`
- `docs/`
- `tests/`
- `scripts/`
- `repobrain/`

Search terms included:

- `manual patch suggestion`
- `manual-only patch suggestion`
- `Fix-Lite Candidate`
- `Fix-Lite`
- `No patch was applied. No files were modified.`
- `patch suggestion`
- `manual patch`
- `manual-only`

Findings:

- current-facing non-canonical wording remained in:
  - `docs/benchmarks/current_capabilities_matrix.md`
  - `docs/packaging/CAPABILITY_SURFACES.md`
- current-facing canonical wording was already present in the main operator/docs
  surfaces such as:
  - `README.md`
  - `docs/EXTERNAL_MODE.md`
  - `docs/USER_GUIDE.md`
  - `docs/OPERATOR_QUICKSTART.md`
  - `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`
  - `docs/packaging/INSTALLATION_SHAPE.md`
  - `tests/test_external_github_foundation_workflow.py`
- historical/refactor artifacts retained existing wording where preserving
  earlier phrasing or sprint evidence remained useful

## Files Updated

- `docs/benchmarks/current_capabilities_matrix.md`
- `docs/packaging/CAPABILITY_SURFACES.md`

## Hits Intentionally Preserved as Historical or No-Change Context

- `docs/trials/external_repo_trial_01_elen_mcp.md`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- `docs/refactor/SPRINT_0_REPO_BOUNDARY_INVENTORY.md`
- `docs/refactor/SPRINT_3_EXTERNAL_CLI_SELFTEST_AUDIT.md`
- `docs/refactor/SPRINT_4_HISTORICAL_TRIAL_LABELING.md`
- `docs/refactor/SPRINT_5_COMMUNITY_PACKAGING_DEDUP.md`

These files were not rewritten because they are historical artifacts or refactor
records rather than current-facing command-surface guidance.

## Validation Results

Validation was run from `RepoBrain-Action` after the terminology updates:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## Explicit Statement

No runtime behavior was intentionally changed in Sprint 6.
