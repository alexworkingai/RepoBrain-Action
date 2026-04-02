# Installation Shape

## Scope

This document defines how RepoBrain is installed and used across currently supported surfaces.

## Surface 1: GitHub Mode (Primary)

Use when you need PR-native ask/review/fix operation in GitHub.

Required shape:

1. GitHub App onboarding/readiness configured.
2. Repo workflow enabled.
3. Operator readiness verdict is explicit.
4. Commands executed in PR/issue comments.

References:

- `docs/onboarding/github_app_setup.md`
- `docs/onboarding/permissions.md`
- `docs/OPERATOR_QUICKSTART.md`

## Surface 2: External CLI Mode (Bounded)

Use when you need bounded external execution on repository checkout.

Current supported command:

- `ask`

Current unsupported commands:

- `review`
- `fix`

Entrypoint:

```bash
python scripts/run_github.py --mode external --repo-root /path/to/repo --command ask --query "..."
```

## Surface 3: MCP-Facing Surface (Bounded)

Use for structured ask-first integration.

Current supported capability:

- `ask`

Current unsupported capabilities:

- `review`
- `fix`
- any non-ask capability

Entrypoint:

```bash
python scripts/run_mcp_surface.py --capability ask --repo-root /path/to/repo --query "..."
```

## Installation Truth Rule

If a surface is not explicitly marked supported in this document, treat it as unsupported until accepted by a later sprint.
