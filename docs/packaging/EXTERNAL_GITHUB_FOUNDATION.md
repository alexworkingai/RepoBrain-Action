# External GitHub Foundation Boundary

## Purpose

This document is a RepoBrain-Action boundary reference for the public external
GitHub foundation surface.

RepoBrain-Action is not the public runtime or install-template host for this
surface. The canonical public host and install kit live in
`repobrain-community`.

## Canonical Public Host

Use these community-owned public artifacts for third-party GitHub-native setup:

- install template: `repobrain-community/templates/repobrain.yml`
- reusable workflow host:
  `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`

For current public install steps and examples, use the `repobrain-community`
README and template files rather than local copies in RepoBrain-Action.

## Current Public Command Truth

Supported in the external GitHub foundation:

- `/repobrain doctor`
- `/repobrain help`
- `/repobrain ask ...`
- `/repobrain review` (bounded read-only Review Candidate)
- `/repobrain fix` (bounded Fix-Lite Candidate manual-only patch suggestion)

Unsupported:

- out-of-contract commands

## Bounded Non-Claims

The public external GitHub foundation does not claim:

- autofix
- patch application
- file modification
- commit creation
- branch pushing
- PR creation
- full review parity
- security verdicts
- safe-to-merge claims
- approval/rejection verdicts
- autonomous repair behavior

Mandatory Fix-Lite boundary:

- `No patch was applied. No files were modified.`

## What Stays In RepoBrain-Action

RepoBrain-Action remains the source of:

- current-truth docs and capability alignment,
- governance and regression tests,
- bounded external CLI ask-only and MCP ask-only secondary surfaces.

Use these local docs for current operator/context references:

- `docs/REPO_BOUNDARY_CONTRACT.md`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/benchmarks/current_capabilities_matrix.md`
