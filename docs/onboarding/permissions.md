# RepoBrain GitHub App Permissions

## Canonical References

Use these docs together:

- Install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- Command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- Troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

## Workflow Permission Baseline

Current external pilot baseline:

- `contents: read`
- `models: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

## Why Each Permission Exists

- `contents: read`
  - required to read repository files and diff context
- `models: read`
  - required for the current GitHub Models-backed external runtime path
- `issues: write`
  - required to post issue and PR comment responses to `/repobrain` commands
- `pull-requests: read`
  - required to read PR metadata and changed files
- `checks: read`
  - required to read check-run state for informational verify output
- `statuses: read`
  - required for verification and status diagnostics
- `actions: read`
  - required for workflow-run diagnostics

## Explicitly Not Required For The External Pilot

- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`
- deployment/package write permissions

## Product Safety Context

Current product truth:

- patch/autofix is disabled
- RepoBrain does not create branches, commits, or PRs on the external pilot path
- consumer repositories should not copy broader internal maintenance permissions from `RepoBrain-Action`
