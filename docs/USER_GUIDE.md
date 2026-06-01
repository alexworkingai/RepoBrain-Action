# RepoBrain User Guide

## Who This Is For

This guide is for users operating RepoBrain from GitHub issue and PR comments.

If you are installing RepoBrain in a new external repository, start here instead:

- `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`

## Supported User Commands

Use the canonical command matrix:

- `docs/commands/REPOBRAIN_COMMANDS.md`

Current supported GitHub commands:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`

Unsupported user-facing spellings:

- `/repobrain status`
- `/repobrain doctor`
- `/repobrain fix-lite`

## Scope Rules

- issue scope:
  - `help`, `ask`, `locate`, and `explain` are supported
  - `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- PR scope:
  - `ask`, `review`, `verify`, and `fix` are supported
  - `locate` and `explain` may be supported when routed by the parser

## Safety And Behavior

Current product behavior remains conservative:

- `/repobrain verify` is informational only
- `/repobrain review` is not approval
- `/repobrain fix` is no-patch proposal/governance only
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
- no safe-to-merge claim
- no security approval claim

Visible fix safety gates should show:

- `patch_authorized=false`
- `patch_applied=false`
- `files_modified=false`
- `branch_created=false`
- `commit_created=false`
- `pr_created=false`

## External Pilot And Security Notes

Current pilot truth:

- `RepoBrain-Action` is the product action
- private TopoCore v6 is a separate dependency
- `TOPOCORE_V6_REPO_TOKEN` is required for private checkout
- `repobrain-community` is retired and not required
- missing or invalid private-token access is a setup failure, not a `v5` fallback case
- RepoBrain-Action is public, but the consumer repository Actions policy must still allow external actions
- `Unable to resolve action ... repository not found` can mean Actions policy failure or wrong ref, not only a typo
- untrusted fork PRs should not receive private TopoCore secrets

## Where To Go Next

- Install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- Command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- Troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- Operator quickstart: `docs/OPERATOR_QUICKSTART.md`
- External mode overview: `docs/EXTERNAL_MODE.md`
- External architecture: `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
