# RepoBrain Operator Quickstart

## Scope

This quickstart is for operators validating RepoBrain in:

- GitHub App mode (primary runtime),
- external GitHub mode foundation (third-party GitHub-native bounded public path hosted publicly through `repobrain-community`),
- external CLI mode (ask-only trial path).

It describes what to verify first, what to run, and how to classify outcomes.

## 1) GitHub App Readiness First

Before command validation, run install/readiness checks and confirm explicit verdict:

- `READY`
- `MISSING_PERMISSION`
- `MISSING_CONFIG`
- `UNSUPPORTED_SETUP`

Readiness artifacts:

- `artifacts/onboarding/repobrain_install_readiness.json`
- `artifacts/onboarding/repobrain_install_readiness.md`

Required operator references:

- `docs/onboarding/github_app_setup.md`
- `docs/onboarding/permissions.md`

If readiness is not `READY`, stop and resolve blockers before command runs.

## 2) GitHub Mode Validation (Primary)

On an open PR:

1. `/repobrain help`
2. `/repobrain ask --profile balanced ...`
3. `/repobrain review --profile balanced`
4. `/repobrain fix --profile premium ...` (safe `no_patch` is acceptable when grounded patch target is absent)

What to verify:

- compact PR-visible output remains intact,
- profile truth is coherent in audit/evidence,
- review/fix `cheap` normalization guardrail remains explicit when applicable.

## 3) External GitHub Mode Foundation Validation (Third-Party)

Public runtime host and install kit:

- `repobrain-community`

RepoBrain-Action boundary/reference doc:

- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`

Run on a third-party PR:

1. `/repobrain doctor`
2. `/repobrain help`
3. `/repobrain ask ...`
4. `/repobrain review`
5. `/repobrain fix`

Expected:

- workflow executes via the reusable external foundation path,
- readiness artifact is uploaded,
- doctor/help truth is current and compact,
- review is a bounded read-only Review Candidate,
- fix is a bounded Fix-Lite Candidate manual-only patch suggestion,
- Fix-Lite may return `suggestion available`, `blocked`, or `not applicable`,
- no duplicate comments appear,
- no patch-applied, file-modified, commit-created, branch-pushed, PR-created, security-verdict, safe-to-merge, approval/rejection, or autofix claims appear.

Mandatory Fix-Lite boundary:

- `No patch was applied. No files were modified.`

## 4) External CLI Mode Validation (Ask-Only)

Run against a local checkout of target repository:

```bash
python scripts/run_github.py \
  --mode external \
  --repo-root /absolute/path/to/repo \
  --command ask \
  --query "What changed around module X?"
```

Expected:

- `STATUS=success`
- `DECISION=ANSWER`
- answer text returned

Unsupported commands must block honestly:

```bash
python scripts/run_github.py --mode external --repo-root /path --command review --query "..."
```

Expected:

- blocked status
- decision `UNSUPPORTED_COMMAND`

## 5) MCP Surface Validation (Ask-Only)

```bash
python scripts/run_mcp_surface.py \
  --capability ask \
  --repo-root /absolute/path/to/repo \
  --query "What changed around module X?"
```

Expected:

- JSON response
- `status=success`
- `decision=ANSWER`

Unsupported capability probe:

```bash
python scripts/run_mcp_surface.py --capability review --repo-root /path --query "..."
```

Expected:

- `status=blocked`
- `decision=UNSUPPORTED_CAPABILITY`

## 6) Trial Evidence Capture

Use:

- `docs/trials/external_repo_trial_evidence_template.md`

Capture for each executed step:

- command
- run/log reference
- artifacts present/missing
- operator blockers
- final verdict (`TRIAL_PASS|TRIAL_PARTIAL|TRIAL_BLOCKED`)

## 7) Stop Conditions

Stop and file product issue if:

1. readiness result is ambiguous,
2. artifact truth contradicts command result,
3. unsupported path behaves as if supported,
4. operator cannot determine deterministic next action.
