# RepoBrain Action

Current release candidate: `0.5.0-rc.1`

RepoBrain is a GitHub-native Repository Intelligence and Quality Scoring Platform.
It operates as a governed GitHub workflow action for repository questions, review guidance, informational verify reporting, and safe no-patch fix proposals.

Current product runtime is v6-only:

- `RepoBrain-Action` is the external product entrypoint
- private TopoCore v6 is a separate proprietary dependency
- external users bring and pay for their own LLM or model provider access
- current product behavior remains no-patch and no-mutation

## Quick Start

For a new external repository install, start here:

- Install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- Command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- Troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- Example workflow: `docs/examples/repobrain_external_pilot_workflow.yml`

## Product Surface

Current supported external GitHub commands:

- `/repobrain audit`
- `/repobrain doctor`
- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review`
- `/repobrain status`
- `/repobrain verify`
- `/repobrain fix`

Current unsupported command spellings:

- `/repobrain score`
- `/repobrain fix-lite`

## Safety Guarantees

Current external product behavior remains intentionally conservative:

- v6-only runtime
- no `repobrain-community` dependency
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
- `/repobrain audit` is informational repository scoring only
- `/repobrain doctor` is report-only setup/runtime diagnostics
- `/repobrain verify` is informational only
- `/repobrain status` is report-only runtime status
- `/repobrain review` is not merge approval
- `/repobrain fix` is no-patch proposal/governance only

## Current Pilot Model

The current external pilot uses:

- `alexworkingai/RepoBrain-Action@main` in controlled pilot repositories
- private TopoCore v6 checked out separately with `TOPOCORE_V6_REPO_TOKEN`
- a caller-owned workflow in the consumer repository
- a bring-your-own-LLM or user-paid model provider model

RepoBrain is not an LLM reseller.
RepoBrain-Action remains private during the current pilot phase.
TopoCore v6 remains private.
`repobrain-community` is retired from the working product architecture and is not required.

## Release And Policy References

- Source-available license: `LICENSE`
- License model: `docs/release/LICENSE_MODEL.md`
- Service/commercial model: `docs/release/SERVICE_AND_COMMERCIAL_MODEL.md`
- Support policy: `docs/release/SUPPORT_POLICY.md`
- Versioning and pinning: `docs/release/VERSIONING_AND_PINNING_STRATEGY.md`
- Public readiness assessment: `docs/release/PUBLIC_READINESS_ASSESSMENT.md`
- Marketplace readiness assessment: `docs/release/MARKETPLACE_READINESS_ASSESSMENT.md`

## Additional References

- User guide: `docs/USER_GUIDE.md`
- Operator quickstart: `docs/OPERATOR_QUICKSTART.md`
- External mode overview: `docs/EXTERNAL_MODE.md`
- External architecture: `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- Repository boundary contract: `docs/REPO_BOUNDARY_CONTRACT.md`
- RepoBrain v6 scoring model: `docs/release/REPOBRAIN_V6_SCORING_MODEL.md`
- Microsoft/GitHub positioning: `docs/release/MICROSOFT_GITHUB_STRATEGIC_POSITIONING.md`
