# GitHub Actions Permission Model

## Purpose

This document explains the least-privilege model for RepoBrain workflows after public visibility and during selected partner pilot onboarding.

## External Partner Baseline

External partner workflows should stay read-mostly by default:

- `contents: read`
- `models: read` when applicable
- `checks: read`
- `statuses: read`
- `actions: read`
- `issues: write`
- `pull-requests: read`

If selected PR command-response comments are required in the partner pilot, a narrowly justified exception is allowed:

- `issues: write`
- `pull-requests: write`

That exception is acceptable only when all of the following hold:

- `contents: write` is absent
- `checks: write` is absent
- `pull_request_target` is absent
- RepoBrain remains no-mutation:
  - no patch/autofix
  - no file changes
  - no RepoBrain-created branch/commit/PR
- the permission is documented as PR command response publication only

## Internal Workflow Permissions

Internal workflows may differ only where a write permission is demonstrably required.

Current intended rules:

- main RepoBrain execution workflow should not request `checks: write` or `pull-requests: write` unless truly required
- dedicated publisher workflow may require `checks: write` and `statuses: write` to publish sanitized check-run/status outputs
- no workflow should request `contents: write` unless a future explicitly approved release path truly needs it

## Why Each Write Permission Exists

Current explicit justifications:

- `checks: write`
  - limited to the dedicated publisher workflow that emits sanitized check-run results after the main workflow has already completed
- `statuses: write`
  - limited to the dedicated publisher workflow for sanitized status-context fallback publication
- `pull-requests: write`
  - justified only when a workflow must publish RepoBrain PR command response comments
  - not a license to create PRs, commits, branches, or file mutations
- `contents: write`
  - not required in the current active internal workflows

## Fork Safety

- no `pull_request_target`
- no private secrets for untrusted fork execution by default
- no private runtime token exposure outside trusted paths

## Mutation Policy

- no patch/autofix
- no RepoBrain-created branch, commit, or PR behavior
- no workflow should imply otherwise

## Diagnostics Tiers

- compact default output is for GitHub issue/PR comments
- `RB_REPOBRAIN_VERBOSE_DIAGNOSTICS=1` enables expanded sanitized diagnostics
- full sanitized debug trace belongs in workflow artifacts/logs, not default partner comments
- controlled issue ask/explain LLM is enabled by default through `RB_REPOBRAIN_ENABLE_ISSUE_LLM=1`, but quota exhaustion or provider unavailability must fall back deterministically and stay non-mutating

## Future Tightening Plan

- continue reducing internal workflow write scopes where possible
- keep publisher-style write scopes isolated in dedicated workflows rather than the main execution workflow

## Live Validation

Sprint 92C live PR retest on `alexworkingai/Elen-MCP-v.2.2.0` confirmed the documented narrow exception works as intended:

- latest PR command response comments were published successfully
- review, verify, fix, audit, and score stayed no-mutation
- latest audit and score comments no longer treated the constrained `pull-requests: write` as a broad dangerous workflow posture
- no `contents: write`
- no `checks: write` on the partner baseline
- no `pull_request_target`

Sprint 92E governance follow-up:

- PR `#119` merged without admin bypass
- dependency graph enabled
- dependency review passed on PR `#119`
- protected-main governance baseline on the public RepoBrain repository remains enabled separately from workflow permissions
- the active public ruleset is currently a solo-owner model rather than review-enforced branch protection
- required checks remain intentionally deferred until stable check names are locked
