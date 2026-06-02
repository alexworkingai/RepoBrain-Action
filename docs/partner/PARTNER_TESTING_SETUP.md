# Partner Testing Setup

## What RepoBrain Is

RepoBrain is a guarded repository-intelligence action that reviews repository state, answers grounded questions, and produces bounded audit and score summaries without mutating the repository.

## What Partners Are Testing

- command quality and grounding
- `v6`-enriched audit and score behavior
- runtime setup ergonomics
- documentation clarity
- repo-type coverage

## What RepoBrain Does Not Do

- no patch/autofix
- no RepoBrain-created branch, commit, or PR
- no safe-to-merge or security approval
- no TopoCore source distribution

## Prerequisites

- repository admin access
- allowed GitHub Actions policy for external actions
- BYO-LLM or user-paid model access when needed
- scoped runtime credential delivery according to the approved partner model

## Workflow Install

- install the RepoBrain workflow into the consumer repository
- keep explicit permissions blocks in place
- do not use `pull_request_target`
- current public action reference is `alexworkingai/RepoBrain-Action@main` until a separately approved tag exists

## Permissions Baseline

- read-mostly baseline only
- no broad write scopes
- no token or env dump
- if PR command-response comments are required, `pull-requests: write` may be granted only as a narrowly justified PR comment response permission
- do not grant `contents: write` for normal partner setup
- do not use `pull_request_target`

## Runtime Mode

- preferred mode: `installed_private_package`
- `private_checkout` is controlled beta-only fallback for owner-managed environments
- the supported authorization model is selected and live-proven
- RepoBrain-Action is now public
- TopoCore remains private and source is not licensed or distributed

## Secret and Runtime Credential Setup

- use placeholders only in shared docs
- do not paste token values into issues, commits, workflow logs, or chat
- keep credentials scoped, expiring, and revocable

## First Smoke Commands

- `/repobrain doctor`
- `/repobrain status`
- `/repobrain audit`
- `/repobrain score`
- `/repobrain ask`

## Expected Outputs

- doctor and status report the active runtime mode truthfully
- ask and explain may use an LLM when safe policy and provider access allow it, but they can also answer from deterministic retrieval and TopoCore-backed evidence when no LLM call occurs
- route labels reflect the typed command even when internal analysis mode differs
- default GitHub comments stay compact and developer-facing
- `RB_REPOBRAIN_VERBOSE_DIAGNOSTICS=1` enables expanded sanitized diagnostics
- audit and score are informational only
- no mutation occurs
- no secret or TopoCore source exposure occurs in user-facing output

## Troubleshooting

- use `/repobrain doctor` first
- confirm runtime credential scope and expiration
- confirm the workflow keeps explicit permissions and avoids `pull_request_target`
- treat protected main as a governance improvement signal, while required checks may still be deferred

## Feedback Submission

- use the partner feedback template and include install friction, command quality, false positives/negatives, and security concerns
