# Sprint 72 - Verify Command Productionization

## 1. Purpose

Sprint 72 productionizes `/repobrain verify` on the external `Elen-MCP-v.2.2.0` repo.
It follows Sprint 70 command-matrix validation and Sprint 71 retrieval/evidence quality hardening.
This sprint does not change runtime policy or enable patch/autofix.

## 2. Baseline

Baseline before Sprint 72:

- RepoBrain-Action latest main before Sprint 72:
  - `e5e0f9f Record external retrieval quality results`
- external command matrix passed
- external retrieval quality passed
- verify behavior before Sprint 72:
  - issue scope: scoped unsupported
  - PR scope: report-only
  - live PR verify could still show `pending` with `Total checks: 0` when GitHub exposed only an aggregate status state without concrete contexts

## 3. Verify Semantics

Current verify status model:

- `PASS`
  - observed verification signals are passing
  - at least one meaningful source exists
  - informational only; not merge approval
- `WARN`
  - observed signals are partial, mixed, permission-limited, or coarse
  - human review is still required
- `FAIL`
  - observed verification source includes failing checks or statuses
- `PENDING`
  - observed verification source includes queued or in-progress checks
- `NOT_RUN`
  - no concrete checks, statuses, or workflow runs were observed for the PR head SHA
- `UNKNOWN`
  - API access, permission, or source ambiguity prevents a trustworthy classification

Source model:

- `checks`
- `statuses`
- `workflow_runs`

Limitations model:

- report missing sources explicitly
- report permission-limited sources explicitly
- report workflow-run fallback as coarse verification only
- never convert missing evidence into an implicit pass

Safety rule:

- `/repobrain verify` does not claim safe-to-merge, security approval, or production approval

## 4. Implementation Summary

Code changes landed in Sprint 72:

- `repobrain/verify.py`
  - preserves raw source-state detail instead of collapsing non-forbidden errors to `empty`
  - adds `status_label` mapping for `PASS/WARN/FAIL/PENDING/NOT_RUN/UNKNOWN`
  - adds limitations synthesis and head-SHA audit anchoring
- `repobrain/formatting.py`
  - renders explicit verification labels
  - renders source summary, limitations, informational-only warning, and safer next steps
  - removes ambiguous success wording that could read like merge approval
- `repobrain/github_flow.py`
  - records verify status, source, counts, head SHA, and PR metadata usage in scoped diagnostics
- tests added:
  - `tests/test_verify_command_productionization.py`

## 5. Unit/Static Test Coverage

Sprint 72 coverage now includes:

- success to `PASS`
- failure to `FAIL`
- pending to `PENDING`
- no concrete signals to `NOT_RUN`
- permission failure to `UNKNOWN`
- workflow fallback with permission gaps to `WARN`
- explicit sources and limitations rendering
- issue-scope scoped unsupported preservation
- no unsafe merge/security wording
- no v5, no repobrain-community, no patch/autofix drift in verify output

## 6. External Verify Live Results

Issue verify:

- issue URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/17`
- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26239886027`
- conclusion:
  - `success`
- status:
  - `PASS_SCOPED_UNSUPPORTED`
- scope behavior:
  - issue-only verify remains scoped unsupported and explicitly redirects users to PR context for CI state
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `not_applicable`
  - fallback reason: `unsupported_issue_context`
- safety result:
  - no fake PR verification
  - no patch behavior
  - no merge or security approval claim

PR verify:

- PR URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/pull/18`
- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26239813135`
- conclusion:
  - `success`
- observed GitHub checks before command:
  - `gh pr checks 18` returned no checks for branch `codex/sprint-72-verify-production-fixture`
- reported status:
  - `NOT_RUN`
- sources:
  - primary source: `status`
  - checks: `empty`
  - statuses: `available`
  - workflow_runs: `empty`
- limitations:
  - no concrete checks, statuses, or workflow runs were observed for the PR head SHA
  - combined status was available only as a coarse aggregate signal, so the report stayed `NOT_RUN`
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `not_applicable`
  - fallback reason: `verify_report_only`
- safety result:
  - no fake green
  - no merge/security approval claim
  - no patch application
  - no RepoBrain-created branch/commit/PR behavior

## 7. Defects / Gaps

Fixed now:

- PR verify no longer reports an effectively empty aggregated pending state as if it were actionable verification progress
- PR verify now exposes source-quality limitations directly in the user-visible comment
- PR verify scoped diagnostics now record `PR metadata used: yes` when head SHA is resolved from PR metadata

Deferred:

- no live failing-check scenario was introduced on Elen-MCP because Sprint 72 avoided creating a deliberate CI break in the pilot repo
- `PENDING` and `FAIL` live behavior remain covered by unit tests and existing GitHub-source logic rather than a destructive live fixture

Not defects:

- issue-scope verify remains scoped unsupported by design
- report-only backend evidence remains explicit and acceptable for verify

## 8. Product Status

- `VERIFY_PRODUCTIONIZATION_PASSED`

## 9. Next Step

Recommended next sprint:

- Sprint 73 - Fix Command Product Path

Focus:

- keep external fix guidance useful while preserving no-patch safety by default
- continue improving user-facing diagnostics without widening runtime policy

Sprint 73 follow-up:

- `/repobrain fix` is now productized as a safe proposal/governance path on external PRs
- visible safety gates now show `patch_authorized=false`, `patch_applied=false`, `files_modified=false`, `branch_created=false`, `commit_created=false`, and `pr_created=false`
- unsafe mutation requests are blocked explicitly with `BLOCKED_BY_SAFETY`

Sprint 74 follow-up target:

- harden the external product path around permissions, private action access, token degradation, and fork safety
- preserve verify as informational and no-mutation while tightening external trust boundaries

## 10. Non-Goals

- no v5
- no repobrain-community
- no patch/autofix
- no production/Marketplace switch
