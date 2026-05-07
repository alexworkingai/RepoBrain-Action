# Packaging Overview (Pre-Marketplace)

## Purpose

This package defines how RepoBrain is prepared for repeatable installation and operator handoff before any Marketplace-level distribution.

It is a pre-distribution hardening layer, not a feature-expansion sprint.

## Current Product Shape

RepoBrain currently exposes four bounded surfaces:

1. GitHub mode (primary): ask/review/fix in comment-driven workflow.
2. External GitHub mode foundation (bounded): doctor/help/ask plus bounded read-only Review Candidate and bounded Fix-Lite Candidate manual-only patch suggestion.
3. External CLI mode (bounded): ask only.
4. MCP-facing surface (bounded): ask only.

## Packaging Objectives

This packaging layer provides:

- install/use clarity,
- preflight and validation checklists,
- explicit supported/unsupported boundaries,
- operator-safe handoff guidance,
- protected-kernel-safe outward wording.

## Not Included

This packaging layer does not include:

- Marketplace launch,
- admin/billing portal,
- patch application, file modification, commit creation, branch pushing, or PR creation in the external public surface,
- MCP capability expansion beyond ask,
- runtime architecture redesign.

## Packaging Index

- Installation shape: `docs/packaging/INSTALLATION_SHAPE.md`
- Capability surfaces: `docs/packaging/CAPABILITY_SURFACES.md`
- External GitHub foundation runbook: `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`
- Preflight checklist: `docs/packaging/PREFLIGHT_CHECKLIST.md`
- Validation checklist: `docs/packaging/VALIDATION_CHECKLIST.md`
- Distribution boundaries: `docs/packaging/DISTRIBUTION_BOUNDARIES.md`
- Startup-readiness layer: `docs/startup/STARTUP_READINESS.md`
