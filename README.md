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

### External repository pilot (direct RepoBrain-Action install)

RepoBrain-Action now owns the external repository pilot install path directly.

Current pilot shape:

- workflow lives in the consumer repository
- action ref is `alexworkingai/RepoBrain-Action@main`
- TopoCore v6 stays private and is checked out separately with a repo secret
- `repobrain-community` is retired from the working product architecture and is not required

Current Sprint 69 validation target:

- issue `/repobrain ask ...`
- PR `/repobrain ask ...`
- visible backend evidence showing `resolved_backend=v6`

Primary operator references:

- `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`
- `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- `docs/examples/repobrain_external_pilot_workflow.yml`

### External CLI mode (bounded surface)

CLI entrypoint:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/repo \
  --command ask \
  --query "What changed in module X?"
```

Current external CLI support:

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
- `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`

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
- External repository pilot install: `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`
- External product architecture: `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- Repository boundary contract: `docs/REPO_BOUNDARY_CONTRACT.md`
- MCP surface contract: `docs/MCP_SURFACE.md`
- Trial template: `docs/trials/external_repo_trial_template.md`
- Historical Sprint 59 trial runbook artifact: `docs/trials/external_repo_trial_01_elen_mcp.md`
- Historical benchmark narrative artifact: `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- Capabilities matrix: `docs/benchmarks/current_capabilities_matrix.md`
- Environment reference: `docs/env_reference.md`
- Team governance layer: `docs/governance/TEAM_GOVERNANCE.md`
- Packaging overview: `docs/packaging/PACKAGING_OVERVIEW.md`
- Startup readiness: `docs/startup/STARTUP_READINESS.md`
- Strategic attention pack: `docs/strategy/ATTENTION_PACK_INDEX.md`

## Scope Boundaries

RepoBrain currently does not claim:

- full production-ready external rollout across arbitrary repositories,
- autofix or patch application by default,
- Marketplace/admin-portal product surface.

This repository intentionally keeps protected kernel internals out of public-facing operator documentation.
