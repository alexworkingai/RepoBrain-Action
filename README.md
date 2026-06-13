# RepoBrain Action

Current release candidate: `0.5.0-rc.1`

RepoBrain is a GitHub-native Repository Intelligence and Quality Scoring Platform.
It operates as a governed GitHub workflow action for repository questions, review guidance, informational verify reporting, repository scoring, and safe no-patch fix proposals.

Current product runtime is v6-only:

- `RepoBrain-Action` is the external product entrypoint
- private TopoCore v6 is a separate proprietary dependency
- external users bring and pay for their own LLM or model provider access
- ask and explain can still answer through deterministic retrieval and TopoCore-backed evidence when an LLM call is not used
- trusted issue ask and explain LLM is enabled by default through `RB_REPOBRAIN_ENABLE_ISSUE_LLM=1`
- when LLM quota is exhausted, RepoBrain falls back to deterministic output and reports the exhausted state without failing the command
- current product behavior remains no-patch and no-mutation
- `/repobrain help` now uses a four-block command-reference manual structure for partners
- PR audit narrative modes now obey canonical PR impact classifier facts so docs-only PRs are not narrated as behavior-affecting or moderate-risk

## Current Status

- RepoBrain-Action supports legacy and internal audit modes plus experimental `hosted_api` self-service foundations
- `hosted_api` mode requires a real external runtime and is not the default GitHub-native beta path
- the next implementation stage is a GitHub-native beta control plane
- Sprint 94B adds the GitHub App installation foundation for that control-plane path
- Sprint 94C adds `github_app_queue` request queue mode and public-safe queue markers
- Sprint 94D adds the private control worker foundation that consumes queued markers through a private TopoCore entrypoint boundary
- GitHub Marketplace is not the immediate route
- trusted and developer beta are expected to use GitHub App installation identity plus a private control worker
- trusted partner beta is not ready until Sprint 94E validation
- final score and audit reports require the private control worker in Sprint 94D
- final score and audit reports require the Sprint 94D private control worker to be deployed in an owner-controlled private repo
- TopoCore remains private and is integrated through stable contracts rather than public runtime distribution
- TopoCore remains a separate team and system
- RepoBrain does not implement TopoCore internals
- RepoBrain integrates TopoCore capabilities and does not implement TopoCore internals
- current GitHub-native queue status is `SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT_READY`

## Quick Start

For a new external repository install, start here:

- Self-service architecture correction and roadmap: `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`
- GitHub App installation foundation: `docs/architecture/SPRINT_94B_GITHUB_APP_INSTALLATION_FOUNDATION.md`
- GitHub-native request queue: `docs/architecture/SPRINT_94C_GITHUB_NATIVE_REQUEST_QUEUE.md`
- Private control worker foundation: `docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md`
- Queue contract: `docs/contracts/GITHUB_NATIVE_REQUEST_QUEUE_V1.md`
- Control worker request contract: `docs/contracts/CONTROL_WORKER_REQUEST_V1.md`
- Control worker result contract: `docs/contracts/CONTROL_WORKER_RESULT_V1.md`
- TopoCore entrypoint adapter contract: `docs/contracts/TOPOCORE_ENTRYPOINT_ADAPTER_V1.md`
- Private control repo setup: `docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md`
- Installation identity contract: `docs/contracts/GITHUB_APP_INSTALLATION_IDENTITY_V1.md`
- Current beta-path quickstart: `docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md`
- Install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- Command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- Troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- Beta queue workflow example: `docs/examples/repobrain_partner_self_service_workflow.yml`
- Example workflow: `docs/examples/repobrain_external_pilot_workflow.yml`
- Sprint 93E historical runbook: `docs/release/SPRINT_93E_TRUSTED_PARTNER_VALIDATION_RUNBOOK.md`
- Sprint 93E historical evidence template: `docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md`
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
- `/repobrain fix` is no-patch proposal and governance only

## Beta Direction

The current beta direction is split into two tracks:

- GitHub-native beta control plane as the intended trusted and developer beta path
- experimental `hosted_api` mode kept as a future external-runtime transport

GitHub-native beta control plane target:
- partner repository
- public `RepoBrain-Action`
- GitHub-native request marker or queue item
- private RepoBrain control worker
- GitHub App installation token
- private TopoCore entrypoint
- public-safe GitHub response

Current 94C queue-mode truth:
- partners use `transport_mode: github_app_queue`
- the public action creates a public-safe queued acknowledgement only
- the queue marker contains no TopoCore internals, no tokens, and no hosted API dependency

Current 94D control-worker truth:
- the private control worker foundation exists in `RepoBrain-Action` as contracts, parser, worker modules, and a private control repo workflow template
- the worker runs only in an owner-controlled private repo
- the worker uses a GitHub App installation token and a configured private TopoCore entrypoint
- the worker does not use `hosted_api` or require `REPOBRAIN_HOSTED_API_URL`
- live trusted partner validation is still deferred to Sprint 94E

What this does not require right now:
- Marketplace
- public SaaS hosting
- domain registration
- TopoCore on partner runners
- owner-generated onboarding tokens
- partner private tokens

## Sprint Foundations Preserved

Useful historical foundations remain in place:

- Phase 1 self-service remains a historical foundation rather than a completed launch state
- the thin public client direction remains useful
- the private hosted/server-side runtime direction remains a historical hosted foundation
- hosted self-service is not claimed as fully live
- Sprint 93A prepared the public self-service foundation
- Sprint 93B added the GitHub OIDC action-side identity envelope
- Sprint 93C defined the hosted trust, quota, and provisioning boundary
- Sprint 93D wired the hosted client send path for supported commands
- Sprint 93E hardened hosted request and response handling and documented trusted validation
- Sprint 94A reclassifies the hosted path as experimental and future-facing because no real external runtime exists yet
- Sprint 94B establishes GitHub App installation identity without Marketplace or partner tokens
- Sprint 94C creates the public-side GitHub-native request queue without running TopoCore on partner runners

Historical sprint truth markers:
- Sprint 93C hosted-boundary truth remains preserved as documentation lineage
- tenant auto-provisioning remains a hosted-boundary concept from Sprint 93C
- Sprint 93D end-to-end self-service truth remains preserved as hosted transport lineage
- final hosted validation remained deferred to Sprint 93E and is now superseded by Sprint 94A

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
