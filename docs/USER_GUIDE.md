# RepoBrain User Guide (Current Reality)

## What RepoBrain Is

RepoBrain is a governed repository/PR decision runtime for GitHub workflows.
It emphasizes:

- evidence-grounded answers and review output,
- explicit governance for patch/no_patch decisions,
- compact primary PR output with deeper diagnostics in artifacts/details.

## Modes You Can Use Today

### GitHub Mode (`issue_comment` workflow)

Use inside PR/issue comments:

- `/repobrain help`
- `/repobrain ask ...`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix ...`

Execution profile flags are user-facing:

- `--profile cheap|balanced|premium`
- default remains `balanced`
- safety guardrail: review/fix normalize `cheap -> balanced` with explicit audit truth

### External Repository Pilot (Direct)

GitHub-native bounded entry path for external repositories now installs directly from `RepoBrain-Action`.

Current direct pilot truth:

- action ref: `alexworkingai/RepoBrain-Action@main`
- TopoCore v6 remains private and is checked out separately with a private repo token
- `repobrain-community` is retired from the working architecture and is not required
- Sprint 69 pilot smoke target is issue/PR `ask` with visible v6 backend evidence

Primary install reference:

- `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`

Architecture reference:

- `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`

Example caller workflow:

- `docs/examples/repobrain_external_pilot_workflow.yml`

### External CLI Mode (`scripts/run_github.py --mode external`)

Current support is intentionally narrow:

- supported: `ask`
- unsupported (blocked honestly): `review`, `fix`, and other non-ask commands

Canonical entrypoint:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /path/to/repo \
  --command ask \
  --query "What does module X do?"
```

### MCP-Facing Surface (`scripts/run_mcp_surface.py`)

Thin ask-first structured surface for integration workflows:

```bash
python scripts/run_mcp_surface.py \
  --capability ask \
  --repo-root /path/to/repo \
  --query "What changed around module X?"
```

Supported now: `ask` only.

## What Works vs Not Yet

### Works Today

- GitHub mode ask/review/fix on configured repositories.
- GitHub mode verify on PRs with informational verification status reporting.
- Direct external repository pilot install from `RepoBrain-Action`.
- External mode ask execution on third-party repository checkouts.
- Operator readiness contract for GitHub App onboarding.
- Evidence/audit artifact generation, including TKYA evidence pack.

### Not Yet (Explicitly)

- Autofix execution in any external surface.
- MCP surface review/fix capabilities.
- Broad production rollout claims for third-party repositories.
- Marketplace-style product packaging/admin portal.

### Verify Semantics

- issue scope:
  - `/repobrain verify` stays scoped unsupported and directs users to PR context
- PR scope:
  - `/repobrain verify` reports observed GitHub verification signals only
  - status labels:
    - `PASS`
    - `WARN`
    - `FAIL`
    - `PENDING`
    - `NOT_RUN`
    - `UNKNOWN`
  - informational only:
    - not merge approval
    - not security approval

### Fix Semantics

- issue scope:
  - `/repobrain fix` stays scoped unsupported and explicitly reports no mutation
- PR scope:
  - `/repobrain fix` is proposal/governance only
  - possible product statuses:
    - `PROPOSAL_READY`
    - `NO_ACTION_NEEDED`
    - `NEEDS_MORE_INFORMATION`
    - `UNSUPPORTED_SCOPE`
    - `BLOCKED_BY_SAFETY`
    - `ERROR_SANITIZED`
  - visible safety gates should show:
    - `patch_authorized=false`
    - `patch_applied=false`
    - `files_modified=false`
    - `branch_created=false`
    - `commit_created=false`
    - `pr_created=false`
  - informational only:
    - not patch application
    - not merge approval
    - not security approval

## Artifacts You Should Expect

Depending on command and mode:

- `repobrain-audit`
- `repobrain-diagnostic-summary`
- `repobrain-tkya-evidence-pack`
- `repobrain-install-readiness` (on readiness/onboarding path)
- `repobrain-stability-benchmark` (GitHub benchmark path)

## Where To Go Next

- Operator install/readiness: `docs/OPERATOR_QUICKSTART.md`
- External repository pilot install: `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`
- External product architecture: `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- External mode details: `docs/EXTERNAL_MODE.md`
- Packaging overview: `docs/packaging/PACKAGING_OVERVIEW.md`
- Startup readiness: `docs/startup/STARTUP_READINESS.md`
- Historical Sprint 59 trial runbook artifact: `docs/trials/external_repo_trial_01_elen_mcp.md`
- Historical benchmark narrative artifact: `docs/benchmarks/external_trial_01_elen_mcp_report.md`
