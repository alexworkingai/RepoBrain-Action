# RepoBrain User Guide (Current Reality)

## What RepoBrain Is

RepoBrain is a governed repository/PR decision runtime for GitHub workflows.
It emphasizes:

- evidence-grounded answers and review output,
- explicit governance for patch/no_patch decisions,
- compact primary PR output with deeper diagnostics in artifacts/details.

## Modes You Can Use Today

### GitHub Mode (`issue_comment` workflow)

Use inside PR/issue comments:

- `/repobrain help`
- `/repobrain ask ...`
- `/repobrain review`
- `/repobrain fix ...`

Execution profile flags are user-facing:

- `--profile cheap|balanced|premium`
- default remains `balanced`
- safety guardrail: review/fix normalize `cheap -> balanced` with explicit audit truth

### External CLI Mode (`scripts/run_github.py --mode external`)

Current support is intentionally narrow:

- supported: `ask`
- unsupported (blocked honestly): `review`, `fix`, and other non-ask commands

Canonical entrypoint:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/repo \
  --command ask \
  --query "What does module X do?"
```

### MCP-Facing Surface (`scripts/run_mcp_surface.py`)

Thin ask-first structured surface for integration workflows:

```bash
python scripts/run_mcp_surface.py \
  --capability ask \
  --repo-root /path/to/repo \
  --query "What changed around module X?"
```

Supported now: `ask` only.

## What Works vs Not Yet

### Works Today

- GitHub mode ask/review/fix on configured repositories.
- External mode ask execution on third-party repository checkouts.
- Operator readiness contract for GitHub App onboarding.
- Evidence/audit artifact generation, including TKYA evidence pack.

### Not Yet (Explicitly)

- External mode review/fix execution.
- MCP surface review/fix capabilities.
- Full GitHub-native PR runtime inside arbitrary third-party repositories from external mode alone.
- Marketplace-style product packaging/admin portal.

## Artifacts You Should Expect

Depending on command and mode:

- `repobrain-audit`
- `repobrain-diagnostic-summary`
- `repobrain-tkya-evidence-pack`
- `repobrain-install-readiness` (on readiness/onboarding path)
- `repobrain-stability-benchmark` (GitHub benchmark path)

## Where To Go Next

- Operator install/readiness: `docs/OPERATOR_QUICKSTART.md`
- External mode details: `docs/EXTERNAL_MODE.md`
- MCP surface details: `docs/MCP_SURFACE.md`
- Packaging overview: `docs/packaging/PACKAGING_OVERVIEW.md`
- Trial protocol/templates: `docs/trials/external_repo_trial_template.md`
- Trial #1 runbook: `docs/trials/external_repo_trial_01_elen_mcp.md`
- Trial #1 benchmark narrative: `docs/benchmarks/external_trial_01_elen_mcp_report.md`
