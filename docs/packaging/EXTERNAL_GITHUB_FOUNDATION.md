# External GitHub Foundation (Pilot)

## Purpose

This document describes the current external repository pilot install shape.
RepoBrain-Action is now the direct product host for the pilot workflow.

## Current Install Truth

Use these files for direct pilot setup:

- install guide: `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`
- product architecture: `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- example workflow: `docs/examples/repobrain_external_pilot_workflow.yml`
- example repo guidance: `docs/examples/repobrain.instructions.md`

Direct pilot workflow shape:

- caller repository owns `.github/workflows/repobrain.yml`
- workflow uses `alexworkingai/RepoBrain-Action@main`
- private TopoCore v6 checkout remains required
- `repobrain-community` is retired and not required

## Current Safety Boundaries

The direct external pilot does not claim:

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

Mandatory boundary:

- `No patch was applied. No files were modified.`
