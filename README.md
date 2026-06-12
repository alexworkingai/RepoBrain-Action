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

## Quick Start

For a new external repository install, start here:

- Phase 1 self-service / OIDC envelope quickstart: `docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md`
- Install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- Command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- Troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- Example workflow: `docs/examples/repobrain_external_pilot_workflow.yml`
- Self-service workflow shape: `docs/examples/repobrain_partner_self_service_workflow.yml`
- Trusted-partner validation runbook: `docs/release/SPRINT_93E_TRUSTED_PARTNER_VALIDATION_RUNBOOK.md`
- Validation evidence template: `docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md`
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

Sprint 92D branch truth:

- issue ask may use an LLM only when safe policy allows
- deterministic fallback remains available for operational and product-analysis questions
- route labels reflect the typed command rather than internal analysis mode
- protected main baseline is enabled on the public RepoBrain repository
- required status checks remain intentionally deferred until stable check names are locked

Sprint 92F-92H implementation truth:

- controlled trusted issue ask/explain LLM is enabled by default through `RB_REPOBRAIN_ENABLE_ISSUE_LLM=1`
- `/repobrain audit --narrative` adds an optional explanatory LLM layer after TopoCore scoring
- `/repobrain audit --executive` adds an optional executive/partner-facing LLM layer after TopoCore scoring
- `/repobrain audit --profile premium` implies a premium narrative/explanation layer after TopoCore scoring
- PR audit narrative, executive, and premium modes now consume canonical PR classifier facts and keep docs-only PR impact grounded
- premium audit narrative is bounded and explicitly reports when it was shortened to stay within response budget
- `/repobrain score` remains a compact TopoCore-first summary and does not require an LLM
- current readiness status on the Sprint 92H branch is `SPRINT_92H_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING`

Sprint 93A foundation truth:

- public Phase 1 self-service foundation is being prepared
- RepoBrain-Action is the intended thin public client direction
- TopoCore v6 remains the private hosted/server-side runtime direction
- no owner-generated onboarding token path is the intended Phase 1 model
- full OIDC and hosted API onboarding are not claimed as live in this sprint

Sprint 93B identity-envelope truth:

- the public action now supports GitHub Actions OIDC token acquisition when the workflow grants `id-token: write`
- the public action now builds a sanitized `repobrain.github_oidc_identity.v1` envelope for future hosted verification
- `self_service_mode` enforces `terms_accepted` and GitHub OIDC availability when explicitly enabled
- hosted API verification and automatic tenant provisioning remain deferred to Sprint 93C
- partner self-service public action is not yet claimed as fully live

Sprint 93C hosted-boundary truth:

- the hosted RepoBrain API trust contract is now defined as `repobrain.github_action_audit_request.v1`
- server-side GitHub OIDC verification, claim consistency checks, tenant auto-provisioning, and default quota policy are now implemented as pure service boundaries
- the action now prepares a redacted hosted request preview when `self_service_mode` and OIDC are both available
- end-to-end action-to-hosted-api request sending and GitHub response posting remain deferred to Sprint 93D
- trusted partner hardening and live validation remain deferred to Sprint 93E

Sprint 93D end-to-end self-service truth:

- `self_service_mode` now wires supported `ask`, `audit`, and `score` commands through the hosted API client path when `api_url` is configured
- the public action now sends the versioned hosted request contract and renders public-safe hosted responses back into the GitHub comment flow
- public-safe hosted error rendering now covers missing `api_url`, hosted API unavailability, quota/public-safe server errors, and other redacted failures
- existing non-self-service local/private runtime behavior remains unchanged
- final trusted partner hardening and validation remain deferred to Sprint 93E

Sprint 93E final-hardening truth:

- hosted self-service client now rejects unexpected redirect responses instead of following them
- requested audit execution profiles such as `/repobrain audit --profile premium` are now preserved end-to-end in the hosted request payload and redacted request preview
- trusted-partner validation runbook and evidence template now exist for `alexworkingai/Elen-MCP-v.2.2.0` and `alexworkingai/repobrain-community`
- the final Phase 1 status remains `SPRINT_93E_HARDENING_READY_LIVE_VALIDATION_PENDING` until live issue and PR validation pass on both trusted validation repositories
- no owner-generated onboarding token, manual registration, or TopoCore install/download path is introduced by the self-service flow

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
