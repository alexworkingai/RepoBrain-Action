# Release Integrity And Provenance

## Purpose

This document defines the release-integrity and provenance rules required before public visibility and partner pinning should be treated as production-grade.

## Current Release State

- no public RC tag has been created
- Sprint 86 does not create a public release tag without explicit owner approval
- current operational reference remains `main` for controlled pilot use only

## Tag Policy

- annotated tags are preferred
- tags are immutable trust anchors
- do not rewrite public tags
- tag creation remains owner-approved only

## Pinning Guidance

- once an approved RC tag exists, partner testing should prefer pinned tag or SHA
- `@main` remains acceptable only for tightly controlled pre-RC pilot use
- public-facing partner guidance should avoid floating refs once an RC tag exists

## SBOM

- SBOM generation workflow: `.github/workflows/sbom.yml`
- intended output: CycloneDX JSON artifact for the built package/runtime surface
- current Sprint 86 status: prepared as a release-adjacent integrity gate

## Provenance

- provenance workflow: `.github/workflows/provenance.yml`
- artifact attestation is prepared as an approval-gated path
- current status: prepared, not yet claimed as exercised in a public release flow

## Release Checklist Integration

Release integrity must align with:

- `docs/release/RC_TAG_AND_PINNING_PLAN.md`
- `docs/release/RELEASE_CANDIDATE_CHECKLIST.md`
- `docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md`

## Rollback Limitations

- once a public tag is pushed, consumers may pin or mirror it
- public tags should therefore not be rewritten
- public visibility also has clone persistence risk independent of tag policy

## Approval Gate

- explicit owner approval is required before RC tag creation
- explicit owner approval is required before public visibility switch

## Current Status

- `RC_TAG_READY_PENDING_OWNER_APPROVAL`
