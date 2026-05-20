# TopoCore v6 Final v6-Only Closeout

## 1. Purpose

Sprint 68 closes the v5-to-v6 TopoCore runtime transition.
It follows Sprint 65 runtime removal, Sprint 66 vendor removal, and Sprint 67 final residue cleanup.
v6 is the only supported TopoCore runtime path.
This sprint records live sanity and final static proof.

## 2. Baseline

- latest accepted `main` before Sprint 68:
  - `1ae2463 Remove final v5 residue`
- Sprint 65:
  - v5 runtime execution removed
- Sprint 66:
  - v5 vendor assets removed
- Sprint 67:
  - standalone v5 guides removed
- current repo variable:
  - `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

## 3. Current Runtime Policy

Supported selectors:

- `auto`
- `v6`

Unsupported legacy selectors and envs:

- `v5`
- `lite`
- `RB_TKYA_BACKEND` values `v5` and `lite`
- `RB_TOPOCORE_ALLOW_DEPRECATED_V5`
- `RB_TOPOCORE_V5_SIMULATE_DISABLED`

Current runtime behavior:

- v6 unavailable means safe failure
- no v5 fallback exists
- `workflow_dispatch` `v6` plus `private_checkout` remains available

## 4. Live v6 Sanity Result

Live sanity was run on `main` through issue `#113`.

- issue URL:
  - `https://github.com/alexworkingai/RepoBrain-Action/issues/113`
- workflow run URL:
  - `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26168571200`
- workflow conclusion:
  - `success`
- requested backend:
  - `auto`
- resolved backend:
  - `v6`
- fallback used:
  - `no`
- fallback reason:
  - `none`
- TKY mode requested:
  - `local`
- TKY mode used:
  - `local`
- TKYA mode:
  - `topocore_v6`
- diagnostic status:
  - route `REVIEW`
  - rationale `TopoCore v6 external decision: status=needs_review action=investigate message_code=DEEP_REVIEW_RECOMMENDED`

Safety result:

- no `decide_raw`
- no patch application
- no file modification by RepoBrain behavior
- no commit, branch, or PR creation by RepoBrain behavior
- no unsafe approval, security, or safe-to-merge claims
- no secret or private URL exposure

## 5. Optional workflow_dispatch Result

The optional manual `workflow_dispatch` sanity was also run on `main`.

- run URL:
  - `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26168656500`
- workflow conclusion:
  - `success`
- requested backend:
  - `v6`
- resolved backend:
  - `v6`
- fallback used:
  - `false`
- fallback reason:
  - `none`
- artifact evidence:
  - `repobrain-lab-backend-evidence`
  - `route=FAST`
  - `status=ready`
  - `action=proceed`
  - `message_code=DECISION_READY`
  - `confidence_band=high`

## 6. Static Proof

Sprint 68 static proof confirms:

- deleted standalone v5 architecture guide: absent
- deleted standalone v5 complete guide: absent
- `repobrain/tkya/vendor`: absent
- `.github/workflows/canary_v5.yml`: absent
- active code, tests, workflows, and `action.yml` lower-case `topocore_v5`: clean
- active code, tests, workflows, and `action.yml` v5 vendor wording: clean
- active workflow and action supported choices for `v5` and `lite`: absent

## 7. Remaining Allowed Legacy References

Remaining legacy references are limited to:

- historical migration docs
- unsupported legacy env diagnostics
- compatibility stubs and contracts
- absence and removal tests

## 8. Safety Boundaries

- no patch application
- no file modification by RepoBrain behavior
- no commit, branch, or PR creation by RepoBrain behavior
- no production or Marketplace switch
- no `repobrain-community` change

## 9. Final Decision

`FINAL_CLOSEOUT_PASSED`

Live sanity passed and final static proof passed.

## 10. Next Step

No more v5 migration or removal sprint is needed.
Next work should be v6 quality and product work rather than v5 cleanup.

## 11. Non-Goals

- no runtime behavior change
- no workflow or action behavior change
- no patch or autofix
- no production or Marketplace switch
- no `repobrain-community` change
