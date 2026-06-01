# Marketplace Readiness Assessment

## Action Metadata

- action name: `RepoBrain Action`
- action description: product-appropriate for repository intelligence and governance
- branding:
  - icon: `search`
  - color: `blue`

## README

- concise external install entrypoint exists
- canonical install, command, and troubleshooting docs are linked
- license, support, and release-readiness docs are linked

## Install Docs

- canonical install guide exists:
  - `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- public action install and private TopoCore runtime setup are documented
- current install path is still private-beta oriented rather than Marketplace turnkey

## Command Docs

- canonical command matrix exists:
  - `docs/commands/REPOBRAIN_COMMANDS.md`
- supported and unsupported commands are documented honestly
- roadmap commands are documented as not yet implemented

## Permissions

- external workflow example is read-mostly
- current baseline avoids:
  - `contents: write`
  - `checks: write`
  - `pull-requests: write`
  - `pull_request_target`

## Security And Fork Docs

- troubleshooting and security/fork behavior are documented
- high-security TopoCore policy exists
- no patch/autofix
- no mutation behavior

## Version And Tag Strategy

- current version file exists: `0.5.0-rc.1`
- current Git tags: none
- public immutable ref guidance is now documented
- no public tags are created yet

## Support And Troubleshooting

- external troubleshooting guide exists
- support policy exists
- public support channel is not yet formalized

## Blockers

1. Repository is still private.
2. Product still depends on private TopoCore v6 plus `TOPOCORE_V6_REPO_TOKEN` in the current beta shape.
3. Public or Marketplace distribution strategy for TopoCore is not yet approved.
4. No immutable public tag has been created.
5. No public support channel has been approved.

## Decision

- Marketplace decision: `MARKETPLACE_NOT_READY`
- approval state: `NEEDS_APPROVAL`
- publication state: Sprint 77 does not publish to GitHub Marketplace
