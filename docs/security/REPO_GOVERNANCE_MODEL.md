# Repo Governance Model

## Purpose

This document defines the repository-governance expectations for the public RepoBrain control plane and the protected-main baseline that supports selected partner onboarding.

## CODEOWNERS Expectations

`CODEOWNERS` should exist and cover:

- workflow surface
- product code
- security docs
- release docs
- partner docs
- tests

## Branch Protection / Ruleset Expectations

Expected governance posture:

- protected default branch
- active ruleset baseline for `main`
- review expectations appropriate for release-critical files
- required checks once stable check names are locked
- least-privilege admin bypass
- no silent bypass of supply-chain or security gates

## Current Protected-Main Baseline

Current Sprint 92E truth:

- `PROTECTED_MAIN_BASELINE_ENABLED`
- ruleset name: `Protect main`
- active on the default branch / `main`
- current public ruleset follows a solo-owner model rather than a review-enforced PR model
- force pushes blocked: enabled
- deletions restricted: enabled
- linear history required: enabled
- PR approval requirement: currently not enforced by the active ruleset
- required checks: deferred
- CODEOWNERS review enforcement: deferred
- interpretation: `GOVERNANCE_PARTIAL_REQUIRED_CHECKS_DEFERRED_SOLO_OWNER_MODEL`

This is real governance improvement, but it is not the final enterprise governance state.

Historical merge evidence:

- PR `#119` merged the protected-main UX polish without admin bypass
- dependency graph enabled on the public RepoBrain repository
- dependency review passed on PR `#119`

## Required Checks

At minimum, governance should require or strongly enforce once stable:

- CI / tests
- lint
- usersafe scan
- TKYA contract guard
- release/supply-chain gates as they become operational

## Review Requirements

- release and workflow changes should still be reviewed deliberately even in solo-owner mode
- security-sensitive docs and workflow paths should not rely on casual direct edits
- future tightening should reintroduce explicit review gates once stable required checks and check names are locked

## Admin Bypass Policy

- any bypass should be exceptional and documented
- bypass should not become the normal operating path for release-critical changes
- repository-admin bypass may exist in the ruleset, but it should not become the routine merge path

## Visibility Status

- RepoBrain-Action is public
- protected main baseline is enabled
- current Sprint 92E branch work should still prefer PR flow even though the active ruleset is currently modeled for solo-owner operation

## How Governance Is Verified

Verification inputs:

- `.github/CODEOWNERS`
- default branch metadata
- branch protection when visible
- repository rulesets when visible
- workflow permission model
- validation checks documented in CI

## Current Verification Result

Current result should be treated as one of:

- `PASS`
- `PARTIAL`
- `WARN`
- `FAIL`
- `UNKNOWN`

Current protected-main baseline should currently be treated as `PARTIAL`.

Reason:

- protected-main baseline is real
- dependency graph enabled
- dependency review passed
- required checks remain deferred
- CODEOWNERS review enforcement remains deferred
- active ruleset is solo-owner rather than review-enforced

GitHub API limitations are handled by `scripts/check_repo_governance.py`.

## Limitations

- GitHub API may return `403` for branch protection or ruleset visibility depending on plan/token scope
- `403` must be treated as `UNKNOWN`, not `PASS`
- required status checks absent should currently be interpreted as deferred, not as a false green enterprise closeout
- private TopoCore governance should not be documented in a way that exposes private paths or source details
