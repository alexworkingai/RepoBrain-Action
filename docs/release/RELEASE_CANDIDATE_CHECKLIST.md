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
  - `/repobrain audit`
  - `/repobrain score`
  - `/repobrain doctor`
  - `/repobrain help`
  - `/repobrain ask <query>`
  - `/repobrain locate <query>`
  - `/repobrain explain <query>`
  - `/repobrain review`
  - `/repobrain status`
  - `/repobrain verify`
  - `/repobrain fix`
- unsupported command spellings documented honestly:
- benchmark evidence now exists for the current `/repobrain audit` MVP and supports demo use with stated limitations

## External Install Readiness

- Status: `READY_WITH_NOTES`
- canonical install guide exists
- canonical command guide exists
- canonical troubleshooting guide exists
- external workflow example is usable and read-mostly
- public action access through `alexworkingai/RepoBrain-Action@main` is documented
- selected partner testing now has a preferred `installed_private_package` runtime path
- note:
  - controlled beta example workflow still uses `private_checkout`
  - normal Python package artifacts can still contain readable implementation files

## Security Readiness

- Status: `READY`
- no token values or private keys found in tracked docs
- no private TopoCore source present in product repo
- no `pull_request_target` in the external example
- no patch/autofix
- no `contents: write` in the external pilot baseline
- high-security TopoCore policy is documented
- SECURITY.md, CONTRIBUTING.md, and CODEOWNERS now exist
- supply-chain and release-integrity docs/workflows are prepared before public visibility

## Public Scrub Readiness

- Status: `READY`
- top-level `LICENSE` exists
- local machine paths have been sanitized from tracked docs
- legacy release docs are relabeled as historical/internal
- support and pinning strategy are documented

## Public-Ready Distribution Gate

- Status: `READY_WITH_NOTES`
- decision:
  - `INSTALLED_PRIVATE_PACKAGE_SELECTED`
- notes:
  - `private_checkout` remains beta-only
  - public visibility is now switched for RepoBrain-Action only
  - Marketplace remains blocked

## Marketplace Readiness

- Status: `BLOCKED`
- blockers:
  - product still depends on a private TopoCore v6 tokenized access path
  - no approved public distribution strategy for TopoCore exists yet
  - no public support channel is approved
  - no immutable public release tag exists yet

## Release Engineering Readiness

- Status: `READY_WITH_NOTES`
- `VERSION` exists and is `0.5.0-rc.1`
- `CHANGELOG.md` exists
- release notes exist
- RC tag and pinning plan exists
- notes:
  - no current Git tags are present
  - immutable pinned-ref guidance for public consumers is documented but not yet executed
  - tag creation remains pending explicit owner approval
  - SBOM and provenance-prep workflows are now prepared but not yet treated as a public release execution claim

## Known Limitations

- TopoCore v6 remains private permanently
- RepoBrain-Action is public, but TopoCore remains private
- external install still requires private runtime authorization
- verify is informational only
- fix is no-patch and no-mutation governance only
- no patch/autofix
- no RepoBrain-created branch, commit, or PR behavior
- audit MVP is implemented
- audit benchmark evidence is documented for demo-facing use
- doctor and status are implemented as report-only diagnostics
- score is implemented as a compact summary of the same guarded audit engine

## Approval Gates

- `PRIVATE_BETA_RC_CONFIRMED`: yes
- `TOPOCORE_SECURITY_POLICY_ADOPTED`: yes
- `PUBLIC_READY_PENDING_APPROVAL`: no
- `PUBLIC_READY_PENDING_OWNER_APPROVAL`: historical Sprint 84/85 state only
- `PUBLIC_VISIBILITY_APPROVAL_PACK_READY`: yes
- `PUBLIC_SWITCH_READY_AFTER_P0_HARDENING`: no
- `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`: historical Sprint 86 state only
- `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`: historical Sprint 87 state only
- `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`: historical Sprint 88 / Sprint 89 state only
- `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`: historical Sprint 90 state only
- `PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY`: yes
- owner approval for the Sprint 91 public visibility switch: yes
- `MARKETPLACE_READY_FOR_PREP_PENDING_APPROVAL`: no
- `MARKETPLACE_NOT_READY`: yes
