# RepoBrain GitHub App Permissions (Foundation)

## Workflow Permission Baseline

Current direct external pilot baseline:

- `contents: read`
- `models: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

## Why Each Permission Exists

- `contents: read`
  - required to read repository files and diff context for Ask/Review/Fix.
- `models: read`
  - required for the current GitHub Models-backed external runtime path.
- `issues: write`
  - required to post issue/PR comment responses to `/repobrain` commands.
- `pull-requests: read`
  - required to read PR metadata, changed files, and review/fix context.
- `checks: read`
  - required to read check-run state for informational verify output.
- `statuses: read`
  - required for verification and check/status diagnostics.
- `actions: read`
  - required for workflow-run diagnostics and publication/orchestration visibility.

## Explicitly Not Required For The External Pilot

- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`
- deployment/package write permissions

Current product truth:

- patch/autofix is disabled
- RepoBrain does not create branches, commits, or PRs on the external pilot path
- consumer repositories should not copy broader internal maintenance permissions from `RepoBrain-Action`

## Selected-Repositories Trust Guidance

For initial rollout:

- install App with selected repositories
- keep explicit repository allowlist via `RB_GH_APP_SELECTED_REPOS`
- validate readiness artifacts before expanding installation scope

This preserves least-privilege onboarding while keeping RepoBrain operational.
