# TopoCore v6 Observation and v5 Deprecation Runway

## 1. Purpose

Sprint 56 creates the v6 observation checklist and the v5 deprecation runway.
It does not remove v5.
It does not mark v5 deprecated in code.
It does not change runtime, workflow, or `action.yml` behavior.
It keeps the current safe gate-disabled state.

## 2. Current State

Latest accepted `main` before Sprint 56:

- `477ba5f Assess v5 deprecation readiness`

Current repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`

Current operating state:

- v6 lab mode is proven but disabled
- v5 default safe mode is active for `issue_comment`
- `workflow_dispatch` v6 `private_checkout` remains available
- v5 fallback remains available as a temporary safety net

## 3. Strategic Direction

- v5 fallback should not be treated as indefinite
- the project is moving from migration validation into deprecation preparation
- deprecation must remain evidence-gated, not automatic
- removal is not approved
- short, measurable, repeatable observation is preferred over another broad planning loop

## 4. Observation Window

Recommended observation window:

- `5` to `10` `issue_comment` runs
- across `2` to `3` days or one focused validation session
- with temporary gate enablement:
  - `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
- after observation:
  - set the gate back to `0`
  - or explicitly decide to keep gate=`1` as the lab default

Required scenario families:

1. issue `ask`
2. issue `locate` or `explain` style question
3. issue review-like question
4. PR `ask` on a small PR
5. PR review on a small PR
6. PR verify-like command
7. fix-lite governance command without patch application
8. dependency-unavailable fallback simulation if practical
9. gate-disabled kill-switch rerun
10. `workflow_dispatch` v6 `private_checkout` sanity rerun

Observation rules:

- Stage 1 observation must be deliberate and time-bounded
- no patch application is allowed
- no commit, branch, or PR creation is allowed
- no secret or private path exposure is allowed

## 5. Evidence Bundle Format

Each observation run should capture the following fields:

- run id or run URL
- event
- command
- gate value
- requested backend
- resolved backend
- fallback used
- fallback reason
- route
- status
- action
- `message_code`
- `confidence_band`
- diagnostic result
- private checkout result
- private install result
- `decide_raw` used
- patch application
- commit, branch, or PR creation
- workflow conclusion
- user-visible output notes

Preferred bundle interpretation:

- `requested_backend`, `resolved_backend`, `fallback_used`, and `fallback_reason` are the minimum backend proof
- legacy `TKYA backend` anchors may remain useful, but they are not sufficient by themselves

## 6. Success Criteria

Observation succeeds only if all of the following remain true:

- `resolved_backend=v6` for gate=`1` scenarios when the private dependency is available
- `fallback_used=false` for healthy v6 scenarios
- fallback to v5 works when gate=`0`
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no unsafe user-visible claims
- no workflow dependency drift
- no secret or private path exposure
- no unexpected `issue_comment` failures

## 7. Failure Criteria

Observation must stop or be classified as failed if any of the following occur:

- v6 is unavailable when the private dependency should be available
- `resolved_backend=v5` under gate=`1` without a clear fallback reason
- backend evidence is missing
- any `decide_raw` exposure
- any patch or autofix side effect
- any commit, branch, or PR creation
- any unsafe security or approval claim
- any secret or private URL exposure
- repeated workflow instability

## 8. Deprecation Runway

Stage 0 - Current state

- gate=`0`
- v5-side default
- v6 proven behind gate
- current state after Sprint 55

Stage 1 - Observation

- temporarily enable gate=`1`
- run the observation matrix
- collect evidence
- no code changes required
- no v5 removal

Stage 2 - Lab default decision

- if observation passes, decide whether to keep gate=`1`
- v5 remains fallback
- docs may mark v5 as fallback or legacy candidate
- no v5 removal

Stage 3 - Deprecation candidate

- after successful observation and explicit approval
- update docs to mark v5 as a deprecated candidate
- add tests for v5-off or v5-disabled behavior if feasible
- still no removal

Stage 4 - Code deprecation

- only after an explicit checkpoint
- warnings or docs may mark v5 deprecated
- all fallback behavior must be tested
- no removal yet

Stage 5 - Removal proposal

- only after longer evidence collection
- separate approval required
- dedicated rollback plan required
- no automatic deletion

Clarification:

- Sprint 56 stays at Stage 0
- Sprint 56 prepares Stage 1
- Sprint 57 may enter Stage 1 if explicitly approved

## 9. v5 Fallback Exit Criteria

v5 fallback can stop being the default safe mode only when all of the following are true:

- the observation window passed
- gate=`1` proved stable
- the kill switch was retested
- v6 handled both issue and PR scenarios
- the fallback path was tested
- no unsafe outputs appeared
- no workflow instability appeared
- explicit approval was recorded

## 10. v5 Deprecation Criteria

v5 can only be marked deprecated after all of the following are true:

- fallback is no longer used during observation except for forced fallback tests
- v6 covers the active command families
- docs are updated
- tests cover both gate=`1` and gate=`0`
- the private dependency strategy is stable
- a rollback plan is documented
- explicit approval exists

## 11. v5 Removal Criteria

v5 removal requires stricter future gates:

- the deprecation checkpoint is completed
- a v5-off test plan is completed
- all v5-specific tests are classified
- workflow and action behavior are updated intentionally
- a fallback replacement is accepted
- a rollback plan exists
- explicit approval exists

## 12. Scorecard

| Area | Current status | Evidence source | Remaining work | Deprecation impact |
|---|---|---|---|---|
| ask | Proven | `tests/test_topocore_backend_lab_default_policy.py`, Sprint 54 closeout | repeat in live observation | Required |
| review | Proven | `tests/test_topocore_backend_review_verify.py`, Sprint 54 gate=`1` route evidence | repeat on live PR or issue scenarios | Required |
| verify | Proven | `tests/test_topocore_backend_review_verify.py` | repeat in live PR scenario | Required |
| fix-lite | Proven | `tests/test_topocore_backend_fix_lite.py` | live governance-only sample | Required |
| `issue_comment` gate=`1` | Proven | Sprint 53 fix, Sprint 54 closeout | repeated observation window | Required |
| `issue_comment` gate=`0` | Proven | Sprint 54 closeout | periodic kill-switch retest | Required |
| `workflow_dispatch` v6 | Proven | Sprint 49 to 51 docs and tests | sanity rerun during observation cycle | Required |
| private dependency | Proven | Sprint 48 to 51 docs and tests | repeated stability evidence | Required |
| runtime diagnostic | Proven | Sprint 50 docs and tests | repeated healthy-run evidence | Required |
| fallback | Proven | backend tests plus gate=`0` evidence | explicit fallback simulation under gate=`1` if practical | Required |
| kill switch | Proven | Sprint 54 closeout | retest during observation | Required |
| PR changed-files context | Needs observation | review and verify tests only | live small-PR sampling | Required |
| issue-only context | Proven | gate=`1` issue evidence | more than one repeated run | Required |
| no `decide_raw` | Proven | static tests and diagnostics policy | keep unchanged | Required |
| no patch or autofix | Proven | fix-lite tests and workflow tests | keep unchanged during observation | Required |
| no commit, branch, or PR creation | Proven | GitHub workflow tests and fix-lite tests | keep unchanged during observation | Required |
| user-visible output | Needs observation | safe output rendering tests and Sprint 54 notes | repeated operator sanity review | Required |
| repeated run stability | Needs observation | not yet established | observation window | Required |
| v5-off readiness | Blocked | Sprint 55 assessment | dedicated v5-off plan and classification | Required before removal |
| production or Marketplace readiness | Not applicable | outside current scope | separate track if ever approved | Not required for lab runway |

## 13. Recommended Next Step

Recommended next sprint:

- `Sprint 57 - v6 Observation Window Execution Plan`

Recommended scope:

- still no code changes unless required for evidence collection
- temporarily set `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1` only during approved observation
- run the observation matrix
- collect evidence
- decide whether to keep gate=`1` or return to `0`
- no v5 removal

Observation results link:

- `docs/architecture/TOPOCORE_V6_SPRINT_57_OBSERVATION_RESULTS.md`
- `docs/architecture/TOPOCORE_V6_PR_PATH_AND_SCOPED_COMMAND_OBSERVATION_FIX.md`

## 14. Non-Goals

- no runtime behavior change
- no workflow or `action.yml` change
- no repository variable change
- no v5 removal
- no v5 code deprecation
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change
