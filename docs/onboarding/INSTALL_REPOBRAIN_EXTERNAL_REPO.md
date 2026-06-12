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
- experimental `hosted_api` mode exists, but it requires a real external runtime and is not the default beta path
- installed private runtime distribution remains a legacy and owner-managed path, not the target self-service beta architecture
- private TopoCore v6 may still be accessed through legacy credentials such as `TOPOCORE_V6_REPO_TOKEN` in owner-managed paths
- installed private package remains the preferred legacy runtime wording when that owner-managed path is explicitly authorized
- trusted partner beta is not ready until Sprint 94E validation

## Current Beta Path

Current beta path:
1. RepoBrain team prepares the GitHub App installation foundation.
2. Trusted partner installs the RepoBrain GitHub App when invited.
3. Trusted partner grants selected repository access to that GitHub App.
4. Partner adds the public `RepoBrain-Action` workflow.
5. Partner runs `/repobrain score`, `/repobrain audit`, or `/repobrain audit --profile premium`.
6. A private control worker executes the request through private TopoCore.
7. A public-safe result is posted back to GitHub.

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

This is not the default GitHub-native beta path described by Sprint 94A.

## Repository Model

Current architecture split:
- public `RepoBrain-Action`: user-facing GitHub action surface
- GitHub App installation identity: partner-repo install and scoped repository access layer
- private TopoCore: private capability provider
- future GitHub-native control worker: owner-controlled execution layer between the public action and private TopoCore

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
- no TopoCore on the partner runner
- no hosted external API requirement

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

For the future GitHub-native beta direction, the partner workflow will remain lightweight and public-facing.

Current reference docs:
- architecture correction: `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`
- GitHub App foundation: `docs/architecture/SPRINT_94B_GITHUB_APP_INSTALLATION_FOUNDATION.md`
- private control repo setup: `docs/control-plane/GITHUB_APP_PRIVATE_CONTROL_REPO_SETUP.md`
- installation identity contract: `docs/contracts/GITHUB_APP_INSTALLATION_IDENTITY_V1.md`
- quickstart: `docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md`
- experimental hosted shape example: `docs/examples/repobrain_partner_self_service_workflow.yml`
- legacy runtime-dependent example: `docs/examples/repobrain_external_pilot_workflow.yml`

Current truth:
- do not use the experimental hosted example as the default trusted beta setup
- do not set fake `api_url` values for partners
- wait for Sprint 94B-94E GitHub-native workflow instructions for the default beta path
- install the RepoBrain GitHub App when invited
- do not install from Marketplace for this stage

## Step 4: Verify Permissions

Current external baseline remains read-mostly:
- `contents: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

Additional identity permission used by the historical and future trust layers:
- `id-token: write`

Not required for the current external product path:
- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`
- deployment or package write permissions

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

## Step 8: Run The Compact Score Summary

Open a safe issue comment and run:

```text
/repobrain score Focus on trusted beta readiness.
```

## Troubleshooting Quick Table

| Failure | Likely cause | Fix |
|---|---|---|
| `Unable to resolve action ... repository not found` | Actions policy blocks external actions, repository slug or ref is wrong, or GitHub resolution is stale | allow external actions, confirm `alexworkingai/RepoBrain-Action@main`, and retry |
| hosted mode placeholder error | `api_url` points to a placeholder or no real external runtime exists | do not use hosted mode for the current default beta path |
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
- do not use `pull_request_target` for the external pilot
- do not expose legacy runtime credentials to untrusted fork code
- `/repobrain verify` is informational only
- `/repobrain fix` is no-patch proposal and governance only
- RepoBrain does not grant TopoCore source rights

## Current Limitations

Important current limitations:
- GitHub-native control-plane beta is still being implemented in Sprints 94B-94E
- experimental hosted mode is not the default trusted beta path
- `/repobrain audit` is implemented as an MVP repository-level audit
- `/repobrain doctor` is report-only installation and runtime diagnostics
- `/repobrain status` is implemented as a lightweight runtime snapshot
- `/repobrain score` is implemented as a compact summary of the same guarded audit engine
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- there is no patch or autofix mode in the current external product path
- Marketplace distribution remains a separate future decision
