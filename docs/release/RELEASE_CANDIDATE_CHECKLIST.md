# Release Candidate Checklist

## Purpose

This checklist evaluates whether the current RepoBrain-Action state is ready for:

- continued private beta use
- a release-candidate handoff
- future public or Marketplace preparation

It does not publish the repository or change visibility by itself.

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

- Status: `READY_WITH_NOTES`
- no token values or private keys found in tracked repo content
- no private TopoCore source present in product repo
- no `pull_request_target` in the external example
- no patch/autofix
- no `contents: write` in the external pilot baseline
- notes:
  - live missing-secret degradation remains documented/static-guarded rather than re-exercised on `main`
  - live untrusted-fork secret-withholding remains documented/static-guarded

## Public Scrub Readiness

- Status: `BLOCKED`
- blockers:
  - no top-level `LICENSE`
  - historical docs still contain local Windows paths such as `D:\\ARIADNA_Minsk\\...`
  - historical docs still contain old v5/community narratives that are safe as history but not scrubbed for public face-value reading
  - legacy release docs describe an outdated release flow and need relabeling or replacement before public exposure

## Marketplace Readiness

- Status: `BLOCKED`
- blockers:
  - repository is still private
  - product still depends on a private TopoCore v6 checkout token
  - no public release/tag strategy is finalized
  - no public support policy is formalized
  - no top-level `LICENSE`
  - current install path is still private-beta oriented rather than Marketplace turnkey

## Release Engineering Readiness

- Status: `READY_WITH_NOTES`
- `VERSION` exists and is `0.5.0-rc.1`
- `CHANGELOG.md` exists
- legacy release docs exist
- notes:
  - no current Git tags are present
  - immutable pinned-ref guidance for public consumers should be formalized before public release

## Known Limitations

- TopoCore v6 remains private permanently
- RepoBrain-Action remains private in the current pilot state
- external install still requires `TOPOCORE_V6_REPO_TOKEN`
- verify is informational only
- fix is no-patch/no-mutation governance only
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior

## Approval Gates

- `PRIVATE_BETA_RC_READY`: yes
- `PUBLIC_READY_PENDING_APPROVAL`: no, blocked by scrub work
- `MARKETPLACE_READY_PENDING_APPROVAL`: no, blocked by packaging/support/private-dependency work
