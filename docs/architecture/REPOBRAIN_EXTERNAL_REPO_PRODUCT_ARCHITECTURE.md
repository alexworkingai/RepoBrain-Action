# RepoBrain External Repo Product Architecture

## Current Product Topology

Current external product path uses:

- `RepoBrain-Action`
- private TopoCore v6
- external consumer repositories
- no `repobrain-community`

Current product entrypoint for external repositories:

- consumer repository workflow: `.github/workflows/repobrain.yml`
- action ref: `alexworkingai/RepoBrain-Action@main`
- private secret: `TOPOCORE_V6_REPO_TOKEN`

## Why `repobrain-community` Is Removed From Architecture

`repobrain-community` added an extra bridge layer without adding current product value.
It is retired from the working product architecture and is not part of the product or the active product runtime, onboarding, or troubleshooting path.
It may archive later as a historical repository if desired.

## Canonical External User Docs

Current user-facing install and usage path is:

- `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- `docs/commands/REPOBRAIN_COMMANDS.md`
- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- `docs/examples/repobrain_external_pilot_workflow.yml`

## Product Guarantees

- v6-only runtime
- no `repobrain-community` dependency in active product runtime/onboarding
- no `v5`
- no patch/autofix
- no patch/autofix by default
- no RepoBrain-created branch/commit/PR behavior
- no safe-to-merge or security approval claim
