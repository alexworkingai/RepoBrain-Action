# RepoBrain External Troubleshooting

## 1. `Unable to resolve action ... repository not found`

### Symptom

GitHub Actions fails during setup before RepoBrain starts.

Example:

- `Unable to resolve action 'alexworkingai/repobrain-action', repository not found`

### Likely causes

- private action access is not enabled for `RepoBrain-Action`
- the consumer repository Actions policy is too strict, including `allowed_actions=local_only`
- the workflow uses the wrong slug or wrong ref

### Fix

Check all of the following:

- private action sharing is enabled for `RepoBrain-Action`
- the consumer repository allows external actions from `alexworkingai`
- the workflow uses the exact action ref `alexworkingai/RepoBrain-Action@main`

## 2. `TOPOCORE_V6_REPO_TOKEN` missing

### Symptom

Private TopoCore checkout fails before RepoBrain runtime execution.

### Fix

- create a token with read access to the private TopoCore v6 repository
- add it as repository secret `TOPOCORE_V6_REPO_TOKEN`
- rerun the workflow

The secret name can appear in setup guidance.
The secret value must never appear.

## 3. Private checkout failed

### Likely causes

- token lacks repo access
- token expired or was rotated
- wrong repository or ref
- fine-grained token exists but was not approved for the target repository

### Fix

- verify token access to the private TopoCore v6 repository
- verify the token is still valid
- verify the workflow still references `secrets.TOPOCORE_V6_REPO_TOKEN`
- update the repository secret if the token changed

Treat this as a sanitized setup failure, not as a `v5` fallback case.

## 4. Verify returns `NOT_RUN`

### Meaning

`NOT_RUN` means no concrete check runs, statuses, or workflow runs were observed for the PR head SHA.

It does not mean:

- pass
- fail
- merge approval

### What to do

- check whether the PR actually has checks configured
- check whether checks are still pending elsewhere
- use the verify comment limitations block to understand what evidence was missing

## 5. Fix returns `BLOCKED_BY_SAFETY`

### Meaning

The request asked for mutation behavior such as applying a patch, committing changes, or creating a PR.

Current product policy keeps patch/autofix disabled.

### What to do

- ask for a proposal or governance recommendation instead
- do not expect RepoBrain to apply patches

## 6. Review, Verify, Or Fix Unsupported In Issue Scope

### Meaning

Issue context is not treated as PR context.
PR-only review/verification/fix behavior requires an open PR.

### What to do

- run the command on a PR instead of a plain issue
- keep issue usage to `help`, `ask`, `locate`, and `explain`

## 7. Workflow Permissions Too Strict

### Symptom

RepoBrain runs, but verify or PR context is incomplete.

### Minimum permissions

Use the current external read-mostly baseline:

- `contents: read`
- `models: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

Do not add by default:

- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`

## 8. Fork PR Restrictions

### Current policy

- no `pull_request_target` for the external pilot
- no private TopoCore token exposure to untrusted fork code
- no checkout of untrusted fork head code with the private TopoCore token by default

### Why

This preserves the current private dependency boundary and avoids widening trust silently.

## 9. Command Not Recognized

Supported commands:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`

Unsupported command spellings today:

- `/repobrain status`
- `/repobrain doctor`
- `/repobrain fix-lite`
