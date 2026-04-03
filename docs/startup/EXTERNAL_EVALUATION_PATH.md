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

What to run (GitHub-native foundation in third-party repo):

- install caller workflow from `docs/packaging/repobrain_external_github_foundation_template.yml`
- `/repobrain help`
- `/repobrain ask ...`
- optional negative check: `/repobrain review`

What it proves:

- real third-party GitHub-native bounded foundation,
- explicit unsupported behavior for out-of-scope commands.

What it does not prove:

- full external ask/review/fix parity.

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

What it does not prove:

- external review/fix support.

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
