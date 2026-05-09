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

## Path B: External GitHub Mode Foundation (Bounded Public Proof)

Public runtime host:

- `repobrain-community`

What to run in a third-party repository:

- install the caller workflow from the public community template
- `/repobrain doctor`
- `/repobrain help`
- `/repobrain ask ...`
- `/repobrain review`
- `/repobrain fix`

What it proves:

- real third-party GitHub-native bounded public runtime,
- doctor/help truth is externally visible,
- review is available as bounded read-only Review Candidate,
- fix is available as bounded Fix-Lite Candidate manual-only patch suggestion,
- duplicate-response regressions remain absent.

What it does not prove:

- full external ask/review/fix parity,
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

What it does not prove:

- external CLI review/fix support.

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
