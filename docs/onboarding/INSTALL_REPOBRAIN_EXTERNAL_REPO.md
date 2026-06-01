# Install RepoBrain In An External Repository

## What RepoBrain Is

RepoBrain is a GitHub-native Repository Intelligence and Quality Scoring Platform.
Today it ships as a governed GitHub workflow action for repository questions, review guidance, informational verify reporting, and safe no-patch fix proposals.

Current product runtime is v6-only:

- `RepoBrain-Action` is the product action repository
- private TopoCore v6 is a separate dependency
- the consumer repository owns the caller workflow and secret configuration
- `repobrain-community` is retired and not required

Current distribution stage:

- public action surface with selected partner pilot path
- not a public Marketplace install flow yet
- selected partner testing should prefer installed private package mode when authorized

## Repository Model

Current external pilot shape:

- `RepoBrain-Action`: product action and user-facing workflow surface
- private TopoCore v6: private runtime dependency
- external consumer repository: owns `.github/workflows/repobrain.yml`, secrets, and command entry

Preferred near-term partner-testing shape:

- `RepoBrain-Action`: public action surface
- private TopoCore v6 runtime: installed private package or approved runtime artifact
- consumer repository: no TopoCore source checkout in the normal partner path

Current beta-only fallback shape:

- `private_checkout`
- controlled pilot repositories only

Do not use:

- `repobrain-community`
- `v5`
- `lite`
- `pull_request_target`

## Prerequisites

Before installation, confirm all of the following:

- you can resolve `alexworkingai/RepoBrain-Action@main`
- the consumer repository Actions policy allows external action resolution
- you have the correct private runtime credential for the mode you are using
- you understand which runtime mode you are using:
  - `installed_private_package` preferred for selected partner testing
  - `private_checkout` beta-only
- you understand that model/API costs are paid through your own provider accounts

Reference docs:

- permissions: `docs/onboarding/permissions.md`
- support policy: `docs/release/SUPPORT_POLICY.md`
- version pinning: `docs/release/VERSIONING_AND_PINNING_STRATEGY.md`
- license model: `docs/release/LICENSE_MODEL.md`

## Step 1: Confirm Public Action Resolution

`RepoBrain-Action` is public, but the consumer repository still needs to allow external action resolution.

Check:

- the consumer repository does not stay on `allowed_actions=local_only`
- if the consumer repository uses selected actions, allow `alexworkingai/RepoBrain-Action`

If this is wrong, GitHub may fail during setup with:

- `Unable to resolve action ... repository not found`

That message can mean private-action access or Actions policy trouble, not only a typo.

## Step 2: Choose The Runtime Distribution Mode

Preferred near-term partner mode:

- install a private TopoCore runtime package or approved runtime artifact
- set `RB_TOPOCORE_V6_RUNTIME_MODE=installed_package`
- avoid source checkout in the consumer workspace

Controlled beta-only mode:

- use private source checkout
- set `RB_TOPOCORE_V6_RUNTIME_MODE=private_checkout`
- keep this mode to owner-controlled or explicitly approved pilots

Honest caveat:

- a standard Python wheel can still contain readable implementation files
- this is safer than source checkout, but it is not the same as strong source secrecy

## Step 3: Create Or Configure The TopoCore v6 Runtime Credential

Create the credential that matches your runtime mode.

Preferred installed-package path:

- use an artifact or package credential equivalent in scope to `TOPOCORE_V6_ARTIFACT_TOKEN`
- keep it read-only, scoped, expiring, and revocable

Controlled `private_checkout` fallback:

- use `TOPOCORE_V6_REPO_TOKEN`
- keep it read-only and limited to the private TopoCore repository

Do not print, commit, or paste the token into docs, comments, or workflow logs.
Private runtime access does not grant any TopoCore v6 source rights.

## Step 4: Add The Repository Secret

In the consumer repository, add the secret that matches your runtime mode:

- preferred: partner-specific equivalent of `TOPOCORE_V6_ARTIFACT_TOKEN`
- controlled fallback: `TOPOCORE_V6_REPO_TOKEN`

Expected behavior:

- the secret name may appear in setup guidance
- the secret value must not appear

## Step 5: Add The Workflow

Copy the workflow example into the consumer repository.
That example remains the controlled-pilot `private_checkout` shape and is not the preferred partner-testing path:

- source: `docs/examples/repobrain_external_pilot_workflow.yml`
- destination: `.github/workflows/repobrain.yml`

The current controlled-pilot workflow uses this action ref:

- `alexworkingai/RepoBrain-Action@main`

For controlled private beta this is acceptable.
For stronger reproducibility, prefer an immutable SHA pin when you operate your own rollout.
Public release tag strategy is documented in `docs/release/VERSIONING_AND_PINNING_STRATEGY.md` and is not finalized by this guide.

Optional repository guidance file:

- source: `docs/examples/repobrain.instructions.md`
- destination: `.github/repobrain.instructions.md`

## Step 6: Verify Permissions

Current external pilot baseline is read-mostly:

- `contents: read`
- `models: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

Not required for the current external product path:

- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`
- deployment/package write permissions

Why this matters:

- comments still need write access to issues
- verify needs read access to PR metadata, checks, statuses, and workflow runs
- current product mode does not mutate repository content

## Step 7: Run The First Doctor Check

This is the recommended first setup check after setup.

Open a safe issue comment and run:

```text
/repobrain doctor
```

Expected healthy doctor behavior:

- overall diagnostic status shown as `PASS`, `WARN`, or `UNKNOWN`
- workflow/action context shown
- runtime credential discussed by name without exposing any value
- v6-only / no-v5 policy shown
- no patch/autofix
- no mutation

## Step 8: Run The First Issue Ask

Open a safe issue comment and run:

```text
/repobrain ask Summarize current RepoBrain backend status.
```

Expected healthy backend evidence:

- requested backend: `auto`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`

## Step 9: Run The First PR Ask

Open a safe PR comment and run:

```text
/repobrain ask Summarize this PR with RepoBrain backend diagnostics.
```

Expected healthy backend evidence:

- requested backend: `auto`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`

## Step 10: Run The First Repository Audit

Open a safe issue comment and run:

```text
/repobrain audit Focus on repository readiness for a Microsoft/GitHub-facing demo.
```

Expected healthy audit behavior:

- overall score between `0` and `100`
- static baseline plus live mode truth shown
- all 10 categories shown
- evidence summary shown with safe repo-relative paths
- critical blockers, top improvements, and 30/60/90-day roadmap shown
- no patch/autofix
- no mutation
- repository-level informational output

## Step 11: Run The Compact Score Summary

Open a safe issue comment and run:

```text
/repobrain score Focus on partner-demo readiness.
```

Expected healthy score behavior:

- compact score summary
- same guarded audit engine as `/repobrain audit`
- static baseline shown
- `v6`-enriched mode shown when private capability is available
- all 10 categories shown compactly
- points back to `/repobrain audit` for the full evidence report

## Expected Backend Evidence

In a healthy external install, backend-invoking commands should show:

- requested backend: `auto` or `v6`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`

Current product truth:

- no `repobrain-community` dependency
- no `v5` fallback
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior

## Troubleshooting Quick Table

| Failure | Likely cause | Fix |
|---|---|---|
| `Unable to resolve action ... repository not found` | Actions policy blocks external actions, repository slug/ref is wrong, or GitHub resolution is stale | allow external actions, confirm `alexworkingai/RepoBrain-Action@main`, and retry |
| `TOPOCORE_V6_REPO_TOKEN` missing | consumer secret not configured | add the repository secret |
| private checkout failed | token lacks access, token expired, wrong repo/ref, token approval incomplete | reissue token with read access and update the secret |
| verify returns `NOT_RUN` | no concrete checks/statuses/workflow runs observed | treat as informational absence, not pass/fail |
| fix returns `BLOCKED_BY_SAFETY` | request asked for mutation | use proposal/governance requests only |
| review/verify/fix unsupported in issue | command needs PR context | run on an open PR |

Full troubleshooting guide:

- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

## Security Notes

- TopoCore v6 remains private
- RepoBrain-Action is public for the selected partner pilot
- do not use `pull_request_target` for the external pilot
- do not expose `TOPOCORE_V6_REPO_TOKEN` to untrusted fork code
- do not checkout untrusted fork head code with the private TopoCore token by default
- `/repobrain verify` is informational only
- `/repobrain fix` is no-patch proposal/governance only
- TopoCore v6 source is not licensed through RepoBrain-Action

## Current Limitations

Current supported commands are documented in:

- `docs/commands/REPOBRAIN_COMMANDS.md`

Important current limitations:

- `/repobrain audit` is implemented as an MVP repository-level audit
- `/repobrain doctor` is implemented as a report-only installation/runtime diagnostic
- `/repobrain status` is implemented as a lightweight runtime snapshot
- `/repobrain score` is implemented as a compact summary of the same guarded audit engine
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- there is no patch/autofix mode in the current external product path
- public or Marketplace distribution requires separate approval and a finalized private TopoCore distribution strategy
