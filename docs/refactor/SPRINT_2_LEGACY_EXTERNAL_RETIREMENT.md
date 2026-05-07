# Sprint 2 Legacy External Surface Retirement

## Purpose

Sprint 2 retires stale legacy external-surface copies from `RepoBrain-Action` after Sprint 78 public-surface acceptance and Sprint 1 docs truth freeze.

This sprint is intentionally narrow. It does not refactor runtime Python code, change active workflow behavior, or modify external repositories.

## Canonical Public Runtime Host

The canonical public external runtime host is:

- `repobrain-community`

Canonical public reusable workflow path:

- `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`

`RepoBrain-Action` is not the public external runtime host.

## Files Reviewed

Delete candidates reviewed in this sprint:

1. `.github/workflows/repobrain_external_foundation.yml`
2. `docs/repobrain_template.yml`

Reference inputs reviewed:

- `docs/refactor/SPRINT_0_REPO_BOUNDARY_INVENTORY.md`
- `docs/refactor/STALE_EXTERNAL_SURFACE_CANDIDATES.md`
- `docs/refactor/KEEP_MOVE_DELETE_MATRIX.md`

Reference/dependency search covered:

- `.github/`
- `docs/`
- `tests/`
- `scripts/`
- `repobrain/`
- `README.md`
- `pyproject.toml`
- `action.yml`

## Dependency Evidence

### Candidate A: `.github/workflows/repobrain_external_foundation.yml`

Search evidence:

- active hits were limited to the file itself and Sprint 0 inventory docs
- no active tests referenced the local legacy workflow path
- current public-facing template/runbook references point to `repobrain-community`, not this local copy

Why it qualified for retirement:

- it preserved an older ask-only boundary
- it directly invoked `alexworkingai/RepoBrain-Action@main`
- it was no longer the canonical public external runtime host
- removing it does not alter active RepoBrain-Action runtime behavior

Final decision:

- `DELETE_NOW`

### Candidate B: `docs/repobrain_template.yml`

Search evidence:

- active hits were limited to the file itself and Sprint 0 inventory docs
- no current tests referenced this path
- the file still used placeholder `OWNER/REPO@v0.1.0` wiring
- canonical public install-template references already point to `repobrain-community/templates/repobrain.yml`

Why it qualified for retirement:

- it was a stale direct-action template shape
- it contradicted the accepted community-hosted install shape
- removing it does not alter active RepoBrain-Action runtime behavior

Final decision:

- `DELETE_NOW`

## Files Deleted

- `.github/workflows/repobrain_external_foundation.yml`
- `docs/repobrain_template.yml`

## References Updated

- no current docs or tests required path rewrites for these two deleted files
- remaining mentions are historical inventory records in `docs/refactor/`

## Validation Results

Validation was rerun after retirement changes:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## Scope Statement

No runtime behavior was intentionally changed in `RepoBrain-Action`.
