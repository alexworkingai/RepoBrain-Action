# RepoBrain Action

Current release candidate: `0.5.0-rc.1`

RepoBrain is a GitHub-native Repository Intelligence and Quality Scoring Platform.
It operates as a governed GitHub workflow action for repository questions, review guidance, informational verify reporting, repository scoring, and safe no-patch fix proposals.

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
- Partner readiness: `docs/release/PARTNER_TESTING_READINESS.md`
- Public approval checklist: `docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md`
- Partner setup pack: `docs/partner/PARTNER_TESTING_SETUP.md`

## Product Surface

Current supported external GitHub commands:

- `/repobrain audit`
- `/repobrain score`
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

- `/repobrain fix-lite`

## Safety Guarantees

Current external product behavior remains intentionally conservative:

- v6-only runtime
- no `repobrain-community` dependency
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
- `/repobrain audit` is an informational 100-point repository scoring MVP and may show contract-validated private `v6` enrichment when available
- `/repobrain score` is a compact summary of the same guarded audit engine
- `/repobrain doctor` is report-only setup/runtime diagnostics
- `/repobrain verify` is informational only
- `/repobrain status` is report-only runtime status
- `/repobrain review` is not merge approval and not safe to merge guidance
- `/repobrain fix` is no-patch proposal/governance only

## Current Pilot Model

The current external pilot uses:

- public `alexworkingai/RepoBrain-Action@main` in controlled pilot repositories
- preferred partner runtime path: private installed package / runtime artifact
- `private_checkout` only as a controlled beta fallback in owner-managed environments
- a caller-owned workflow in the consumer repository
- a bring-your-own-LLM or user-paid model provider model

Sprint 84 public-ready gate truth:

- `private_checkout` remains beta-only
- selected partner testing should prefer installed private package mode when authorized
- plain Python package artifacts still need honest handling because they can contain readable implementation files

Sprint 91 public-switch truth:

- owner approval for the RepoBrain-Action public visibility switch was recorded and executed
- RepoBrain-Action is now public
- selected partner pilot kickoff pack is ready from the public action surface
- RC tag creation remains approval-gated and is not executed automatically
- Marketplace remains not started

RepoBrain is not an LLM reseller.
TopoCore v6 remains private.
`repobrain-community` is retired from the working product architecture and is not required.

## Release And Policy References

- Source-available license: `LICENSE`
- License model: `docs/release/LICENSE_MODEL.md`
- Service/commercial model: `docs/release/SERVICE_AND_COMMERCIAL_MODEL.md`
- Support policy: `docs/release/SUPPORT_POLICY.md`
- Versioning and pinning: `docs/release/VERSIONING_AND_PINNING_STRATEGY.md`
- Audit benchmark report: `docs/release/AUDIT_BENCHMARK_REPORT.md`
- Microsoft/GitHub demo report: `docs/release/MICROSOFT_GITHUB_DEMO_REPORT.md`
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
