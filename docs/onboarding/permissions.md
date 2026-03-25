# RepoBrain GitHub App Permissions (Foundation)

## Workflow Permission Baseline

`RepoBrain` workflow should provide at least:

- `contents: read`
- `issues: write`
- `pull-requests: write`
- `checks: write`
- `statuses: read`
- `actions: read`

## Why Each Permission Exists

- `contents: read`
  - required to read repository files and diff context for Ask/Review/Fix.
- `issues: write`
  - required to post issue/PR comment responses to `/repobrain` commands.
- `pull-requests: write`
  - required for PR-facing flows (review/fix context and patch PR support when enabled).
- `checks: write`
  - required for RepoBrain check publication path.
- `statuses: read`
  - required for verification and check/status diagnostics.
- `actions: read`
  - required for workflow-run diagnostics and publication/orchestration visibility.

## Selected-Repositories Trust Guidance

For initial rollout:

- install App with selected repositories
- keep explicit repository allowlist via `RB_GH_APP_SELECTED_REPOS`
- validate readiness artifacts before expanding installation scope

This preserves least-privilege onboarding while keeping RepoBrain operational.
