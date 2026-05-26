# GitHub Actions Permission Model

## Purpose

This document explains the least-privilege model for RepoBrain workflows before public visibility.

## External Partner Baseline

External partner workflows should stay read-mostly:

- `contents: read`
- `models: read` when applicable
- `checks: read`
- `statuses: read`
- `actions: read`
- `issues: write`
- `pull-requests: read`

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
  - not required in the current active internal workflows
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

## Future Tightening Plan

- continue reducing internal workflow write scopes where possible
- keep publisher-style write scopes isolated in dedicated workflows rather than the main execution workflow
