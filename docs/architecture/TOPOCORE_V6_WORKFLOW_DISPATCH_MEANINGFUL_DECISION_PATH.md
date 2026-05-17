# TopoCore v6 Workflow Dispatch Meaningful Decision Path

## 1. Purpose

Sprint 49 adds a meaningful manual `workflow_dispatch` v6 decision path.
It fixes the Sprint 48 validation gap where private install succeeded but only help or dry-run behavior executed.
`issue_comment` remains v5-pinned.
`workflow_dispatch` default remains safe.
v5 fallback remains available.
No patch application is enabled.

## 2. Current Baseline

- latest accepted `main` before Sprint 49: `99bf16f Add GitHub lab TopoCore v6 dependency gate`
- operational run `349` confirmed:
  - private checkout passed
  - private install passed
  - `topocore-v6-0.30.0` installed
  - no meaningful v6 decision evidence was produced because the command path stayed on `help`

## 3. New `workflow_dispatch` Inputs

- `repobrain_lab_command`
- `repobrain_lab_query`
- `repobrain_lab_fixture`

Defaults:

- `repobrain_lab_command=help`
- `repobrain_lab_query="Summarize current RepoBrain TopoCore backend status."`
- `repobrain_lab_fixture=minimal`

## 4. Meaningful Lab Commands

Sprint 49 implements the following workflow-dispatch lab commands:

- `help`
  - keeps the existing safe help or no-op path
  - does not claim v6 decision execution
- `ask`
  - runs a bounded local RepoBrain decision path through the selectable backend seam
- `review`
  - runs a bounded fixture-backed review-style decision path
- `verify`
  - runs a bounded fixture-backed verify-style decision path
- `fix-lite`
  - runs a bounded conservative fix-lite decision path
  - does not authorize patching or repository mutation

These lab commands are fixture-backed validation paths.
They are intentionally scoped for workflow-dispatch evidence generation, not for normal comment-driven GitHub behavior.

## 5. Backend Evidence

Sprint 49 emits a compact sanitized evidence record for meaningful workflow-dispatch lab commands.

Evidence fields:

- `lab_command`
- `lab_fixture`
- `requested_backend`
- `resolved_backend`
- `backend_mode`
- `fallback_used`
- `fallback_reason`
- `status`
- `action`
- `message_code`
- `confidence_band`

For `fix-lite`, the evidence record also preserves conservative safety markers:

- `patch_authorized=false`
- `patch_applied=false`
- `files_modified=false`
- `branch_created=false`
- `commit_created=false`
- `pr_created=false`

Evidence is written to:

- `artifacts/lab_backend_evidence/repobrain_lab_backend_evidence.json`

The workflow uploads that artifact only for `workflow_dispatch`.

## 6. Safety Boundaries

- no secrets are written to logs or artifacts
- no private URLs with credentials are written to logs or artifacts
- no raw code, raw diff, or raw prompt is emitted
- `decide_raw` remains forbidden
- no patch application is introduced
- no commit, branch, or PR creation is introduced
- no default `issue_comment` behavior is changed

## 7. Sprint 50 Target

If the first post-Sprint-49 real GitHub run proves category A:

- Sprint 50 may switch `issue_comment` lab runtime to v6 with v5 fallback

If the first post-Sprint-49 real GitHub run still lacks evidence:

- Sprint 50 fixes the specific instrumentation or path blocker

## 8. Non-Goals

- no v5 removal
- no default v6 `issue_comment` runtime
- no default private dependency install
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no PR, check, or comment behavior change by default
- no `repobrain-community` change
