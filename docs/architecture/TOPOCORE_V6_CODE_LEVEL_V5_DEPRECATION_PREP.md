# TopoCore v6 Code-Level v5 Deprecation Preparation

## 1. Purpose

Sprint 62 prepares code-level v5 deprecation mechanics.
v6 is the active `issue_comment` lab default.
v5 is fallback-only and a deprecation candidate.
This sprint does not remove v5.
This sprint does not disable fallback.
This sprint does not change runtime behavior.

## 2. Current Operating State

Latest accepted `main` before Sprint 62:

- `b0869ba Mark v5 as deprecation candidate`

Current operating state:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
- v6 `issue_comment` lab default active
- v5 fallback-only
- v5 removal not approved
- kill switch remains `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`

## 3. v5 Seam Classification

| Seam | Current role | Classification | Current tests | Future action |
|---|---|---|---|---|
| `repobrain/topocore_backend.py` | resolves backend policy and legacy env precedence | `fallback_required`, `deprecation_candidate`, `migrate_to_v6` | `tests/test_topocore_backend_selection.py`, `tests/test_topocore_backend_lab_default_policy.py` | keep fallback logic now, later reduce legacy-default assumptions |
| `repobrain/tky_local.py` | local provider chooses v6 first and falls back to v5 engine | `fallback_required`, `keep_as_kill_switch`, `needs_more_evidence` | backend selection/review/verify/fix-lite tests | preserve fallback path now, add v5-off simulation next |
| `repobrain/tky_engine.py` | legacy engine request/decision contract used by v5-side flow | `fallback_required`, `removal_candidate_later` | backend tests that assert v5 engine behavior | keep stable until fallback retirement plan exists |
| `repobrain/tkya/engine.py` | legacy v5 or lite engine loader plus `RB_TKYA_BACKEND` compatibility | `fallback_required`, `keep_as_kill_switch`, `removal_candidate_later` | backend selection and lab switch tests | retain for fallback and kill switch, classify vendor-specific assumptions later |
| `repobrain/github_flow.py` | renders gate=`0` and scoped fallback semantics in GitHub path | `keep_as_kill_switch`, `migrate_to_v6` | gate propagation and routing tests | keep runtime output stable, no deprecation wiring yet |
| `action.yml` | still defaults `topocore_backend` to `v5` and exports `RB_TKYA_BACKEND=v5` | `fallback_required`, `deprecation_candidate`, `keep_as_kill_switch` | `tests/test_github_runtime_v6_lab_switch.py` | later update only with explicit workflow/action checkpoint |
| `.github/workflows/repobrain.yml` | gate=`0` still forces v5-side behavior and skips private checkout/install | `keep_as_kill_switch`, `fallback_required`, `needs_more_evidence` | issue-comment gate and lab switch tests | preserve current semantics until v5-off simulation is approved |

## 4. v5 Test Classification

| Test file | Current purpose | Classification | Keep / migrate / remove / add-next | Notes |
|---|---|---|---|---|
| `tests/test_topocore_backend_selection.py` | backend precedence, `RB_TKYA_BACKEND`, default fallback, safe v6 fallback markers | fallback safety | keep now | core proof that v5 fallback remains available |
| `tests/test_topocore_backend_lab_default_policy.py` | auto prefers v6, but fallback to v5 stays safe; GitHub pin remains supported | mixed: v6 default plus v5 fallback | keep now, migrate later | some assertions about GitHub-style v5 pin will need rewording later |
| `tests/test_topocore_backend_review_verify.py` | review/verify task-family behavior under v5 and v6 | fallback safety plus migrate-to-v6 | keep now | later split target-runtime assumptions from fallback checks |
| `tests/test_topocore_backend_fix_lite.py` | conservative fix-lite routing and no patch/autofix under v5 and v6 | fallback safety | keep now | remains relevant until fix-lite contract changes |
| `tests/test_github_issue_comment_v6_lab_runtime.py` | gate=`1` v6 lab runtime and gate=`0` v5 safety | kill switch | keep now | critical until fallback retirement is explicitly approved |
| `tests/test_github_issue_comment_v6_gate_env_propagation.py` | gated local-provider/backend propagation and explicit v5 kill switch | kill switch | keep now | still required while gate=`0` exists |
| `tests/test_github_runtime_v6_lab_switch.py` | workflow/action defaults, private dependency off by default, v5 pin compatibility | mixed: safety and old defaults | keep now, migrate later | action default `v5` is now fallback-oriented, not target-oriented |
| `tests/test_github_runtime_v6_dependency_gate.py` | no default private dependency and guarded private checkout | safety invariant | keep now | independent of v5 target status |

Grouped outcome:

Keep now:

- tests that prove gate=`0` kill switch
- tests that prove fallback when v6 is unavailable
- tests that prove no default private dependency in CI
- tests that prove no `decide_raw`
- tests that prove no patch or autofix

Migrate later:

- tests that still assume `action.yml` or workflow defaults describe the primary target runtime rather than the fallback path
- tests that treat old TKYA output as the main intended runtime rather than the kill switch behavior

Remove later:

- tests that only protect v5 internals after fallback retirement, once fallback is intentionally removed

Add next:

- v5-off simulation tests
- fallback-disabled configuration tests
- deprecation warning or metadata tests
- v5 removal guard tests

## 5. Deprecation Metadata

Sprint 62 adds:

- `repobrain/topocore_deprecation.py`

The module is dependency-free and import-safe.
It does not import `topocore_v6`.
It does not import the v5 engine.
It does not read environment variables at import time.
It does not affect runtime selection.

Constants:

- `TOPOCORE_V5_STATUS = "deprecation_candidate"`
- `TOPOCORE_V5_ROLE = "fallback_only"`
- `TOPOCORE_V6_STATUS = "active_lab_default"`
- `TOPOCORE_V5_REMOVAL_APPROVED = False`
- `TOPOCORE_V5_CODE_DEPRECATION_ACTIVE = False`
- `TOPOCORE_V5_FALLBACK_REQUIRED = True`

Helper:

- `get_topocore_deprecation_policy()`

These values are for policy, docs, and tests only.
They are not wired into backend selection or user-facing output in Sprint 62.

## 6. v5-Off Simulation Plan

Proposed future variable:

- `RB_TOPOCORE_V5_SIMULATE_DISABLED=1`

Intended future behavior:

- simulate v5 unavailability without deleting v5 files
- stay opt-in
- remain off by default
- not affect default CI
- not affect the gate=`0` kill switch until explicitly approved
- not break fallback unexpectedly

Expected future tests:

- v5-off simulation while v6 is healthy
- explicit failure behavior when both v6 and simulated-v5-off are unavailable
- gate=`0` kill switch expectations under an approved simulation mode
- rollback to the normal fallback path

Why not enabled in Sprint 62:

- simulation changes runtime behavior, even if guarded
- Sprint 62 is limited to preparation and classification
- Sprint 63 can implement it in a controlled way

Sprint 63 follow-up:

- the planned opt-in simulation is now implemented
- see `docs/architecture/TOPOCORE_V6_OPT_IN_V5_OFF_SIMULATION.md`

## 7. Entry Gates for Code-Level Deprecation

Before active code-level deprecation:

- metadata exists
- tests classify v5 seams
- gate=`0` kill switch still green
- v6 lab default remains stable
- fallback behavior tests still pass
- v5-off simulation plan is accepted
- explicit approval exists

## 8. Entry Gates for v5 Removal

Before removal:

- v5-off simulation passes
- fallback replacement is accepted
- v5-specific tests are migrated or removed intentionally
- workflow and action defaults are updated intentionally
- at least one checkpoint exists after code-level deprecation
- rollback plan exists
- explicit approval exists

## 9. Recommended Next Step

Recommended next sprint:

- `Sprint 63 - Implement Opt-In v5-Off Simulation`

Recommended scope:

- add `RB_TOPOCORE_V5_SIMULATE_DISABLED=1` behavior
- keep it off by default
- no deletion
- no workflow or action default change
- tests prove v6 still works and gate=`0` behavior is understood
- rollback is documented

## 10. Non-Goals

- no runtime behavior change
- no workflow or `action.yml` change
- no repository variable change
- no v5 removal
- no fallback disablement
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change
