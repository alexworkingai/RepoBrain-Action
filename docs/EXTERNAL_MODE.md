# RepoBrain External Mode

## Purpose

External mode provides a controlled CLI execution path for third-party repository trials without requiring GitHub issue-comment runtime wiring.

Current status: **ask-first / ask-only**.

## Entrypoint

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/target/repo \
  --command ask \
  --query "your question"
```

Arguments:

- `--mode external` enables external path
- `--repo-root` points to repository checkout
- `--command` currently supports only `ask`
- `--query` is required for ask
- `--dry-run` defaults to true and is accepted for parity
- `--tky-mode` defaults to `auto`

## Support Matrix (External Mode)

- `ask`: supported
- `review`: unsupported (blocked)
- `fix`: unsupported (blocked)
- any other command: unsupported (blocked)

Block behavior is explicit:

- `status=blocked`
- `decision=UNSUPPORTED_COMMAND`
- message includes requested unsupported command

## Runtime Behavior

For supported ask path, external mode:

1. loads config from target repo root,
2. builds external index package,
3. runs retrieval over indexed chunks,
4. synthesizes ask answer via local provider path.

No `GITHUB_TOKEN` is required for this external ask flow.

## What External Mode Is Not (Yet)

External mode is not currently:

- full PR-native GitHub review/fix runtime,
- replacement for GitHub App installation/readiness flow,
- complete third-party repo automation surface.

For review/fix in PR context, use GitHub mode in the target repository.

## Trial Usage Reference

- Trial runbook: `docs/trials/external_repo_trial_01_elen_mcp.md`
- Reusable template: `docs/trials/external_repo_trial_template.md`
- Evidence template: `docs/trials/external_repo_trial_evidence_template.md`
- Trial #1 report: `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- MCP-facing adapter: `docs/MCP_SURFACE.md`
