# Sprint 70 - External Command Matrix on Elen-MCP

## Purpose

Sprint 70 validates the supported external RepoBrain command surface on `alexworkingai/Elen-MCP-v.2.2.0`.
It follows the successful external `ask` smokes from Sprint 69 and checks issue-scope and PR-scope behavior with real GitHub runs.

## Baseline

- RepoBrain-Action baseline before Sprint 70:
  - `1c9e24f Fix external RepoBrain action references`
- external issue `ask` smoke passed
- external PR `ask` smoke passed
- Elen-MCP Actions policy was fixed to allow external actions
- `TOPOCORE_V6_REPO_TOKEN` is configured in Elen-MCP
- no `repobrain-community` dependency remains

## Command Discovery

Supported issue-comment command spellings confirmed from `repobrain/commands.py`:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`

Supported profile flag on command surface:

- `--profile cheap|balanced|premium`
  - valid on `ask`, `review`, and `fix`

Unsupported or not-present spellings:

- `/repobrain status`
- `/repobrain doctor`
- `/repobrain fix-lite`

## Test Targets

- safe issue:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/13`
- safe PR:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/pull/14`
- PR fixture branch:
  - `alexworkingai-patch-1`
- PR fixture file:
  - `docs/repobrain_pr_smoke_fixture.md`
- final state after validation:
  - issue closed
  - PR closed without merge

## Issue Command Matrix

| Command | Run URL | Conclusion | Route | Requested backend | Resolved backend | Fallback used | Fallback reason | Scope status | Safety result | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| `/repobrain help` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222297404` | `success` | `HELP` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | help text only; no patch/autofix | `PASS` |
| `/repobrain ask Summarize this repository and RepoBrain backend status.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222351231` | `success` | `REVIEW` | `auto` | `v6` | `no` | `none` | `n/a` | bounded answer posted; no repo mutation | `PASS` |
| `/repobrain review Summarize review risks for this repository.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222391215` | `success` | `WAIT` | `auto` | `not_applicable` | `not_applicable` | `unsupported_issue_context` | `unsupported_issue_context` | honest scoped block; no PR review claim; no patch | `PASS_SCOPED_UNSUPPORTED` |
| `/repobrain verify Summarize verification status.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222421428` | `success` | `WAIT` | `auto` | `not_applicable` | `not_applicable` | `unsupported_issue_context` | `unsupported_issue_context` | honest scoped block; no fake verify claim | `PASS_SCOPED_UNSUPPORTED` |
| `/repobrain fix Propose a safe documentation-only improvement, but do not apply any patch.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222452256` | `success` | `WAIT` | `auto` | `not_applicable` | `not_applicable` | `unsupported_issue_context` | `unsupported_issue_context` | `patch_authorized=no`, `patch_applied=no`, no branch/commit/PR action | `PASS_SCOPED_UNSUPPORTED` |
| `/repobrain locate RepoBrain workflow configuration.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222487441` | `success` | `REVIEW` | `auto` | `v6` | `no` | `none` | `n/a` | direct evidence answer; no LLM write path | `PASS` |
| `/repobrain explain RepoBrain pilot setup.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222522639` | `success` | `REVIEW` | `auto` | `v6` | `no` | `none` | `n/a` | bounded explanation; no repo mutation | `PASS` |

## PR Command Matrix

| Command | Run URL | Conclusion | PR metadata used | Requested backend | Resolved backend | Fallback used | Fallback reason | Verification status | Patch authorized/applied | Safety result | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `/repobrain ask Summarize this PR with RepoBrain backend diagnostics.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222574994` | `success` | `yes` | `auto` | `v6` | `no` | `none` | `NOT_RUN` | `n/a` | PR summary posted with backend evidence; no repo mutation | `PASS` |
| `/repobrain review Summarize review risks for this PR.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222606916` | `success` | `yes` | `auto` | `v6` | `no` | `none` | `Verification NOT_RUN: PASS=0, FAIL=0, NOT_RUN=2` | `n/a` | bounded PR review; low-risk docs-only output; no fake approval claim | `PASS` |
| `/repobrain verify Summarize verification status for this PR.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222641664` | `success` | `no` | `auto` | `not_applicable` | `not_applicable` | `verify_report_only` | `NOT_RUN` | `n/a` | meaningful report-only verify output; no fake green claim | `PASS_SCOPED_UNSUPPORTED` |
| `/repobrain fix Propose a safe documentation-only improvement for this PR, but do not apply any patch.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222674497` | `success` | `yes` | `auto` | `v6` | `no` | `none` | `NOT_RUN` | `no_patch` / no apply | safe no-patch outcome; no file/branch/commit/PR action | `PASS` |
| `/repobrain help` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26222704648` | `success` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | help text only; no repo mutation | `PASS` |

## Backend Evidence Summary

- backend-invoking commands resolved `v6`:
  - issue `ask`
  - issue `locate`
  - issue `explain`
  - PR `ask`
  - PR `review`
  - PR `fix`
- report-only or scoped not-applicable commands:
  - issue `review`
  - issue `verify`
  - issue `fix`
  - PR `verify`
  - `help` on issue and PR
- fallback status:
  - no `v5`
  - no fallback activation
  - no `repobrain-community`

## Safety Summary

- no `decide_raw` surfaced in external output
- no patch application
- no file modification by RepoBrain behavior
- no commit/branch/PR creation by RepoBrain behavior
- no unsafe approval or safe-to-merge claim
- no secret or token exposure
- no raw private path or raw stack trace exposure

## Blockers / Defects

- none blocking acceptance

Minor observations:

- issue-only `ask` and `explain` still note `issue_only_policy_disabled` for LLM usage, but the bounded retrieval answer and v6 backend evidence remain healthy
- PR `verify` is intentionally report-only and records `verify_report_only` instead of pretending it is a full retrieval-backed v6 decision path

## Product Status

`EXTERNAL_COMMAND_MATRIX_PASSED`

## Recommended Next Step

Sprint 71 should focus on:

- v6 retrieval and evidence quality on external repos
- sharper issue-scope answer quality
- PR review/fix evidence richness on larger diffs

## Non-Goals

- no v5
- no `repobrain-community`
- no patch/autofix
- no production/Marketplace switch
