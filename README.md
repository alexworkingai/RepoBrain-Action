# RepoBrain Action

Current release candidate: `0.5.0-rc.1`

RepoBrain is a governed repository cognition runtime for GitHub workflows.
It provides compact decision outputs, explicit safety governance, and auditable artifacts while keeping the protected internal kernel undisclosed.

## What Works Today

### GitHub mode (primary runtime)

Run in PR/issue comments:

- `/repobrain help`
- `/repobrain ask ...`
- `/repobrain review`
- `/repobrain fix ...`

Execution profile controls:

- `--profile cheap|balanced|premium`
- default: `balanced`
- safety guardrail: review/fix requests for `cheap` are normalized to governed `balanced`

### External mode (bounded surface)

Third-party GitHub-native foundation (bounded):

- template: `docs/packaging/repobrain_external_github_foundation_template.yml`
- supported: `/repobrain help`, `/repobrain ask ...`
- unsupported (explicit block): `/repobrain review`, `/repobrain fix`

CLI entrypoint:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/repo \
  --command ask \
  --query "What changed in module X?"
```

Current external support:

- supported: `ask`
- unsupported (explicit block): `review`, `fix`, other non-ask commands

### MCP-facing bounded surface (ask-first)

CLI adapter:

```bash
python scripts/run_mcp_surface.py \
  --capability ask \
  --repo-root /path/to/repo \
  --query "What changed in module X?"
```

- supported capability: `ask`
- unsupported capability requests are blocked explicitly with structured public-safe responses

## Readiness and Operator Path

GitHub App onboarding/readiness references:

- `docs/onboarding/github_app_setup.md`
- `docs/onboarding/permissions.md`

Readiness artifacts:

- `artifacts/onboarding/repobrain_install_readiness.json`
- `artifacts/onboarding/repobrain_install_readiness.md`

## Artifacts

Common artifacts include:

- `repobrain-audit`
- `repobrain-diagnostic-summary`
- `repobrain-tkya-evidence-pack`
- `repobrain-install-readiness`
- `repobrain-stability-benchmark` (when benchmark path is active)

## Documentation Index

- User guide: `docs/USER_GUIDE.md`
- Operator quickstart: `docs/OPERATOR_QUICKSTART.md`
- External mode: `docs/EXTERNAL_MODE.md`
- External GitHub foundation: `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`
- MCP surface contract: `docs/MCP_SURFACE.md`
- Trial template: `docs/trials/external_repo_trial_template.md`
- Trial #1 runbook: `docs/trials/external_repo_trial_01_elen_mcp.md`
- Trial #1 narrative: `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- Capabilities matrix: `docs/benchmarks/current_capabilities_matrix.md`
- Environment reference: `docs/env_reference.md`
- Team governance layer: `docs/governance/TEAM_GOVERNANCE.md`
- Packaging overview: `docs/packaging/PACKAGING_OVERVIEW.md`
- Startup readiness: `docs/startup/STARTUP_READINESS.md`
- Strategic attention pack: `docs/strategy/ATTENTION_PACK_INDEX.md`

## Scope Boundaries

RepoBrain currently does not claim:

- full external GitHub-native review/fix runtime,
- external review/fix support in CLI external mode,
- marketplace/admin-portal product surface.

This repository intentionally keeps protected kernel internals out of public-facing operator documentation.
