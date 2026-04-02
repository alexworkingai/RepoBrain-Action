# Packaging Overview (Pre-Marketplace)

## Purpose

This package defines how RepoBrain is prepared for repeatable installation and operator handoff before any Marketplace-level distribution.

It is a pre-distribution hardening layer, not a feature-expansion sprint.

## Current Product Shape

RepoBrain currently exposes three bounded surfaces:

1. GitHub mode (primary): ask/review/fix in comment-driven workflow.
2. External CLI mode (bounded): ask only.
3. MCP-facing surface (bounded): ask only.

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
- external review/fix support,
- MCP capability expansion beyond ask,
- runtime architecture redesign.

## Packaging Index

- Installation shape: `docs/packaging/INSTALLATION_SHAPE.md`
- Capability surfaces: `docs/packaging/CAPABILITY_SURFACES.md`
- Preflight checklist: `docs/packaging/PREFLIGHT_CHECKLIST.md`
- Validation checklist: `docs/packaging/VALIDATION_CHECKLIST.md`
- Distribution boundaries: `docs/packaging/DISTRIBUTION_BOUNDARIES.md`
