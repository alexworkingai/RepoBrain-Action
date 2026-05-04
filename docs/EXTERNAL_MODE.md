# RepoBrain External Mode

## Purpose

RepoBrain currently exposes two bounded external paths:

1. External GitHub mode foundation (third-party GitHub-native ask/help path).
2. External CLI mode (ask-only on local checkout).

Both paths are intentionally bounded and must block unsupported capabilities honestly.

## External GitHub Mode Foundation (Third-Party)

Use this when a third-party repository needs GitHub-native command entry via workflow.

Foundation template:

- `docs/packaging/repobrain_external_github_foundation_template.yml`

Contract in this foundation stage:

- supported: `/repobrain help`, `/repobrain doctor`, `/repobrain ask ...`, `/repobrain review` (bounded Review-Lite PR triage)
- unsupported (explicit block): `/repobrain fix`

Runbook and install details:

- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`
- `docs/onboarding/github_app_setup.md`

Use `/repobrain doctor` to verify the external setup surface before first ask/review commands.

## External CLI Mode (Ask-Only)

Entrypoint:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/target/repo \
  --command ask \
  --query "your question"
```

Arguments:

- `--mode external` enables external path.
- `--repo-root` points to repository checkout.
- `--command` currently supports only `ask`.
- `--query` is required for ask.
- `--dry-run` defaults to true and is accepted for parity.
- `--tky-mode` defaults to `auto`.

Support in CLI external mode:

- `ask`: supported
- `review`: unsupported (blocked)
- `fix`: unsupported (blocked)
- any other command: unsupported (blocked)

Block behavior is explicit:

- `status=blocked`
- `decision=UNSUPPORTED_COMMAND`
- message includes requested unsupported command

## Runtime Behavior (CLI External Ask)

For supported ask path, external CLI mode:

1. loads config from target repo root,
2. builds external index package,
3. runs retrieval over indexed chunks,
4. synthesizes ask answer via local provider path.

No `GITHUB_TOKEN` is required for this external CLI ask flow.

## What External Mode Is Not (Yet)

External mode is not currently:

- full ask/review/fix parity on third-party GitHub repositories,
- replacement for primary GitHub-mode review/fix runtime,
- complete third-party repo automation surface.

## Trial Usage Reference

- Trial runbook: `docs/trials/external_repo_trial_01_elen_mcp.md`
- Reusable trial template: `docs/trials/external_repo_trial_template.md`
- Evidence template: `docs/trials/external_repo_trial_evidence_template.md`
- Trial #1 report: `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- MCP-facing adapter: `docs/MCP_SURFACE.md`
