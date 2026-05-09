# External Repo Trial #01 Runbook - alexworkingai/Elen-MCP-v.2.2.0

> Historical artifact notice
>
> This document is a historical external trial artifact. It reflects the RepoBrain surface and validation posture at the time of the original Elen-MCP trial and is not the current command-surface truth.
>
> Current public external GitHub foundation truth after Sprint 78:
> - `/repobrain doctor`
> - `/repobrain help`
> - `/repobrain ask <question>`
> - `/repobrain review` as bounded read-only Review Candidate
> - `/repobrain fix` as bounded Fix-Lite Candidate manual-only patch suggestion
>
> Mandatory Fix-Lite boundary:
> - `No patch was applied. No files were modified.`
>
> For current operator guidance, use:
> - `docs/EXTERNAL_MODE.md`
> - `docs/USER_GUIDE.md`
> - `docs/OPERATOR_QUICKSTART.md`
> - `docs/benchmarks/current_capabilities_matrix.md`

## Scope

This runbook defines the first controlled external-repository RepoBrain beta trial.

- trial id: `external-repo-trial-01`
- target repository: `alexworkingai/Elen-MCP-v.2.2.0`
- primary objective: prove install/readiness + external ask execution path with reproducible artifacts
- out of scope: feature redesign, routing redesign, benchmark redesign, runtime-governance changes

## Preconditions (Operator Checklist)

All items below are required before running commands on a PR.

1. RepoBrain GitHub App is installed for `alexworkingai/Elen-MCP-v.2.2.0` (for GitHub-mode readiness validation).
2. App permissions match `docs/onboarding/permissions.md`.
3. Required App config is set (ID, installation ID, private key/key path, webhook secret, repository selection config).
4. Trial operator can access workflow logs/artifacts in the target repository.
5. Local checkout of `alexworkingai/Elen-MCP-v.2.2.0` exists for external CLI trial.
6. Python environment is ready to run `scripts/run_github.py` from RepoBrain-Action workspace.

## Trial PR / Scope Selection Rules

Pick one active code area in `alexworkingai/Elen-MCP-v.2.2.0` with these properties:

1. Small-to-medium scope for Trial #1 (avoid ultra-large edge cases).
2. Clear module boundaries for ask verification.
3. Low-risk area where honest unsupported review/fix behavior can be validated without ambiguity.

Record selected module/question scope in the evidence template before execution.

## Command Execution Order (External Mode)

Run commands in this exact order from terminal.

1. `python scripts/run_github.py --mode external --repo-root <repo_path> --command ask --query "<targeted repository question>"`
2. (optional continuity probe) rerun external ask with a narrower follow-up query
3. negative check: `python scripts/run_github.py --mode external --repo-root <repo_path> --command review --query "<probe>"` to confirm honest unsupported block

Notes:

- External mode currently supports only `ask`.
- `review` and `fix` are expected to block as unsupported in external mode.
- GitHub-native review/fix validation should be executed in GitHub mode, not external mode.

## Artifact Collection Contract

For each command run, collect:

1. full command string and timestamp
2. terminal/stdout snapshot containing `STATUS` and `DECISION`
3. generated artifacts/logs (if present):
   - `repobrain-install-readiness`
   - `repobrain-audit`
   - `repobrain-diagnostic-summary`
   - `repobrain-tkya-evidence-pack`
   - `<repo_root>/artifacts/external_flow_index.zip`
4. local evidence archive path

Use `docs/trials/external_repo_trial_evidence_template.md` as the canonical capture sheet.

## Trial Outcome Classification

Classify each stage with one explicit status:

- `READY_TO_PROCEED`
- `BLOCKED_SETUP`
- `COMMAND_WORKED`
- `COMMAND_FAILED`
- `TRIAL_PASS`
- `TRIAL_PARTIAL`
- `TRIAL_BLOCKED`

Classification rules:

1. Readiness failures -> `BLOCKED_SETUP` and stop command trial.
2. External ask success + explicit unsupported review block -> valid trial progression.
3. Missing trust artifact/log evidence -> `TRIAL_PARTIAL` unless it blocks verdict confidence.
4. Trial is `TRIAL_PASS` only if readiness is clear, external ask succeeds, and unsupported review block is explicit/honest.

## Stop Conditions (File Product Issue Instead of Improvising)

Stop and open a product issue when any of the following occurs:

1. Readiness result is ambiguous (cannot distinguish missing vs invalid vs unsupported).
2. External ask path fails without deterministic reason.
3. Unsupported command does not block explicitly.
4. Provider/profile/provenance truth is contradictory in canonical audit/evidence.

## Rollback / Cleanup Notes

After Trial #1 (or on blocked setup):

1. Archive collected artifacts with trial ID label.
2. Remove temporary trial-only variables/secrets not needed for continued beta.
3. If trial is paused, disable temporary trial workflow wiring in target repository.
4. Record blocker codes and next actions in trial summary.