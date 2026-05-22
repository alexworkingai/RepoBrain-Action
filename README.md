# RepoBrain Action

Current release candidate: `0.5.0-rc.1`

RepoBrain is a governed repository cognition action for GitHub workflows.
Current product runtime is v6-only, with `RepoBrain-Action` as the external product entrypoint and private TopoCore v6 as a separate dependency.

## Quick Start

For a new external repository install, start here:

- Install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- Command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- Troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- Example workflow: `docs/examples/repobrain_external_pilot_workflow.yml`

## Product Surface

Current external GitHub command surface:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`

Unsupported command spellings today:

- `/repobrain status`
- `/repobrain doctor`
- `/repobrain fix-lite`

## Safety Guarantees

Current external product behavior remains intentionally conservative:

- v6-only runtime
- no `repobrain-community` dependency
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
- `/repobrain verify` is informational only
- `/repobrain review` is not merge approval
- `/repobrain fix` is no-patch proposal/governance only

## Current Pilot Model

The current external pilot uses:

- `alexworkingai/RepoBrain-Action@main`
- private TopoCore v6 checked out separately with `TOPOCORE_V6_REPO_TOKEN`
- a caller-owned workflow in the consumer repository

RepoBrain-Action remains private during the current pilot phase.
TopoCore v6 remains private.
`repobrain-community` is retired from the working product architecture and is not required.

## Additional References

- User guide: `docs/USER_GUIDE.md`
- Operator quickstart: `docs/OPERATOR_QUICKSTART.md`
- External mode overview: `docs/EXTERNAL_MODE.md`
- External architecture: `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- Repository boundary contract: `docs/REPO_BOUNDARY_CONTRACT.md`
- Public/readiness assessment: `docs/release/PUBLIC_READINESS_ASSESSMENT.md`
