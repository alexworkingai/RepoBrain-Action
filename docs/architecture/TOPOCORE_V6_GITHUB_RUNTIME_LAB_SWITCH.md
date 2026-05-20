# TopoCore v6 GitHub Runtime Lab Switch

> Sprint 67 status: This file is retained only as a historical checkpoint. For current runtime policy use `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`, `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`, and `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`.

> Historical note: references below to v5 fallback or legacy `lite` execution are superseded. Sprint 65 removed deprecated v5 runtime execution, and Sprint 66 removed orphaned vendor assets. Current supported runtime policy is v6-only.


## 1. Purpose

Sprint 47 adds a reversible GitHub runtime lab switch for TopoCore v6.
Default GitHub `issue_comment` behavior was pinned to v5 at Sprint 47 time; this file is now historical only.
Manual `workflow_dispatch` originally supported `v5`, `v6`, or `auto`; current supported selectors are `auto` and `v6` only.
v5 fallback has since been removed.
Sprint 47 does not install private TopoCore v6 into GitHub Actions.
Sprint 65 later removed v5 runtime execution.
Sprint 47 does not enable patch application.

## 2. Current Baseline

- latest accepted main before Sprint 47: `3a06ec6 Make TopoCore v6 default lab backend policy`
- Sprint 46 made lab/local no-env policy v6-preferred `auto`
- GitHub runtime remained v5-pinned before Sprint 47
- `action.yml` and `.github/workflows/repobrain.yml` were unchanged before Sprint 47

## 3. GitHub Runtime Policy

- historical only: `issue_comment` default remained v5 at Sprint 47 time
- historical only: `workflow_dispatch` default remained v5 at Sprint 47 time
- current supported `workflow_dispatch` selectors are `auto` and `v6`; historical `v5` selection is unsupported
- action input default later moved away from `v5`
- `RB_TOPOCORE_BACKEND` controls selector behavior when passed
- `RB_TKYA_BACKEND=v5` is now an unsupported legacy diagnostic input

## 4. Lab Switch Behavior

- historical only: `v5` once forced v5; it is now unsupported
- `v6` now requires v6 and fails safely if unavailable
- `auto` now uses v6 or fails safely if unavailable
- missing `topocore_v6` does not break default GitHub runtime
- real GitHub v6 execution still requires future private dependency or install work

## 5. What Sprint 47 Enables

- manual GitHub lab runs can request the v6 backend
- manual GitHub lab runs can request the `auto` backend policy
- default `issue_comment` path stays safe and v5-pinned
- a future sprint can decide whether manual GitHub v6 lab runs should install private TopoCore v6

## 6. What Sprint 47 Does Not Enable

- no private dependency install
- no default v6 GitHub runtime
- no canary
- no production or Marketplace switch
- no v5 removal
- no patch application
- no commit, branch, or PR creation
- no PR, comment, or check behavior change by default

## 7. Fallback and Failure Behavior

- current GitHub behavior no longer uses v5
- manual `v6` or `auto` selection now fails safely when v6 is unavailable
- strict local mode remains opt-in
- no raw paths or secrets are exposed in backend-selection errors

## 8. Sprint 48 Target

Sprint 48 — GitHub Lab v6 Dependency Strategy / Optional Private Install Gate

Expected:
- decide whether manual GitHub v6 lab runs should install private TopoCore v6
- choose between no install, local artifact, private package, or private checkout
- historical note only; the current issue-comment lab runtime is v6-only
- no v5 removal

## 9. Non-Goals

- no v5 removal
- no default v6 `issue_comment` runtime
- no private TopoCore v6 install
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no PR, check, or comment behavior change by default
- no `repobrain-community` change
