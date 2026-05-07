# Sprint 7: Repo Boundary Contract Freeze

## 1. Purpose

Sprint 7 freezes the canonical repository-boundary contract after accepted
Sprint 78 behavior and Refactor Sprints 0–6.

The goal is to make future refactoring safer by clearly stating what each
repository owns, what it does not own, and what must not be reintroduced into
`RepoBrain-Action`.

## 2. Repository States and Local Paths

- Primary repository:
  `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`
- Public external runtime repository:
  `D:\ARIADNA_Minsk\1MyProjects\repobrain-community`
- Third-party validation repository:
  `D:\ARIADNA_Minsk\1MyProjects\elen-mcp-prod_v2`

At Sprint 7 start:

- `RepoBrain-Action`: `codex/refactor-6-fix-lite-terminology-normalization`
- `repobrain-community`: `codex/sprint-78-fix-lite-candidate`
- `elen-mcp-prod_v2`: `test/sprint-73-guidance-live-validation`

## 3. Current Sprint 78 Truth

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
- `fix` = Fix-Lite Candidate manual-only patch suggestion

Mandatory Fix-Lite boundary:

- `No patch was applied. No files were modified.`

## 4. Prior Refactor Inputs Reviewed

- `docs/refactor/SPRINT_0_REPO_BOUNDARY_INVENTORY.md`
- `docs/refactor/STALE_EXTERNAL_SURFACE_CANDIDATES.md`
- `docs/refactor/KEEP_MOVE_DELETE_MATRIX.md`
- `docs/refactor/SPRINT_2_LEGACY_EXTERNAL_RETIREMENT.md`
- `docs/refactor/SPRINT_3_EXTERNAL_CLI_SELFTEST_AUDIT.md`
- `docs/refactor/SPRINT_4_HISTORICAL_TRIAL_LABELING.md`
- `docs/refactor/SPRINT_5_COMMUNITY_PACKAGING_DEDUP.md`
- `docs/refactor/SPRINT_6_FIX_LITE_TERMINOLOGY_NORMALIZATION.md`

Current-facing supporting docs reviewed as needed:

- `README.md`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/benchmarks/current_capabilities_matrix.md`
- `docs/packaging/CAPABILITY_SURFACES.md`
- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`
- `docs/packaging/PACKAGING_OVERVIEW.md`
- `docs/startup/READINESS_MATRIX.md`

## 5. Files Created / Updated

Created:

- `docs/REPO_BOUNDARY_CONTRACT.md`
- `docs/refactor/SPRINT_7_REPO_BOUNDARY_CONTRACT_FREEZE.md`

Updated with lightweight navigation links:

- `README.md`
- `docs/EXTERNAL_MODE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`

## 6. Boundary Decisions Frozen

Frozen by this sprint:

- `RepoBrain-Action` remains the core/docs/tests/governance repository
- `repobrain-community` remains the canonical public external runtime and
  template host
- `elen-mcp-prod_v2` remains validation-only and must not be treated as current
  runtime truth
- retired legacy external workflow/template copies stay retired from
  `RepoBrain-Action`
- external CLI ask-only and MCP ask-only remain bounded secondary surfaces in
  `RepoBrain-Action`

## 7. Guardrails for Future Refactoring

Future refactors must preserve:

- current supported/unsupported command honesty
- no-autofix/no-patch/no-file-modification guarantees
- TKYA/TopoCore contract guards
- audit/evidence metadata
- current docs truth
- local validation gates
- live PR validation discipline for runtime-impacting changes

## 8. Validation Results

Validation was run from `RepoBrain-Action` after adding the contract freeze
docs:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## 9. Explicit Statement

No runtime behavior was intentionally changed in Sprint 7.
