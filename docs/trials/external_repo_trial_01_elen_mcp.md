# External Repo Trial #01 Runbook — alexworkingai/Elen-MCP-v.2.2.0

## Scope

This runbook defines the first controlled external-repository RepoBrain beta trial.

- trial id: `external-repo-trial-01`
- target repository: `alexworkingai/Elen-MCP-v.2.2.0`
- primary objective: prove install/readiness + ask/review/fix execution path with reproducible artifacts
- out of scope: feature redesign, routing redesign, benchmark redesign, runtime-governance changes

## Preconditions (Operator Checklist)

All items below are required before running commands on a PR.

1. RepoBrain GitHub App is installed for `alexworkingai/Elen-MCP-v.2.2.0`.
2. App permissions match `docs/onboarding/permissions.md`.
3. RepoBrain workflow is present and enabled in the target repository.
4. Required App config is set (ID, installation ID, private key/key path, webhook secret, repository selection config).
5. Repository selection includes `alexworkingai/Elen-MCP-v.2.2.0` when using selected-repo mode.
6. Trial operator has permission to comment on PRs and view workflow artifacts.

## Trial PR Selection Rules

Pick one open PR in `alexworkingai/Elen-MCP-v.2.2.0` with these properties:

1. Same-repo PR (not fork) for deterministic provenance.
2. Contains active diff context (not closed/merged).
3. Small-to-medium scope for Trial #1 (avoid ultra-large edge cases).
4. Low-risk code area where safe `NO_PATCH` is acceptable.

Record selected PR number in the evidence template before execution.

## Command Execution Order

Run commands in this exact order on the selected PR.

1. `/repobrain help`
2. `/repobrain ask --profile balanced <targeted repository question>`
3. `/repobrain review --profile balanced`
4. (optional continuity probe) small safe commit, then `/repobrain review --profile balanced`
5. `/repobrain fix --profile premium <narrow, safe instruction>`

Notes:

- Keep `balanced` as default profile unless explicit trial condition requires another profile.
- `fix --profile cheap` is not part of Trial #1 baseline because review/fix cheap->balanced guardrail is already an accepted contract.

## Artifact Collection Contract

For each command run, collect:

1. workflow run URL and run ID
2. command comment URL
3. artifacts (if generated):
   - `repobrain-install-readiness`
   - `repobrain-audit`
   - `repobrain-diagnostic-summary`
   - `repobrain-tkya-evidence-pack`
   - `repobrain-stability-benchmark` (if present in run path)
4. per-artifact file list and local evidence path

Use `docs/trials/external_repo_trial_evidence_template.md` as the canonical capture sheet.

## Trial Outcome Classification

Classify each stage with one explicit status:

- `READY_TO_PROCEED`
- `BLOCKED_SETUP`
- `COMMAND_WORKED`
- `COMMAND_FAILED`
- `NO_PATCH_SAFE_ACCEPTED`
- `TRIAL_PASS`
- `TRIAL_PARTIAL`
- `TRIAL_BLOCKED`

Classification rules:

1. Readiness failures -> `BLOCKED_SETUP` and stop command trial.
2. Missing artifact required by command path -> `TRIAL_PARTIAL` unless it blocks trust-critical validation.
3. `fix` returning safe `NO_PATCH` with explicit governance is acceptable (`NO_PATCH_SAFE_ACCEPTED`).
4. Trial is `TRIAL_PASS` only if readiness and at least ask+review execute with trustworthy artifacts.

## Stop Conditions (File Product Issue Instead of Improvising)

Stop and open a product issue when any of the following occurs:

1. Readiness result is ambiguous (cannot distinguish missing vs invalid vs unsupported).
2. App/repo binding cannot be validated from operator-visible outputs.
3. Ask/review/fix execution succeeds but trust artifacts are missing in the run path.
4. Provider/profile/provenance truth is contradictory in canonical audit/evidence.

## Rollback / Cleanup Notes

After Trial #1 (or on blocked setup):

1. Remove temporary trial PR comments if required by repo policy.
2. Archive collected artifacts with trial ID label.
3. Remove temporary trial-only repo variables/secrets not needed for ongoing beta.
4. If trial is paused, disable RepoBrain workflow in target repo until next scheduled attempt.
