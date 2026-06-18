# Sprint 94E Trusted Partner Beta Validation

## 1. Purpose

Sprint 94E validates the GitHub-native trusted partner beta path.
Trusted partner beta requires live validation evidence.

It validates the chain:
- partner command
- public action queue marker
- private control worker
- private TopoCore entrypoint
- public-safe final GitHub result

## 2. What 94E validates

94E validation must confirm:
- partner workflow uses `transport_mode=github_app_queue`
- partner workflow does not set `api_url`
- partner workflow does not set `REPOBRAIN_HOSTED_API_URL`
- partner repo does not store a TopoCore token
- partner repo does not store a GitHub App private key
- GitHub App installation identity is used
- queue marker is created
- private control worker discovers the marker
- private control worker deduplicates `request_id`
- private TopoCore entrypoint is invoked in private context
- final result comment is public-safe
- no secret or private-path leakage occurs
- `hosted_api` is not called
- no patch or autofix occurs
- no branch, commit, or PR is created by RepoBrain runtime

## 3. Trusted Repositories

Primary:
- `alexworkingai/Elen-MCP-v.2.2.0`

Secondary:
- `alexworkingai/repobrain-community`

## 4. Commands To Validate

For the primary MCP repository:
- `/repobrain score`
- `/repobrain audit`
- `/repobrain audit --profile premium`

For the secondary community repository:
- `/repobrain score`
- `/repobrain audit`
- `/repobrain audit --profile premium`

## 5. Validation Modes

### A. Package-only readiness

Docs, scripts, examples, and tests are ready, but operator setup is not complete.

Status:
- `SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING`

### B. Plumbing validation with stub TopoCore

Queue and worker path are validated with stub TopoCore only.

Status:
- `SPRINT_94E_PLUMBING_VALIDATED_REAL_TOPOCORE_PENDING`

### C. Full trusted beta validation with real private TopoCore

Queue, worker, real private TopoCore entrypoint, and final public-safe result all work on trusted repositories.

Status:
- `TRUSTED_PARTNER_BETA_READY`

## 6. Required Evidence For `TRUSTED_PARTNER_BETA_READY`

Full trusted beta readiness requires:
- queue acknowledgement URL or comment id for each command
- `request_id` for each command
- control worker run id or log reference
- final result comment URL or comment id for each command
- TopoCore mode = `real_private_entrypoint`, not `stub`
- leakage scan result = pass
- `hosted_api` usage = none
- partner secrets = none
- TopoCore in partner runner = no
- GitHub App private key in partner repo = no
- idempotency check = pass
- duplicate responder check = pass
- validation timestamp
- validation actor or operator

## 7. What Does Not Qualify As Full Beta Readiness

The following are not enough on their own:
- queued acknowledgement alone
- stub TopoCore alone
- docs-only PR
- private control worker dry-run alone
- old Sprint 93E `hosted_api` runs
- GitHub App auth check alone

## 8. Next Sprint After Successful Validation

If full trusted beta validation succeeds, the next sprint is:
- Sprint 94F - public developer beta without Marketplace

## 9. Status

Allowed statuses:
- `SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING`
- `SPRINT_94E_PLUMBING_VALIDATED_REAL_TOPOCORE_PENDING`
- `TRUSTED_PARTNER_BETA_READY`

Forbidden without live evidence:
- `PUBLIC_DEVELOPER_BETA_READY`
- `MARKETPLACE_READY`
- `PRODUCTION_APPROVED`
- `SECURITY_CERTIFIED`
