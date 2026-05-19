# TopoCore v6 v5 Deprecation Readiness Assessment

## 1. Purpose

Sprint 55 assesses readiness for a future v5 deprecation track.
It does not deprecate v5.
It does not remove v5.
It does not change runtime behavior.
It keeps `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0` as the current safe operational state.

## 2. Current Operating Model

Current safe operating model:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- `issue_comment` remains on the v5-side path by default
- controlled v6 lab mode is proven but currently disabled
- `workflow_dispatch` v6 `private_checkout` remains available for manual validation
- v5 fallback remains available

Operational interpretation:

- the repository can prove a controlled v6 lab path when explicitly enabled
- the repository still intentionally operates in the v5-side mode by default
- no code-level deprecation signal for v5 is justified yet

## 3. Proven v6 Capabilities

The following v6 capabilities are already proven in code, tests, or operational evidence:

- Sprint 42:
  - real adapter contract lock
  - real TopoCore v6 adapter implementation
- Sprint 43:
  - runtime backend selector
- Sprint 44:
  - review and verify backend expansion
- Sprint 45:
  - guarded fix-lite decision path
- Sprint 46:
  - local and lab default `auto` policy with v6-preferred behavior when available
- Sprint 47:
  - `workflow_dispatch` GitHub runtime lab switch
- Sprint 48:
  - private dependency gate for manual GitHub v6 lab runs
- Sprint 49:
  - meaningful `workflow_dispatch` v6 decision path
- Sprint 50:
  - runtime import diagnostic and import/API blocker fix
- Sprint 51:
  - optional TKYA evidence artifact no longer false-fails v6 lab runs
- Sprint 52:
  - controlled `issue_comment` v6 lab runtime design
- Sprint 53:
  - gate and env propagation fix for `issue_comment`
  - explicit backend evidence fields:
    - `requested_backend`
    - `resolved_backend`
    - `fallback_used`
    - `fallback_reason`
- Sprint 54 operational evidence:
  - gate `1` can resolve `issue_comment` to v6
  - gate `0` keeps `issue_comment` on the v5-side path

Command-family coverage already proven through tests or bounded operational evidence:

- ask-like path
- review-like path
- verify-like path
- guarded fix-lite decision path

Safety boundaries proven to remain intact on the v6 track:

- no `decide_raw`
- no patch application
- no commit creation
- no branch creation
- no PR creation

## 4. Remaining v5 Responsibilities

v5 and TKYA still provide active responsibilities that prevent immediate deprecation:

- default safe `issue_comment` behavior while `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- fallback behavior when TopoCore v6 is unavailable
- compatibility with the existing `action.yml` default `topocore_backend=v5`
- compatibility with `RB_TKYA_BACKEND`
- baseline local provider behavior through:
  - `repobrain/tky_local.py`
  - `repobrain/tky_engine.py`
  - `repobrain/tkya/engine.py`
- legacy diagnostic anchors such as:
  - `TKYA backend`
  - `TKYA mode`
- v5-side behavior when the private dependency is unavailable or not enabled

Tests and documentation that still depend on v5 remaining present include:

- `tests/test_topocore_backend_selection.py`
- `tests/test_topocore_backend_lab_default_policy.py`
- `tests/test_topocore_backend_review_verify.py`
- `tests/test_topocore_backend_fix_lite.py`
- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`

These artifacts show that v5 is still part of the supported runtime story, not only a legacy leftover.

## 5. Not Yet Proven

The following areas are not yet proven well enough to support deprecation or removal planning beyond assessment:

- sustained `issue_comment` v6 operation over time
- a repeated gate=`1` observation window
- PR-based workloads across varied PR shapes and repositories
- verification-heavy workloads in repeated live usage
- high-volume or concurrent GitHub Actions behavior
- private dependency outage handling over time
- v6 behavior with non-trivial changed-file sets and broader live diffs
- patch or fix behavior beyond fix-lite governance
- production or Marketplace readiness
- a truly v5-free runtime

## 6. Deprecation Blockers

Current hard blockers to any future v5 deprecation decision include:

- insufficient repeated v6 `issue_comment` evidence
- no v5-off test plan
- no sustained observation window with gate=`1`
- no PR workload matrix across representative scenarios
- no long-running private dependency availability policy
- any unresolved fallback ambiguity under partial v6 failure
- any user-visible regression in `issue_comment` output
- any `decide_raw` leakage
- any patch or autofix unsafe behavior
- any missing rollback or kill-switch plan
- any unresolved workflow dependency drift

Until those blockers are addressed, v5 should remain active and non-deprecated.

## 7. Deprecation Readiness Criteria

Before marking v5 deprecated in documentation or policy, the repository should satisfy all of the following:

- a gate=`1` observation window is completed
- the gate=`0` kill switch is retested
- `workflow_dispatch` v6 `private_checkout` remains green
- `issue_comment` v6 diagnostics remain stable
- fallback evidence remains stable and understandable
- ask, review, verify, and fix-lite coverage remains confirmed
- PR-based scenarios are sampled
- private dependency access remains stable
- docs are updated to explain deprecation status without removing v5
- no patch or autofix expansion is introduced
- explicit approval is recorded

## 8. Removal Readiness Criteria

Removing v5 is a stricter future decision than merely marking it deprecated.
Before any removal work, all of the following should be true:

- v5 is documented as deprecated for an explicit checkpoint period
- v6 has sufficient operational history
- a fallback replacement exists or removal risk is explicitly accepted
- all v5-specific tests are classified as:
  - migrate
  - remove
  - keep as legacy coverage
- workflow and action defaults are intentionally updated
- v5 vendor assumptions are removed
- a rollback plan exists
- explicit removal approval exists

## 9. Recommended Next Step

Given `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0` is intentionally preserved:

- no immediate runtime sprint is recommended
- do not deprecate v5 yet
- the next optional sprint should be:
  - `Sprint 56 - v6 Lab Observation Checklist and Repeated Issue Comment Evidence`
- that sprint should remain docs and test planning first
- only after that should the project consider leaving gate=`1` enabled for an observation window

See also:

- `docs/architecture/TOPOCORE_V6_OBSERVATION_AND_V5_DEPRECATION_RUNWAY.md`

## 10. Decision

Current decision:

- NO-GO for v5 removal now
- NO-GO for code-level v5 deprecation now
- GO for future v6 observation planning
- GO for keeping v6 lab mode available behind the gate
- GO for keeping the current safe gate-disabled state
- GO for beginning deprecation preparation without deprecating v5 yet

## 11. Non-Goals

- no runtime behavior change
- no workflow or `action.yml` change
- no repository variable change
- no v5 removal
- no v5 code deprecation
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change
