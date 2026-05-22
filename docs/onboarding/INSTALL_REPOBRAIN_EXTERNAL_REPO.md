# Install RepoBrain In An External Repository

## What RepoBrain Is

RepoBrain is a governed GitHub workflow action for repository questions, review guidance, verify reporting, and safe no-patch fix proposals.

Current product runtime is v6-only:

- `RepoBrain-Action` is the product action repository
- private TopoCore v6 is a separate dependency
- the consumer repository owns the caller workflow and secret configuration
- `repobrain-community` is retired and not required

Current distribution stage:

- private beta / pilot path
- not a public Marketplace install flow yet

## Repository Model

Current external pilot shape:

- `RepoBrain-Action`: product action and user-facing workflow surface
- private TopoCore v6: private dependency checked out separately
- external consumer repository: owns `.github/workflows/repobrain.yml`, secrets, and command entry

Do not use:

- `repobrain-community`
- `v5`
- `lite`
- `pull_request_target`

## Prerequisites

Before installation, confirm all of the following:

- you can resolve `alexworkingai/RepoBrain-Action@main`
- private action sharing is enabled for `RepoBrain-Action`
- the consumer repository Actions policy allows external action resolution
- you have a token with read access to the private TopoCore v6 repository
- you can store that token as `TOPOCORE_V6_REPO_TOKEN`

## Step 1: Configure Private Action Access

`RepoBrain-Action` is private during the pilot.
The consumer repository must be allowed to resolve it.

Check:

- `RepoBrain-Action` private action sharing is enabled for repositories owned by `alexworkingai`
- the consumer repository does not stay on `allowed_actions=local_only`
- if the consumer repository uses selected actions, allow `alexworkingai/RepoBrain-Action`

If this is wrong, GitHub may fail during setup with:

- `Unable to resolve action ... repository not found`

That message can mean private-action access or Actions policy trouble, not only a typo.

## Step 2: Create Or Configure The TopoCore v6 Token

Create a token that can read the private TopoCore v6 repository.

Required property:

- read access to the private TopoCore v6 repository

Do not print, commit, or paste the token into docs, comments, or workflow logs.

## Step 3: Add The Repository Secret

In the consumer repository, add:

- `TOPOCORE_V6_REPO_TOKEN`

Expected behavior:

- the secret name may appear in setup guidance
- the secret value must not appear

## Step 4: Add The Workflow

Copy the workflow example into the consumer repository:

- source: `docs/examples/repobrain_external_pilot_workflow.yml`
- destination: `.github/workflows/repobrain.yml`

The workflow should use this exact action ref:

- `alexworkingai/RepoBrain-Action@main`

Optional repository guidance file:

- source: `docs/examples/repobrain.instructions.md`
- destination: `.github/repobrain.instructions.md`

## Step 5: Verify Permissions

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

## Step 6: Run The First Issue Ask

Open a safe issue comment and run:

```text
/repobrain ask Summarize current RepoBrain backend status.
```

Expected healthy backend evidence:

- requested backend: `auto`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`

## Step 7: Run The First PR Ask

Open a safe PR comment and run:

```text
/repobrain ask Summarize this PR with RepoBrain backend diagnostics.
```

Expected healthy backend evidence:

- requested backend: `auto`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`

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
| `Unable to resolve action ... repository not found` | private action access not enabled, `allowed_actions=local_only`, or wrong slug | enable private action access, allow external actions, confirm `alexworkingai/RepoBrain-Action@main` |
| `TOPOCORE_V6_REPO_TOKEN` missing | consumer secret not configured | add the repository secret |
| private checkout failed | token lacks access, token expired, wrong repo/ref, token approval incomplete | reissue token with read access and update the secret |
| verify returns `NOT_RUN` | no concrete checks/statuses/workflow runs observed | treat as informational absence, not pass/fail |
| fix returns `BLOCKED_BY_SAFETY` | request asked for mutation | use proposal/governance requests only |
| review/verify/fix unsupported in issue | command needs PR context | run on an open PR |

Full troubleshooting guide:

- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

## Security Notes

- TopoCore v6 remains private
- RepoBrain-Action remains private during the pilot
- do not use `pull_request_target` for the external pilot
- do not expose `TOPOCORE_V6_REPO_TOKEN` to untrusted fork code
- do not checkout untrusted fork head code with the private TopoCore token by default
- `/repobrain verify` is informational only
- `/repobrain fix` is no-patch proposal/governance only

## Current Limitations

Current supported commands are documented in:

- `docs/commands/REPOBRAIN_COMMANDS.md`

Important current limitations:

- `/repobrain status` is unsupported
- `/repobrain doctor` is unsupported
- `/repobrain fix-lite` is unsupported as a user-facing command spelling
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- there is no patch/autofix mode in the current external product path
