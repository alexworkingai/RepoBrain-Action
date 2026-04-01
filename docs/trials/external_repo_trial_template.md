# External Repo Trial Template

Use this template for future external-repository trials.

## Trial Metadata

- trial id: `<external-repo-trial-xx>`
- repository: `<owner/repo>`
- operator: `<name or handle>`
- date window: `<YYYY-MM-DD ...>`
- target PR: `<#number + URL>`
- trial objective: `<one-line objective>`

## Preconditions

Mark each item `OK` or `BLOCKED`.

1. GitHub App installed on target repository.
2. Required permissions granted.
3. Required config/secrets/vars present.
4. Selected-repository binding validated.
5. Workflow enabled and visible in Actions.

If any item is `BLOCKED`, classify setup as `BLOCKED_SETUP` and stop.

## Command Plan (Ordered)

1. `/repobrain help`
2. `/repobrain ask --profile balanced <question>`
3. `/repobrain review --profile balanced`
4. (optional) small safe commit, rerun review
5. `/repobrain fix --profile premium <safe narrow instruction>`

## Required Artifacts Per Command

For each executed command, capture:

- workflow run URL + run ID
- command comment URL
- artifact names present
- artifact file paths downloaded
- quick verdict (`COMMAND_WORKED` / `COMMAND_FAILED`)

Recommended artifacts:

- `repobrain-install-readiness`
- `repobrain-audit`
- `repobrain-diagnostic-summary`
- `repobrain-tkya-evidence-pack`
- `repobrain-stability-benchmark` (if run path includes it)

## Outcome Classification

Use exactly one final classification:

- `TRIAL_PASS`
- `TRIAL_PARTIAL`
- `TRIAL_BLOCKED`

Decision rules:

1. `TRIAL_PASS`:
   - readiness is clear and actionable
   - ask + review work on target PR
   - trust artifacts are available and coherent
2. `TRIAL_PARTIAL`:
   - core command path works but evidence is incomplete or partially ambiguous
3. `TRIAL_BLOCKED`:
   - setup/readiness or command execution is blocked

## Required Trial Summary

At trial end, publish a compact summary:

1. setup verdict and blockers
2. command success/failure by step
3. artifact completeness
4. ask/review/fix quality notes
5. no_patch behavior (if applicable)
6. next actions with owner + due date
