# Repo Governance Model

## Purpose

This document defines the repository-governance expectations that must be in place before public visibility is approved.

## CODEOWNERS Expectations

`CODEOWNERS` must exist and cover:

- workflow surface
- product code
- security docs
- release docs
- partner docs
- tests

## Branch Protection / Ruleset Expectations

Expected governance posture:

- protected default branch
- review expectations appropriate for release-critical files
- required checks for CI/safety validation
- least-privilege admin bypass
- no silent bypass of supply-chain or security gates

## Required Checks

At minimum, governance should require or strongly enforce:

- CI / tests
- lint
- usersafe scan
- TKYA contract guard
- release/supply-chain gates as they become operational

## Review Requirements

- release and workflow changes should be reviewed deliberately
- security-sensitive docs and workflow paths should not rely on casual direct edits

## Admin Bypass Policy

- any bypass should be exceptional and documented
- bypass should not become the normal operating path for release-critical changes

## Visibility Status

- RepoBrain-Action remains private in Sprint 86
- public switch still requires explicit owner approval after P0 hardening

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
- `WARN`
- `FAIL`
- `UNKNOWN`

GitHub API limitations are handled by `scripts/check_repo_governance.py`.

## Limitations

- GitHub API may return `403` for branch protection or ruleset visibility depending on plan/token scope
- `403` must be treated as `UNKNOWN`, not `PASS`
- private TopoCore governance should not be documented in a way that exposes private paths or source details
