# External GitHub Mode Foundation (Third-Party Repositories)

## Purpose

This document defines the Sprint 66 foundation for third-party GitHub-native RepoBrain usage.

It provides a bounded, product-shaped install path for external repositories without claiming full command parity.

## Current Capability Boundary

Supported in external GitHub mode foundation:

- `/repobrain help`
- `/repobrain ask ...`

Explicitly unsupported (blocked with clear boundary message):

- `/repobrain review`
- `/repobrain fix`
- non-RepoBrain or out-of-contract commands

## Installation Shape (Third-Party Repo)

1. Install the RepoBrain GitHub App to the target repository (selected-repo rollout recommended).
2. Add `.github/workflows/repobrain_external.yml` using:
   - `docs/packaging/repobrain_external_github_foundation_template.yml`
   - reusable host: `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`
3. Configure required secrets/variables:
   - `RB_GH_APP_ID`
   - `RB_GH_APP_INSTALLATION_ID`
   - `RB_GH_APP_PRIVATE_KEY` (recommended) or `RB_GH_APP_PRIVATE_KEY_PATH`
   - `RB_GH_APP_REPOSITORY_SELECTION`
   - `RB_GH_APP_SELECTED_REPOS` (when selection mode is `selected`)
4. Trigger `/repobrain help` on an open PR first, then `/repobrain ask ...`.

## Expected Artifacts

The foundation workflow uploads operator-readable artifacts:

- `repobrain-install-readiness`
- `repobrain-audit`
- `repobrain-diagnostic-summary`
- `repobrain-tkya-evidence-pack`

If command is out of boundary, readiness still publishes while unsupported command behavior remains explicit.

## Third-Party Trial Runbook (Minimal)

1. Open PR in target external repository.
2. Post `/repobrain help`.
3. Verify:
   - workflow executed,
   - readiness artifact exists,
   - boundary/output is compact and readable.
4. Post `/repobrain ask <question>`.
5. Verify:
   - ask response published,
   - audit/diagnostic/evidence artifacts uploaded.
6. Optional negative check: `/repobrain review`.
7. Verify unsupported behavior is explicit and does not pretend support.

## Stop Conditions

Stop and file a product issue instead of improvising if:

1. readiness artifact is missing or contradictory,
2. supported/unsupported behavior does not match this contract,
3. setup requires copying internal monolithic workflows,
4. outward docs or workflow text would expose protected kernel internals.
