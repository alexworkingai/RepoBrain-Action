# Refactor Phase Closeout

## 1. Purpose

This document closes the post-Sprint 78 refactor phase after Refactor Sprints 0-14.

It freezes the current safe baseline, records the stop decision, and makes the default next move explicit:

- stop refactoring by default
- preserve the accepted safety baseline
- return future work to product roadmap planning unless a specific regression or product-driven refactor need appears

## 2. Final state summary

- `RepoBrain-Action` is now cleaned up as the core/docs/tests/current-truth repository.
- `repobrain-community` owns the public external runtime and the canonical public install template.
- `elen-mcp-prod_v2` remains validation-only.
- external CLI ask-only and MCP ask-only remain bounded secondary surfaces in `RepoBrain-Action`.
- the primary `RepoBrain-Action` PR UI contract remains distinct from the external GitHub foundation contract.

Operationally, this means:

- public third-party GitHub-native runtime truth lives in the external foundation hosted through `repobrain-community`
- internal/core governance, regression protection, and runtime-adjacent safety truth remain owned in `RepoBrain-Action`
- validation evidence may come from `elen-mcp-prod_v2`, but that repository is not a source of current product truth

## 3. Sprints completed

### Sprints 0-7

These sprints established the documentation and ownership baseline:

- docs truth cleanup
- repository boundary cleanup
- legacy external surface retirement
- historical docs labeling
- community packaging deduplication
- Fix-Lite terminology normalization
- canonical repository boundary contract freeze

### Sprint 8

Sprint 8 mapped the runtime entrypoint dependency graph and identified:

- active entrypoints that must remain
- regression-protecting legacy surfaces
- unsafe early removal targets
- the smallest safe refactor starting point

### Sprints 9-14

These sprints characterized and then selectively micro-refactored the fix-path safety stack:

- Sprint 9: fix helper characterization and `patch_extract` micro-refactor
- Sprint 10: patch targeting characterization
- Sprint 11: patch targeting micro-refactor
- Sprint 12: patch validator characterization
- Sprint 13: patch validator micro-refactor
- Sprint 14: patch guard characterization top-up

## 4. Fix-path safety baseline

The accepted fix-path safety baseline after Sprint 14 is:

- `patch_extract` characterized and micro-refactored
- `patch_targeting` characterized and micro-refactored
- `patch_validator` characterized and micro-refactored
- `patch_guard` characterized; no micro-refactor is needed now
- `NO_PATCH` / no-action governance preserved across all refactor sprints
- primary PR UI `/repobrain fix` validation repeatedly returned safe `no_patch` outcomes after runtime-adjacent refactors

Safe behavior that remains intentionally preserved:

- no autofix
- no patch application claim
- no file modification claim
- no commit creation claim
- no branch push claim
- no PR creation claim
- no safe-to-merge claim
- no security verdict
- no approval/rejection verdict

## 5. Explicit stop decision

The refactor phase should stop here by default.

Decisions:

- do not continue refactoring by default
- `patch_guard.py` micro-refactor is skipped for now
- `github_flow.py` split is deferred
- `external_flow.py` and `mcp_surface.py` refactors are deferred
- workflow wiring refactors are deferred
- TKYA/TopoCore contract changes are deferred

Reason:

- Sprint 14 showed coverage is already strong enough around `patch_guard.py`
- there is no obvious cleanup that is worth more runtime-adjacent churn
- further refactoring now has diminishing returns

Future refactoring requires a product-driven reason, not polish for its own sake.

## 6. What must not regress

The following must remain true:

- no stale external workflow/template copies in `RepoBrain-Action`
- no current docs saying the external GitHub foundation is ask-only
- no current docs saying review/fix are unsupported for the public external GitHub foundation
- no autofix claim
- no patch application claim
- no file modification claim
- no commit/branch/PR creation claim
- no safe-to-merge claim
- no security verdict
- no approval/rejection verdict
- no weakening of `NO_PATCH` governance

The two-contract distinction must also remain explicit:

- `RepoBrain-Action` primary PR UI
- `repobrain-community` external GitHub foundation

## 7. Recommended next product phase

This document does not start that work. It only points the next phase in the right direction.

Recommended next product phase:

- roadmap planning for stronger review/fix functionality
- define the full-review target carefully before expanding claims
- define any fix-capability expansion only after safety gates and validation discipline are specified
- consider structure/ontology/code-quality scoring as a separate product epic
- keep the two-contract distinction explicit:
  - `RepoBrain-Action` primary PR UI
  - `repobrain-community` external GitHub foundation

## 8. Acceptance baseline

Baseline local gates remain:

- `ruff`
- `pytest`
- env reference check
- usersafe scan
- TKYA contract guard
- git diff check

Acceptance rules remain:

- runtime-adjacent code changes require PR/CI and primary PR UI review/fix validation
- docs/tests-only changes require PR/CI merge closeout, but do not always require PR UI command validation

## 9. Final statement

Refactor phase is closed. Further work should return to product roadmap unless a specific regression or product-driven refactor need appears.
