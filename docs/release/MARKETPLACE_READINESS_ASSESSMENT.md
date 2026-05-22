# Marketplace Readiness Assessment

## Action Metadata

- action name: `RepoBrain Action`
- action description: product-appropriate after Sprint 76 metadata cleanup
- branding:
  - icon: `search`
  - color: `blue`

## README

- concise external install entrypoint exists
- canonical install, command, and troubleshooting docs are linked
- current private beta shape is explained

## Install Docs

- canonical install guide exists:
  - `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- private action access and TopoCore token setup are documented

## Command Docs

- canonical command matrix exists:
  - `docs/commands/REPOBRAIN_COMMANDS.md`
- supported and unsupported commands are documented honestly

## Permissions

- external workflow example is read-mostly
- current baseline avoids:
  - `contents: write`
  - `checks: write`
  - `pull-requests: write`
  - `pull_request_target`

## Security And Fork Docs

- troubleshooting and security/fork behavior are documented
- no patch/autofix
- no mutation behavior

## Version And Tag Strategy

- current version file exists: `0.5.0-rc.1`
- current Git tags: none
- public immutable ref guidance is not finalized

## Support And Troubleshooting

- external troubleshooting guide exists
- public support policy is not yet formalized

## Blockers

1. Repository is still private.
2. Product still depends on private TopoCore v6 plus `TOPOCORE_V6_REPO_TOKEN`.
3. No top-level `LICENSE`.
4. No finalized public tag/pinning strategy.
5. No formal public support policy.
6. Historical docs still need public scrub/relabeling.

## Decision

- Marketplace decision: `MARKETPLACE_NOT_READY`
- approval state: `NEEDS_APPROVAL` after scrub, packaging, licensing, and support decisions are completed
