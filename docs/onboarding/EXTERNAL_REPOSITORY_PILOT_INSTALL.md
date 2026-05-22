# External Repository Pilot Install

This page is retained as a compatibility entrypoint.

For the canonical external install flow, use:

- `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`

For command behavior, use:

- `docs/commands/REPOBRAIN_COMMANDS.md`

For troubleshooting, use:

- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

## Current Product Truth

- action ref: `alexworkingai/RepoBrain-Action@main`
- TopoCore v6 remains private
- `TOPOCORE_V6_REPO_TOKEN` is required for private checkout
- `repobrain-community` is retired and not required
- supported runtime selectors are `auto` and `v6`
- legacy `v5` and `lite` are unsupported
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior

## Minimal Workflow Reference

Use:

- `docs/examples/repobrain_external_pilot_workflow.yml`

Install as:

- `.github/workflows/repobrain.yml`

## Primary Next Steps

1. follow `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
2. validate commands with `docs/commands/REPOBRAIN_COMMANDS.md`
3. resolve failures with `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
