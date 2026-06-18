# Install RepoBrain In An External Repository

## What RepoBrain Is

RepoBrain is a GitHub-native Repository Intelligence and Quality Scoring Platform.
Today it ships as a governed GitHub workflow action for repository questions, review guidance, informational verify reporting, and safe no-patch fix proposals.

Current product runtime is v6-only:
- `RepoBrain-Action` is the product action repository
- private TopoCore v6 is a separate dependency
- the consumer repository owns the caller workflow and secret configuration
- `repobrain-community` is retired and not required

## Current Distribution And Beta Truth

Current truth:
- the action surface is public
- Marketplace is not the current onboarding route
- the default trusted beta direction is moving to a GitHub-native control plane
- Sprint 94B adds the GitHub App installation foundation for that direction
- Sprint 94C adds the GitHub-native request queue for that direction
- Sprint 94D adds the private control worker foundation that consumes those queue markers through a private TopoCore entrypoint boundary
- Sprint 94E is the trusted partner beta validation stage for that direction
- experimental `hosted_api` mode exists, but it requires a real external runtime and is not the default beta path
- installed private runtime distribution remains a legacy and owner-managed path, not the target self-service beta architecture
- private TopoCore v6 may still be accessed through legacy credentials such as `TOPOCORE_V6_REPO_TOKEN` in owner-managed paths
- installed private package remains the preferred legacy runtime wording when that owner-managed path is explicitly authorized
- trusted partner beta is not ready until Sprint 94E validation
- trusted partner beta requires live validation evidence before it can be called ready
- final score and audit reports require the private control worker in Sprint 94D
- final score and audit reports require the Sprint 94D private control worker to be deployed in an owner-controlled private repo

## Current Beta Path

Current beta path:
1. RepoBrain team prepares the GitHub App installation foundation.
2. Trusted partner installs the RepoBrain GitHub App when invited.
3. Trusted partner grants selected repository access to that GitHub App.
4. Partner adds the public `RepoBrain-Action` workflow.
5. Partner runs `/repobrain score`, `/repobrain audit`, or `/repobrain audit --profile premium`.
6. `RepoBrain-Action` creates a public-safe queue marker and queued acknowledgement through `github_app_queue`.
7. The Sprint 94D private control worker foundation executes the request through a private TopoCore entrypoint when deployed in the owner-controlled private repo.
8. A public-safe final result is posted back to GitHub only by that private control worker.
9. Trusted partner beta is not ready until Sprint 94E live validation evidence exists.

This flow is being implemented in Sprints 94B-94E.

## Experimental Hosted Mode

Hosted self-service is now classified as experimental and future external-runtime mode.

Current truth:
- do not treat `REPOBRAIN_HOSTED_API_URL` as a required current beta setup step
- do not create fake hosted endpoint values for partner onboarding
- do not require domain registration, tunnels, or external hosting subscriptions for the near-term beta plan
- keep hosted examples only as future transport shape references
- partner repos must not provide TopoCore token for the default GitHub-native beta path
- partner repos must not provide owner token for the default GitHub-native beta path

## Legacy And Internal Runtime-Dependent Path

The numbered install steps below still document the older runtime-dependent path for explicitly approved internal or owner-managed pilots:
- `installed_private_package` or approved artifact delivery when authorized
- `private_checkout` only as a beta fallback

This is not the default GitHub-native beta path described by Sprint 94A and Sprint 94C.

## Repository Model

Current architecture split:
- public `RepoBrain-Action`: user-facing GitHub action surface
- GitHub App installation identity: partner-repo install and scoped repository access layer
- GitHub-native request queue: public-safe marker and acknowledgement layer in Sprint 94C
- private TopoCore: private capability provider
- private GitHub-native control worker foundation: owner-controlled execution layer between the public action and private TopoCore

Do not use:
- `repobrain-community`
- `v5`
- `lite`
- `pull_request_target`

## Prerequisites

Before installation, confirm all of the following:
- you can resolve `alexworkingai/RepoBrain-Action@main`
- the consumer repository Actions policy allows external action resolution
- you understand whether you are using the current GitHub-native beta direction or a legacy owner-managed runtime path
- you understand that model or API costs are paid through your own provider accounts where applicable
- secret values such as `TOPOCORE_V6_REPO_TOKEN` must not appear in logs, comments, or committed files

Reference docs:
- permissions: `docs/onboarding/permissions.md`
- support policy: `docs/release/SUPPORT_POLICY.md`
- version pinning: `docs/release/VERSIONING_AND_PINNING_STRATEGY.md`
- license model: `docs/release/LICENSE_MODEL.md`

## Step 1: Confirm Public Action Resolution

`RepoBrain-Action` must resolve from the consumer repository.

Check:
- the consumer repository does not stay on `allowed_actions=local_only`
- if the consumer repository uses selected actions, allow `alexworkingai/RepoBrain-Action`

## Step 2: Choose The Installation Shape

Preferred near-term beta direction:
- GitHub-native control plane
- GitHub App installation identity
- `transport_mode: github_app_queue`
- no TopoCore on the partner runner
- no hosted external API requirement
- no partner secret requirement for the queue-only step
- no TopoCore token in the partner repository
- no GitHub App private key in the partner repository

Legacy owner-managed path when explicitly approved:
- install a private TopoCore runtime package or approved runtime artifact
- set `RB_TOPOCORE_V6_RUNTIME_MODE=installed_package`
- avoid source checkout in the consumer workspace
- a controlled private-checkout path may still use `TOPOCORE_V6_REPO_TOKEN`

Controlled beta-only fallback:
- use private source checkout
- set `RB_TOPOCORE_V6_RUNTIME_MODE=private_checkout`
- keep this to owner-controlled or explicitly approved pilots
- do not expose that credential to untrusted fork execution

Honest caveat:
- a standard Python wheel can still contain readable implementation files
- that is safer than source checkout, but it is not the same as strong source secrecy

## Step 3: Add The Workflow

For the current GitHub-native beta direction, the partner workflow remains lightweight and public-facing.

Current reference docs:
- architecture correction: `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`
- GitHub App foundation: `docs/architecture/SPRINT_94B_GITHUB_APP_INSTALLATION_FOUNDATION.md`
- GitHub-native request queue: `docs/architecture/SPRINT_94C_GITHUB_NATIVE_REQUEST_QUEUE.md`
- private control worker foundation: `docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md`
- queue contract: `docs/contracts/GITHUB_NATIVE_REQUEST_QUEUE_V1.md`
- control worker request contract: `docs/contracts/CONTROL_WORKER_REQUEST_V1.md`
- control worker result contract: `docs/contracts/CONTROL_WORKER_RESULT_V1.md`
- TopoCore entrypoint adapter contract: `docs/contracts/TOPOCORE_ENTRYPOINT_ADAPTER_V1.md`
- private control repo setup: `docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md`
- installation identity contract: `docs/contracts/GITHUB_APP_INSTALLATION_IDENTITY_V1.md`
- quickstart: `docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md`
- beta queue example: `docs/examples/repobrain_partner_self_service_workflow.yml`
- legacy runtime-dependent example: `docs/examples/repobrain_external_pilot_workflow.yml`

Current truth:
- do not use the experimental hosted example as the default trusted beta setup
- do not set fake `api_url` values for partners
- do not require `REPOBRAIN_HOSTED_API_URL` for the default beta queue path
- wait for Sprint 94B-94E GitHub-native workflow instructions for the default beta path
- use the Sprint 94B-94D GitHub-native workflow and private control-plane docs for the default beta path
- do not expect final reports until the owner deploys the Sprint 94D private worker in the private control repo
- install the RepoBrain GitHub App when invited
- do not install from Marketplace for this stage
- do not claim trusted beta ready until live validation evidence exists

## Step 4: Verify Permissions

Current external baseline remains read-mostly:
- `contents: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

Not required for the current default queue-only path:
- `id-token: write`
- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`
- deployment or package write permissions

Not required for the current external product path:
- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`

## Step 5: Run The First Doctor Check

Open a safe issue comment and run:

```text
/repobrain doctor
```

Expected healthy doctor behavior:
- overall diagnostic status shown as `PASS`, `WARN`, or `UNKNOWN`
- workflow and action context shown
- runtime mode or control-plane context discussed without exposing secret values
- v6-only and no-v5 policy shown
- no patch or autofix
- no mutation
- this is the recommended first setup check after setup

## Step 6: Run The First Issue Ask

Open a safe issue comment and run:

```text
/repobrain ask Summarize current RepoBrain backend status.
```

Expected backend truth:
- resolved backend: `v6`
- no patch/autofix

## Step 7: Run The First Repository Audit

Open a safe issue comment and run:

```text
/repobrain audit Focus on repository readiness for trusted beta onboarding.
```

Expected queue-path truth:
- `RepoBrain-Action` posts a queued acknowledgement only
- a machine-readable GitHub queue marker is embedded in the comment
- no final audit report is produced until Sprint 94D private worker execution exists

## Step 8: Run The Compact Score Summary

Open a safe issue comment and run:

```text
/repobrain score Focus on trusted beta readiness.
```

Expected queue-path truth:
- `RepoBrain-Action` posts a queued acknowledgement only
- no final score report is produced until Sprint 94D private worker execution exists

## Troubleshooting Quick Table

| Failure | Likely cause | Fix |
|---|---|---|
| `Unable to resolve action ... repository not found` | Actions policy blocks external actions, repository slug or ref is wrong, or GitHub resolution is stale | allow external actions, confirm `alexworkingai/RepoBrain-Action@main`, and retry |
| hosted mode placeholder error | `api_url` points to a placeholder or no real external runtime exists | do not use hosted mode for the current default beta path |
| queue mode unsupported event | workflow is not running from `issue_comment` | use the documented issue-comment beta queue workflow |
| verify returns `NOT_RUN` | no concrete checks, statuses, or workflow runs observed | treat as informational absence, not pass or fail |
| fix returns `BLOCKED_BY_SAFETY` | request asked for mutation | use proposal and governance requests only |
| review, verify, or fix unsupported in issue | command needs PR context | run on an open PR |

Full troubleshooting guide:
- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

## Security Notes

- TopoCore remains private
- TopoCore is a separate team and system
- RepoBrain does not implement TopoCore internals
- RepoBrain integrates TopoCore through contracts and public-safe results
- GitHub App private key belongs only in the private control repo
- partner repos must not store the GitHub App private key
- partner repos must not store TopoCore tokens for the GitHub-native beta path
- do not use `pull_request_target` for the external pilot
- do not expose legacy runtime credentials to untrusted fork code
- `/repobrain verify` is informational only
- `/repobrain fix` is no-patch proposal and governance only
- RepoBrain does not grant TopoCore source rights

## Current Limitations

Important current limitations:
- GitHub-native control-plane beta is still being implemented in Sprints 94B-94E
- Sprint 94D adds only the private worker foundation and workflow template, not the final trusted partner validation
- Sprint 94E is the validation stage and the current truthful package-only status is `SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING`
- experimental hosted mode is not the default trusted beta path
- Sprint 94C queue mode only creates a public-safe queued acknowledgement and marker
- final score and audit reports require the private control worker to be deployed in the owner-controlled private repo
- `/repobrain audit` is implemented as an MVP repository-level audit outside the queue-only partner path
- `/repobrain doctor` is report-only installation and runtime diagnostics
- `/repobrain status` is implemented as a lightweight runtime snapshot
- `/repobrain score` is implemented as a compact summary of the same guarded audit engine outside the queue-only partner path
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- there is no patch or autofix mode in the current external product path
- Marketplace distribution remains a separate future decision
