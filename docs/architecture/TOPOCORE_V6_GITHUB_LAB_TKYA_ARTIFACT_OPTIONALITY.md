# TopoCore v6 GitHub Lab TKYA Artifact Optionality

> Historical note: references below to v5 fallback or legacy `lite` execution are superseded. Sprint 65 removed deprecated v5 runtime execution, and Sprint 66 removed orphaned vendor assets. Current supported runtime policy is v6-only.


## 1. Purpose

Sprint 51 makes optional TKYA evidence artifact upload non-fatal for v6 lab `workflow_dispatch` runs.
Sprint 50 already proved real v6 lab backend execution through the lab backend evidence artifact.
The remaining failure was a legacy optional TKYA evidence upload with absent files.
This sprint fixes workflow artifact strictness only.

## 2. Current Baseline

- latest accepted `main` before Sprint 51: `f05e76c Fix GitHub TopoCore v6 lab import blocker`
- post-Sprint-50 manual run confirmed:
  - private checkout passed
  - private install passed
  - runtime v6 evidence artifact uploaded
  - evidence confirmed:
    - `requested_backend=v6`
    - `resolved_backend=v6`
    - `fallback_used=false`
    - `status=ready`
    - `action=proceed`
    - `message_code=DECISION_READY`
    - `confidence_band=high`
  - the workflow failed later on missing TKYA evidence pack files

## 3. Root Problem

- v6 lab backend execution is working
- the failure was caused by optional legacy TKYA evidence artifact upload being strict when files were absent
- missing TKYA evidence pack files are valid for this v6 lab run mode
- the lab backend evidence artifact is the relevant artifact for v6 lab validation

## 4. Fix

Sprint 51 changes the workflow step:

- `Upload RepoBrain TKYA evidence pack artifact`

The step now uses:

- `if-no-files-found: warn`

This keeps the missing-file condition visible in logs without failing the whole workflow.
It does not hide real v6 failures because the following still fail when broken:

- private checkout
- private install
- runtime import diagnostic
- meaningful lab command execution
- lab backend evidence generation

The dedicated lab backend evidence artifact remains preserved.

## 5. Safety Boundaries

- `issue_comment` is unchanged
- `workflow_dispatch` defaults are unchanged
- private checkout and install are unchanged
- runtime import diagnostic is unchanged
- no patch application
- no commit, branch, or PR creation
- no `decide_raw`

## 6. Expected Post-Merge Operational Check

Manual run:

- `topocore_backend=v6`
- `topocore_v6_dependency_mode=private_checkout`
- `topocore_v6_ref=main`
- `repobrain_lab_command=ask`
- `repobrain_lab_query="Summarize current RepoBrain TopoCore backend status."`
- `repobrain_lab_fixture=minimal`

Expected:

- overall workflow success
- lab backend evidence artifact uploaded
- evidence contains:
  - `requested_backend=v6`
  - `resolved_backend=v6`
  - `fallback_used=false`
  - `status` present
  - `action` present
  - `message_code` present
  - `confidence_band` present
- absent TKYA evidence pack files do not fail the run

## 7. Sprint 52 Decision

If the Sprint 51 post-merge operational check succeeds, Sprint 52 may implement:

- GitHub `issue_comment` v6 lab runtime with v5 fallback

If it fails, Sprint 52 should fix only the specific remaining blocker.

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
