# Sprint 4 Historical Trial Labeling

## 1. Purpose

Sprint 4 labels older Elen-MCP trial and benchmark documents as historical artifacts so they cannot be mistaken for current operational guidance after Sprint 78.

This sprint is docs-only. It does not change runtime code, tests, workflows, or external repositories.

## 2. Repository States and Local Paths

Primary repository:

- `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`

Reference repositories only:

- `D:\ARIADNA_Minsk\1MyProjects\repobrain-community`
- `D:\ARIADNA_Minsk\1MyProjects\elen-mcp-prod_v2`

Observed start state:

- `RepoBrain-Action`: `codex/refactor-3-external-cli-selftest-audit` @ `4424688`
- `repobrain-community`: `codex/sprint-78-fix-lite-candidate` @ `7969932`
- `elen-mcp-prod_v2`: `test/sprint-73-guidance-live-validation` @ `0835bd2`

## 3. Current Sprint 78 Truth

Current public external GitHub foundation commands:

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

## 4. Files Inspected

Historical artifacts:

- `docs/trials/external_repo_trial_01_elen_mcp.md`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md`

Current-facing references inspected:

- `README.md`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/benchmarks/current_capabilities_matrix.md`
- `docs/startup/READINESS_MATRIX.md`
- `docs/strategy/ATTENTION_PACK_INDEX.md`
- `docs/refactor/SPRINT_3_EXTERNAL_CLI_SELFTEST_AUDIT.md`

## 5. Files Updated

- `docs/trials/external_repo_trial_01_elen_mcp.md`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- `README.md`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/refactor/SPRINT_4_HISTORICAL_TRIAL_LABELING.md`

## 6. Historical Labeling Decisions

### `docs/trials/external_repo_trial_01_elen_mcp.md`

- Added a top-of-file historical artifact notice.
- Preserved the historical runbook body, including the older external CLI ask-first framing.
- Added a current-state note that points readers to current Sprint 78 truth and current operator docs.

### `docs/benchmarks/external_trial_01_elen_mcp_report.md`

- Added a top-of-file historical artifact notice.
- Preserved the historical benchmark body and Sprint 59-era interpretation.
- Fixed the mojibake in the title so the document header is readable.
- Added a current-state note that points readers to current Sprint 78 truth and current operator docs.

## 7. Reference / Index Updates

Updated current-facing link text where needed so the historical docs are not presented as current operational guidance:

- `README.md`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`

No broader doc rewrites were made.

## 8. Remaining Risks

1. The historical bodies still contain older review/fix-unsupported framing, but the new top-of-file notices now make that status explicit.
2. Additional archival/index cleanup may still be useful later if more historical trial documents are surfaced.

## 9. Validation Results

Validation was rerun from `RepoBrain-Action` after the labeling updates:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`
- `git diff --name-only`
- `git diff --stat`

## 10. Final Statement

No runtime behavior was intentionally changed in Sprint 4.