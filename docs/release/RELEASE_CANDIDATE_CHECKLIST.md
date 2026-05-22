# Release Candidate Checklist

## Purpose

This checklist evaluates whether the current RepoBrain-Action state is ready for:

- continued private beta use
- release-candidate handoff
- future public or Marketplace preparation

It does not publish the repository, change visibility, create a release tag, or publish to Marketplace by itself.

## Runtime Readiness

- Status: `READY`
- v6-only runtime path is in place
- no v5 fallback
- no `repobrain-community` dependency
- private TopoCore v6 boundary remains intact

## Command Readiness

- Status: `READY`
- supported commands:
  - `/repobrain help`
  - `/repobrain ask <query>`
  - `/repobrain locate <query>`
  - `/repobrain explain <query>`
  - `/repobrain review`
  - `/repobrain verify`
  - `/repobrain fix`
- unsupported commands documented honestly:
  - `/repobrain status`
  - `/repobrain doctor`
  - `/repobrain fix-lite`
- roadmap commands documented without claiming implementation:
  - `/repobrain audit`
  - `/repobrain score`

## External Install Readiness

- Status: `READY_WITH_NOTES`
- canonical install guide exists
- canonical command guide exists
- canonical troubleshooting guide exists
- external workflow example is usable and read-mostly
- private action access and `TOPOCORE_V6_REPO_TOKEN` requirements are documented
- note:
  - current install path still depends on a private TopoCore v6 repository and a repo secret

## Security Readiness

- Status: `READY`
- no token values or private keys found in tracked docs
- no private TopoCore source present in product repo
- no `pull_request_target` in the external example
- no patch/autofix
- no `contents: write` in the external pilot baseline
- high-security TopoCore policy is documented

## Public Scrub Readiness

- Status: `READY`
- top-level `LICENSE` exists
- local machine paths have been sanitized from tracked docs
- legacy release docs are relabeled as historical/internal
- support and pinning strategy are documented

## Marketplace Readiness

- Status: `BLOCKED`
- blockers:
  - repository is still private
  - product still depends on a private TopoCore v6 tokenized access path
  - no approved public distribution strategy for TopoCore exists yet
  - no public support channel is approved
  - no immutable public release tag exists yet

## Release Engineering Readiness

- Status: `READY_WITH_NOTES`
- `VERSION` exists and is `0.5.0-rc.1`
- `CHANGELOG.md` exists
- release notes exist
- notes:
  - no current Git tags are present
  - immutable pinned-ref guidance for public consumers is documented but not yet executed

## Known Limitations

- TopoCore v6 remains private permanently
- RepoBrain-Action remains private in the current pilot state
- external install still requires `TOPOCORE_V6_REPO_TOKEN`
- verify is informational only
- fix is no-patch and no-mutation governance only
- no patch/autofix
- no RepoBrain-created branch, commit, or PR behavior
- audit, score, doctor, and status roadmap commands are not implemented yet

## Approval Gates

- `PRIVATE_BETA_RC_CONFIRMED`: yes
- `TOPOCORE_SECURITY_POLICY_ADOPTED`: yes
- `PUBLIC_READY_PENDING_APPROVAL`: no
- `PUBLIC_BLOCKED_BY_DISTRIBUTION_STRATEGY`: yes
- `MARKETPLACE_READY_FOR_PREP_PENDING_APPROVAL`: no
- `MARKETPLACE_NOT_READY`: yes
