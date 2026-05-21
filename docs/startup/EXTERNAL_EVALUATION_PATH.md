# External Evaluation Path

## Scope

This path shows what each surface proves today for third-party evaluation.

## Path A: GitHub Mode (Primary Product Proof)

What to run:

- `/repobrain help`
- `/repobrain ask --profile balanced ...`
- `/repobrain review --profile balanced`
- `/repobrain fix --profile premium ...`

What it proves:

- primary product behavior in PR-native workflow,
- governance-aware behavior,
- artifact-backed observability.

## Path B: External Repository Pilot (Direct Product Proof)

What to run in a pilot repository:

- install the caller workflow from `docs/examples/repobrain_external_pilot_workflow.yml`
- configure private TopoCore v6 access
- run issue `/repobrain ask ...`
- run PR `/repobrain ask ...`

What it proves:

- real external repository wiring directly to `RepoBrain-Action`
- visible v6 backend evidence in the consumer repository
- no `repobrain-community` dependency in the active install path

What it does not prove:

- full external command-matrix parity,
- patch application, file modification, commit creation, branch pushing, or PR creation,
- security verdicts, safe-to-merge claims, or approval/rejection decisions.

## Path C: External CLI Mode (Bounded Proof)

What to run:

```bash
python scripts/run_github.py --mode external --repo-root /path/to/repo --command ask --query "..."
```

Optional negative check:

```bash
python scripts/run_github.py --mode external --repo-root /path/to/repo --command review --query "..."
```

What it proves:

- real third-party ask execution path.

## Path D: MCP Surface (Bounded Integration Proof)

What to run:

```bash
python scripts/run_mcp_surface.py --capability ask --repo-root /path/to/repo --query "..."
```

Unsupported check:

```bash
python scripts/run_mcp_surface.py --capability review --repo-root /path/to/repo --query "..."
```

What it proves:

- structured ask-first integration surface,
- honest unsupported blocking for out-of-scope capability.

## Evaluation Integrity Rule

If any path claim exceeds what was actually validated, classify result as partial and document the gap explicitly.
