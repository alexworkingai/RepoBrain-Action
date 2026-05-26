# Supply-Chain Security Baseline

## Purpose

This document defines the minimum supply-chain and release-trust baseline required before RepoBrain-Action can safely switch to public visibility.

## SECURITY.md

Root `SECURITY.md` now exists and defines:

- current support status
- private pre-public state
- security reporting expectations
- no TopoCore source disclosure
- no secret disclosure in public channels
- partner pilot incident guidance

## CODEOWNERS

`.github/CODEOWNERS` now establishes explicit ownership for:

- `action.yml`
- `.github/workflows/`
- `repobrain/`
- `scripts/`
- `docs/security/`
- `docs/release/`
- `docs/partner/`
- `tests/`

## Dependabot Decision

Near-term decision:

- use GitHub Dependabot
- monitor `pip` dependencies
- monitor GitHub Actions versions

Status:

- configured via `.github/dependabot.yml`

## Dependency Review

Status:

- workflow prepared: `.github/workflows/dependency-review.yml`
- runs on `pull_request` when the repository is public or when explicitly enabled for private testing

Limitation:

- private-repository execution may depend on plan/features and is therefore not treated as universally live-proven in Sprint 86

## CodeQL / SAST

Status:

- workflow prepared: `.github/workflows/codeql.yml`
- Python analysis configured
- gated to public visibility or explicit private enablement

Limitation:

- private-repository execution may depend on GitHub plan/features and must not be treated as automatically verified while API/features remain limited

## SBOM Generation

Status:

- workflow prepared: `.github/workflows/sbom.yml`
- intended to build the package and generate a CycloneDX SBOM artifact

Goal:

- make release/package composition inspectable before public switch and partner rollout

## Artifact Attestations / Provenance

Status:

- workflow prepared: `.github/workflows/provenance.yml`
- attestation step is gated behind explicit enablement or future public mode

Why gated:

- Sprint 86 does not create public release artifacts
- attestation should not be claimed as operational until executed in an approved release path

## Branch / Ruleset Governance

Status:

- governance expectations documented in `docs/security/REPO_GOVERNANCE_MODEL.md`
- verification script prepared: `scripts/check_repo_governance.py`

Limitation:

- GitHub API may return `403` for branch protection or ruleset visibility depending on plan/token scope
- `403` is treated as `UNKNOWN`, not `PASS`

## Release Integrity

Status:

- documented in `docs/release/RELEASE_INTEGRITY_AND_PROVENANCE.md`
- RC tag creation remains owner-approved only
- immutable tag policy is documented
- SBOM/provenance path is prepared but not yet an approved public release flow

## Current Status

Sprint 86 baseline after these changes:

- SECURITY baseline added
- CODEOWNERS added
- CONTRIBUTING added
- Dependabot configured
- dependency review prepared
- CodeQL prepared
- SBOM workflow prepared
- provenance workflow prepared
- governance verification path documented

## Remaining Blockers

P0 blocker may still remain if any of the following are unresolved:

- private GitHub feature limitations prevent live governance or SAST verification
- installed private package mode is not live-proven in an external workflow
- provenance path is documented but not exercised in an approved release flow

## Why This Is Required Before Public Switch

Public visibility changes the trust boundary.
Once the repository is public, trust depends not only on product behavior but also on:

- dependency update discipline
- review ownership
- SAST readiness
- release artifact transparency
- governance verification
- operationally clear reporting boundaries
