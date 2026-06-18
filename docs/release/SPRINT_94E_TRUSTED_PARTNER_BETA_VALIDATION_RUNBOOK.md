# Sprint 94E Trusted Partner Beta Validation Runbook

## 1. Preconditions

Required before live validation:
- Sprint 94D merged to `main`
- public `RepoBrain-Action` ref pinned to a validated commit SHA
- RepoBrain GitHub App exists
- GitHub App installed on selected trusted repositories
- private control repo exists
- private control repo has:
  - `REPOBRAIN_GITHUB_APP_ID`
  - `REPOBRAIN_GITHUB_APP_PRIVATE_KEY`
- private control repo can mint an installation token
- private control worker can run

For full real validation, the private control repo must also have:
- `REPOBRAIN_TOPOCORE_ENTRYPOINT_MODE=command`
- `REPOBRAIN_TOPOCORE_ENTRYPOINT_CMD=<private command configured outside public repo>`

For plumbing validation only:
- `REPOBRAIN_TOPOCORE_ENTRYPOINT_MODE=stub`

Do not include actual secret values.
Do not include a private command path if it reveals private infrastructure.
Use placeholders only.

## 2. Partner Workflow Requirement

Trusted repositories must use a workflow equivalent to:
- `transport_mode: github_app_queue`
- `terms_accepted: "true"`
- `profile: partner-pilot`

Must not use:
- `api_url`
- `REPOBRAIN_HOSTED_API_URL`
- TopoCore token
- GitHub App private key
- owner token
- `private_checkout`

Critical workflow note:
- for `issue_comment` live validation, the workflow file must be active on the repository default branch
- workflow must be active on the repository default branch
- a workflow added only in an unmerged PR may not respond to `issue_comment`

If the workflow is not on the default branch, use:
- `SPRINT_94E_BLOCKED_WORKFLOW_NOT_ON_DEFAULT_BRANCH`

## 3. Partner Setup Steps

For each trusted repository:
1. Confirm GitHub App installation.
2. Confirm the workflow exists on the default branch.
3. Confirm the workflow uses a pinned `RepoBrain-Action` ref.
4. Confirm there is no `api_url` or `hosted_api` default path.
5. Create or identify a validation issue or PR.
6. Post:
   - `/repobrain score`
   - `/repobrain audit`
   - `/repobrain audit --profile premium`

## 4. Expected Public Action Result

For each command:
- queued acknowledgement comment appears
- machine-readable queue marker exists
- `request_id` exists
- `status=queued`
- `transport_mode=github_app_queue`
- no final audit claim yet
- no `hosted_api` error
- no `REPOBRAIN_HOSTED_API_URL` blocker
- no TopoCore execution in the partner runner

Queued acknowledgement alone is not a full pass.

## 5. Private Control Worker Dry-Run

Run the private control worker in dry-run mode:
- discovers queued markers
- validates `request_id`
- validates repo identity
- does not post final result
- does not leak token or path data

Example private-control-repo-only environment:
- `REPOBRAIN_CONTROL_WORKER_DRY_RUN=true`
- `REPOBRAIN_TOPOCORE_ENTRYPOINT_MODE=stub`

## 6. Private Control Worker Stub Mode

Run the private control worker with stub TopoCore:
- processes queued markers
- posts a public-safe final result
- confirms renderer and posting path
- confirms no `hosted_api`
- confirms no partner secrets

Status after only stub mode:
- `SPRINT_94E_PLUMBING_VALIDATED_REAL_TOPOCORE_PENDING`

Stub mode is not enough for final trusted beta readiness.

## 7. Private Control Worker Real TopoCore Mode

Run the private control worker with the real private TopoCore entrypoint:
- processes queued markers
- posts a public-safe final result
- score and verdict come from TopoCore
- LLM does not modify score
- no TopoCore internals are exposed

Only after this succeeds:
- `TRUSTED_PARTNER_BETA_READY`

Real private TopoCore configuration is private-control-repo only.
Public `RepoBrain-Action` never stores a TopoCore command, path, or token.
Partner repositories never store TopoCore secrets.

## 8. Idempotency Check

Re-run the worker on the same markers:
- must not duplicate a completed final result
- must skip already-processed `request_id`
- must preserve public-safe output

## 9. Leakage Scan

Scan:
- partner workflow logs
- queued acknowledgement comments
- final result comments
- control worker sanitized logs
- evidence file

Must not contain:
- `Authorization`
- `Bearer`
- classic GitHub personal access token prefixes
- fine-grained GitHub personal access token prefixes
- JWT-like token
- GitHub App private key
- installation token
- TopoCore token
- private TopoCore path
- `.topocore-v6`
- private checkout path
- `decide_raw`
- raw internal trace
- raw stack trace with secrets
- `REPOBRAIN_HOSTED_API_URL` as a required path

## 10. PASS Criteria

For `TRUSTED_PARTNER_BETA_READY`:
- primary MCP repo passes all three commands with real private TopoCore
- secondary community repo passes all three commands with real private TopoCore
- queue acknowledgement appears for each
- final result appears for each
- idempotency passes
- no duplicate responder
- no `hosted_api` usage
- no partner secrets
- no TopoCore in partner runner
- no leakage
- governance remains truthful
- no Marketplace, public-beta, or production overclaim

## 11. Failure Handling

For each failure, record:
- repository
- command
- `request_id` if available
- stage
- error code
- safe summary
- whether retry is safe
- whether the blocker is operator setup or a code issue
