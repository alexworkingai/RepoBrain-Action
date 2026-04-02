# External Repo Trial Template

Use this template for future external-repository trials.

## Trial Metadata

- trial id: `<external-repo-trial-xx>`
- repository: `<owner/repo>`
- operator: `<name or handle>`
- date window: `<YYYY-MM-DD ...>`
- trial mode: `external` or `github`
- target scope: `<PR/module/question set>`
- trial objective: `<one-line objective>`

## Preconditions

Mark each item `OK` or `BLOCKED`.

1. Install/readiness verdict collected.
2. Required permissions granted.
3. Required config/secrets/vars present.
4. Selected-repository binding validated (when GitHub mode is used).
5. Local repo checkout available (when external mode is used).

If any item is `BLOCKED`, classify setup as `BLOCKED_SETUP` and stop.

## Command Plan (Ordered)

External mode baseline:

1. `python scripts/run_github.py --mode external --repo-root <repo_path> --command ask --query "<question>"`
2. (optional) ask continuity rerun with narrower scope
3. unsupported-command probe (`review` or `fix`) to verify honest block

GitHub mode baseline (if included in same trial):

1. `/repobrain help`
2. `/repobrain ask --profile balanced <question>`
3. `/repobrain review --profile balanced`
4. `/repobrain fix --profile premium <safe narrow instruction>`

## Required Evidence Per Command

For each executed command, capture:

- command text
- run/log URL or local stdout snapshot
- status (`COMMAND_WORKED` / `COMMAND_FAILED`)
- decision code (if available)
- artifact names present
- artifact file paths downloaded

Recommended artifacts:

- `repobrain-install-readiness`
- `repobrain-audit`
- `repobrain-diagnostic-summary`
- `repobrain-tkya-evidence-pack`
- external mode: `<repo_root>/artifacts/external_flow_index.zip`

## Outcome Classification

Use exactly one final classification:

- `TRIAL_PASS`
- `TRIAL_PARTIAL`
- `TRIAL_BLOCKED`

Decision rules:

1. `TRIAL_PASS`:
   - setup/readiness is clear and actionable
   - supported command path works
   - unsupported path (if tested) blocks honestly
2. `TRIAL_PARTIAL`:
   - core path works but evidence/diagnostics are incomplete
3. `TRIAL_BLOCKED`:
   - setup/readiness or command execution is blocked

## Required Trial Summary

At trial end, publish a compact summary:

1. setup verdict and blockers
2. command success/failure by step
3. artifact completeness
4. ask/review/fix observations (mode-specific)
5. unsupported-command behavior observations
6. next actions with owner + due date
