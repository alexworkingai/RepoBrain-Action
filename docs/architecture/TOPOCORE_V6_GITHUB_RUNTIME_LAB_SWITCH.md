# TopoCore v6 GitHub Runtime Lab Switch

## 1. Purpose

Sprint 47 adds a reversible GitHub runtime lab switch for TopoCore v6.
Default GitHub `issue_comment` behavior remains pinned to v5.
Manual `workflow_dispatch` can request `v5`, `v6`, or `auto`.
v5 fallback remains available.
Sprint 47 does not install private TopoCore v6 into GitHub Actions.
Sprint 47 does not remove v5.
Sprint 47 does not enable patch application.

## 2. Current Baseline

- latest accepted main before Sprint 47: `3a06ec6 Make TopoCore v6 default lab backend policy`
- Sprint 46 made lab/local no-env policy v6-preferred `auto`
- GitHub runtime remained v5-pinned before Sprint 47
- `action.yml` and `.github/workflows/repobrain.yml` were unchanged before Sprint 47

## 3. GitHub Runtime Policy

- `issue_comment` default remains v5
- `workflow_dispatch` default remains v5
- `workflow_dispatch` may choose `v5`, `v6`, or `auto`
- action input default is `v5`
- `RB_TOPOCORE_BACKEND` controls selector behavior when passed
- `RB_TKYA_BACKEND=v5` remains the compatible pin behavior inside the action

## 4. Lab Switch Behavior

- `v5`: force v5
- `v6`: try v6, fallback to v5 unless strict local mode is enabled
- `auto`: try v6, fallback to v5 unless strict local mode is enabled
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

- default GitHub behavior stays on v5
- manual `v6` or `auto` selection falls back to v5 when v6 is unavailable
- strict local mode remains opt-in
- no raw paths or secrets are exposed in backend-selection errors

## 8. Sprint 48 Target

Sprint 48 — GitHub Lab v6 Dependency Strategy / Optional Private Install Gate

Expected:
- decide whether manual GitHub v6 lab runs should install private TopoCore v6
- choose between no install, local artifact, private package, or private checkout
- keep default `issue_comment` v5 unless explicitly changed later
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
