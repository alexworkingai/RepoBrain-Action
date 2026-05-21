# RepoBrain External Mode

## Purpose

RepoBrain currently exposes three external-facing paths:

1. Direct external repository pilot install from `RepoBrain-Action`.
2. External CLI mode (ask-only on local checkout).
3. MCP ask-first integration surface.

The old `repobrain-community` bridge is retired from the working product architecture and is not required for current onboarding.

## External Repository Pilot (Direct GitHub Path)

Use this when a pilot repository needs GitHub-native command entry via workflow.

Current direct pilot install truth:

- the caller repository owns `.github/workflows/repobrain.yml`
- the workflow uses `alexworkingai/RepoBrain-Action@main`
- the caller repository provides a private TopoCore v6 checkout token
- Sprint 69 smoke target is issue and PR `ask` with visible v6 backend evidence

Install and architecture references:

- `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`
- `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- `docs/examples/repobrain_external_pilot_workflow.yml`
- `docs/examples/repobrain.instructions.md`

Bounded non-claims remain in force:

- no patch application
- no file modification
- no commit creation
- no branch pushing
- no PR creation by RepoBrain behavior
- no security verdicts
- no safe-to-merge claims
- no approval/rejection verdicts
- no autofix

## External CLI Mode (Ask-Only)

Entrypoint:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/target/repo \
  --command ask \
  --query "your question"
```

Support in CLI external mode:

- `ask`: supported
- `review`: unsupported (blocked)
- `fix`: unsupported (blocked)
- any other command: unsupported (blocked)

## MCP Surface (Ask-Only)

Entrypoint:

```bash
python scripts/run_mcp_surface.py \
  --capability ask \
  --repo-root /path/to/repo \
  --query "your question"
```

Supported now: `ask` only.

Unsupported capability requests must block explicitly.

## Trial Usage Reference

- Historical Sprint 59 trial runbook artifact: `docs/trials/external_repo_trial_01_elen_mcp.md`
- Reusable trial template: `docs/trials/external_repo_trial_template.md`
- Evidence template: `docs/trials/external_repo_trial_evidence_template.md`
- Historical benchmark narrative artifact: `docs/benchmarks/external_trial_01_elen_mcp_report.md`
- MCP-facing adapter: `docs/MCP_SURFACE.md`
