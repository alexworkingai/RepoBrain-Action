# RepoBrain External Mode

## Purpose

RepoBrain currently exposes three external-facing paths:

1. direct external repository install from `RepoBrain-Action`
2. external CLI mode
3. MCP ask-first integration surface

The canonical external GitHub install and support path is now:

- `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- `docs/commands/REPOBRAIN_COMMANDS.md`
- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

The old `repobrain-community` bridge is retired from the working product architecture and is not required.

## External Repository Pilot (Direct GitHub Path)

Current direct pilot truth:

- the caller repository owns `.github/workflows/repobrain.yml`
- the workflow uses `alexworkingai/RepoBrain-Action@main`
- private TopoCore v6 is checked out separately with `TOPOCORE_V6_REPO_TOKEN`
- example workflow: `docs/examples/repobrain_external_pilot_workflow.yml`
- no autofix
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior

## External CLI Mode

Current support is intentionally narrow:

- supported: `ask`
- unsupported: non-ask commands

Entrypoint:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/target/repo \
  --command ask \
  --query "your question"
```

## MCP Surface

Current MCP-facing support is also ask-first only.

Entrypoint:

```bash
python scripts/run_mcp_surface.py \
  --capability ask \
  --repo-root /path/to/repo \
  --query "your question"
```
