# Preflight Checklist

Use this checklist before handing RepoBrain to an operator/deployer.

## A. Baseline and Scope

1. Confirm target work stays within accepted surfaces.
2. Confirm no unsupported capability is being promised.
3. Confirm protected-kernel policy is acknowledged.

## B. Setup Prerequisites

1. Python environment is available for scripts.
2. Repository checkout is available for local/external validation.
3. GitHub permissions/secrets/variables are configured for GitHub mode readiness checks.

## C. Surface-Specific Preconditions

### GitHub mode

1. Readiness flow can produce explicit verdict.
2. Expected artifacts are accessible.
3. Operator can trigger `/repobrain help`.

### External GitHub mode foundation

1. Caller workflow is installed from the reusable external foundation template.
2. Operator understands the current bounded public command surface:
   - `/repobrain doctor`
   - `/repobrain help`
   - `/repobrain ask ...`
   - `/repobrain review` as bounded read-only Review Candidate
   - `/repobrain fix` as bounded Fix-Lite Candidate manual-only patch suggestion
3. Readiness artifacts are expected on each run.
4. Operator understands the mandatory Fix-Lite no-action guarantee:
   - `No patch was applied. No files were modified.`

### External mode (CLI)

1. `scripts/run_github.py --mode external` is callable.
2. Local path for target repository is known.
3. Operator understands ask-only boundary.

### MCP surface

1. `scripts/run_mcp_surface.py` is callable.
2. Operator understands ask-only capability boundary.
3. Unsupported capability block behavior is understood.

## D. Stop Conditions

Stop and escalate before running trials if:

1. Supported boundary is unclear.
2. Readiness classification is ambiguous.
3. Setup requires out-of-scope feature expansion.
4. Outward text would disclose protected-kernel internals.
