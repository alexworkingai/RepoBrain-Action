# Sprint 5: Community Packaging Surface Dedup

## Purpose

This sprint deduplicates remaining community packaging/install artifacts in
`RepoBrain-Action` after public external runtime ownership moved to
`repobrain-community`.

The goal is to reduce ownership confusion without changing runtime behavior or
current public command truth.

## Repository States and Local Paths

- Primary repository:
  `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`
- Public external runtime repository:
  `D:\ARIADNA_Minsk\1MyProjects\repobrain-community`
- Third-party validation repository:
  `D:\ARIADNA_Minsk\1MyProjects\elen-mcp-prod_v2`

At Sprint 5 start:

- `RepoBrain-Action`: `codex/refactor-4-historical-trial-labeling`
- `repobrain-community`: `codex/sprint-78-fix-lite-candidate`
- `elen-mcp-prod_v2`: `test/sprint-73-guidance-live-validation`

## Current Sprint 78 Truth

External GitHub foundation supports:

- `/repobrain doctor`
- `/repobrain help`
- `/repobrain ask <question>`
- `/repobrain review`
- `/repobrain fix`

Current meanings:

- `doctor` = setup health card
- `help` = command truth and boundaries
- `ask` = repo/PR/guidance-aware bounded answer
- `review` = bounded read-only Review Candidate
- `fix` = bounded Fix-Lite Candidate manual-only patch suggestion

Mandatory Fix-Lite boundary:

- `No patch was applied. No files were modified.`

## Candidate Files Reviewed

1. `docs/packaging/repobrain_external_github_foundation_template.yml`
2. `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`

## Reference and Dependency Evidence

### Template Candidate

`docs/packaging/repobrain_external_github_foundation_template.yml` was a local
copy of the public install template shape and pointed at the community-owned
reusable workflow host.

Evidence:

- current public canonical template already exists at
  `repobrain-community/templates/repobrain.yml`
- current public reusable workflow host already exists at
  `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`
- no runtime Python code or active workflow in `RepoBrain-Action` depended on
  the local template file
- direct references were limited to docs and one narrow docs-truth test

### Packaging Doc Candidate

`docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md` still carried useful navigation
value as a stable local entry point, but duplicated install/runbook detail that
belongs in `repobrain-community`.

Evidence:

- current docs still linked to this path
- readers may still expect a RepoBrain-Action packaging doc at this location
- the file could be reduced safely to a boundary/reference document without
  removing unique current-truth guidance

## Decision for Each Candidate

### 1. `docs/packaging/repobrain_external_github_foundation_template.yml`

- Decision: `DELETE_NOW`
- Reason:
  - stale local duplicate of community-owned install template material
  - not required by active runtime behavior
  - canonical template now belongs to `repobrain-community`

### 2. `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`

- Decision: `CONVERT_TO_BOUNDARY_STUB`
- Reason:
  - path is still useful for docs navigation inside `RepoBrain-Action`
  - content should point readers to `repobrain-community` instead of duplicating
    public install/runbook detail

## Files Deleted, Converted, or Retained

- Deleted:
  - `docs/packaging/repobrain_external_github_foundation_template.yml`
- Converted to boundary/reference stub:
  - `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`
- Retained with updated references:
  - `README.md`
  - `docs/EXTERNAL_MODE.md`
  - `docs/OPERATOR_QUICKSTART.md`
  - `docs/packaging/INSTALLATION_SHAPE.md`
  - `docs/USER_GUIDE.md`
  - `docs/packaging/PACKAGING_OVERVIEW.md`
  - `tests/test_external_github_foundation_workflow.py`

## Reference Updates

Direct references were updated to:

- point readers at `repobrain-community/templates/repobrain.yml`
- preserve `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md` as a local
  boundary/reference document
- keep the public reusable workflow host explicit where helpful

## Risks and Rollback Notes

Primary risk:

- documentation readers who previously used the local template path may need the
  new canonical path clarified

Rollback note:

- if downstream docs navigation proves confusing, the packaging boundary stub can
  be expanded slightly without restoring a local duplicate template

## Validation Results

Validation was run from `RepoBrain-Action` after the change set:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## Explicit Statement

No runtime behavior was intentionally changed in Sprint 5.
