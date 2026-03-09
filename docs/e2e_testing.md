# E2E Testing (Current Repo)

RepoBrain E2E validation is executed locally via GitHub CLI using:

- `scripts/e2e/run_e2e_suite.py`

## Why local gh orchestration

`GITHUB_TOKEN`-triggered workflows often do not re-trigger other workflows.  
For realistic end-to-end checks, this harness uses local `gh` commands:

- create temp branch
- open PR
- post `/repobrain ...` comments
- wait workflow runs
- download artifacts
- validate usersafe JSON outputs

## Scenarios covered

1. `review` via issue_comment
2. `fix` via issue_comment
3. `ask` via issue_comment
4. `workflow_dispatch` toggles path for LLM/Embeddings

## Expected artifacts validated

- `config_snapshot.json`
- `ai_quota_snapshot.json`
- `llm_usage.json` (if LLM used)
- `embeddings_usage.json` (if embeddings used)
- `verification_report.json`
- `check_run_payload.json` (when check-run path is used)
- `patch.diff`/`patch_parts` (fix path, optional)
- `ask_result.md` (optional when comment is truncated)

## PASS/FAIL interpretation

- **PASS**: run succeeded and required usersafe artifacts validated.
- **WARN**: run succeeded but optional checks/artifact download had issues.
- **FAIL**: workflow failed or artifact validation detected hard violations.

