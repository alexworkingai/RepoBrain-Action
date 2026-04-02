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

What it does not prove:

- external CLI parity for review/fix.

## Path B: External CLI Mode (Bounded Proof)

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

What it does not prove:

- external review/fix support.

## Path C: MCP Surface (Bounded Integration Proof)

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
