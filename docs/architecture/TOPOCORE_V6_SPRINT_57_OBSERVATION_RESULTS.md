# TopoCore v6 Sprint 57 Observation Results

## 1. Purpose

Sprint 57 executes the v6 observation window from Sprint 56.
The goal is to decide whether `issue_comment` v6 lab mode should become the active lab default.
v5 is now treated as temporary fallback, not target runtime.
Sprint 57 does not remove v5.
Sprint 57 does not enable patch application.

## 2. Starting State

Latest accepted `main` before Sprint 57:

- `da8b947 Plan v6 observation and v5 deprecation runway`

Starting repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`

Expected observation setting:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Baseline:

- v5 fallback remains available
- safe issue fixture:
  - `https://github.com/alexworkingai/RepoBrain-Action/issues/111`
- safe PR fixture:
  - `https://github.com/alexworkingai/RepoBrain-Action/pull/87`

## 3. Observation Matrix

| ID | Event type | Scenario | Command/comment | Expected backend | Expected fallback | Required evidence | Result | Run URL | Notes |
|---|---|---|---|---|---|---|---|---|---|
| OBS-01 | `issue_comment` | issue ask | `/repobrain ask Summarize current RepoBrain TopoCore backend status.` | `v6` | `false` | requested/resolved backend, fallback, route/action/message_code, safety markers | PASS | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083130947` | gate=`1`; checkout/install/diagnostic all `success`; `requested_backend=auto`, `resolved_backend=v6`, `fallback_used=false`, route `REVIEW`, rationale included `status=needs_review action=investigate message_code=DEEP_REVIEW_RECOMMENDED` |
| OBS-02 | `issue_comment` | issue explain or locate style | `/repobrain ask Explain where RepoBrain selects the TopoCore backend.` | `v6` | `false` | requested/resolved backend, fallback, route/action/message_code, safety markers | PASS | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083180593` | gate=`1`; checkout/install/diagnostic all `success`; `requested_backend=auto`, `resolved_backend=v6`, `fallback_used=false`, route `REVIEW`, rationale included `status=needs_review action=investigate message_code=DEEP_REVIEW_RECOMMENDED` |
| OBS-03 | `issue_comment` | issue review-like question | `/repobrain review Summarize any risks in the current TopoCore v6 lab runtime gate.` | `v6` | `false` | requested/resolved backend, fallback, route/action/message_code, safety markers | FAIL | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083228917` | run succeeded, checkout/install/diagnostic all `success`, but user-visible output was PR-only guidance (`Review/fix is available in Pull Requests`) and no usable TopoCore backend evidence was emitted |
| OBS-04 | `issue_comment` | PR ask on small PR | `/repobrain ask Summarize this PR with TopoCore backend diagnostics.` | `v6` | `false` | requested/resolved backend, fallback, route/action/message_code, safety markers | FAIL | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083287326` | run succeeded and issue_comment v6 setup steps all passed, but audit showed `tky_engine=topocore_v5`, `tkya_backend=v5`, no explicit `requested_backend`/`resolved_backend`, and comment diagnostics referenced provider-unavailable/network override |
| OBS-05 | `issue_comment` | PR review on small PR | `/repobrain review Summarize review risks for this PR.` | `v6` | `false` | requested/resolved backend, fallback, route/action/message_code, safety markers | FAIL | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083359618` | run succeeded and v6 setup steps passed, but audit showed `tky_engine=topocore_v5`, `tkya_backend=v5`, and explicit TopoCore backend requested/resolved fields were missing |
| OBS-06 | `issue_comment` | PR verify-like command | `/repobrain verify Summarize verification status for this PR.` | `v6` | `false` | requested/resolved backend, fallback, route/action/message_code, safety markers | FAIL | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083422830` | verification comment returned successfully, but audit did not provide usable TopoCore backend requested/resolved evidence for the v6 observation requirement |
| OBS-07 | `issue_comment` | fix-lite governance | `/repobrain fix Summarize fix-lite governance status without applying patches.` | `v6` | `false` | requested/resolved backend, fallback, no patch/no repo mutation markers | FAIL | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083471633` | run succeeded and v6 setup steps passed, but user-visible output again returned PR-only guidance (`Review/fix is available in Pull Requests`) rather than a meaningful v6 fix-lite decision path |
| OBS-08 | `workflow_dispatch` | v6 private checkout sanity rerun | `ask / minimal / backend=v6 / dependency_mode=private_checkout` | `v6` | `false` | requested/resolved backend, fallback, status/action/message_code, import/install evidence | PASS | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083715128` | checkout/install/diagnostic all `success`; evidence artifact recorded `requested_backend=v6`, `resolved_backend=v6`, `fallback_used=false`, `status=ready`, `action=proceed`, `message_code=DECISION_READY`, `confidence_band=high` |
| OBS-09 | `issue_comment` | gate=`0` kill switch rerun | `/repobrain ask Summarize current RepoBrain TopoCore backend status.` | `v5` | `false` | requested/resolved backend, no private checkout/install, safety markers | PASS | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26083784946` | gate set to `0`; checkout/install/diagnostic all `skipped`; audit recorded `requested_backend=v5`, `resolved_backend=v5`, `fallback_used=false` |
| OBS-10 | mixed | dependency fallback simulation | optional only if safe and non-disruptive | `v5` fallback | `true` if simulated | clear fallback reason without instability | NOT_RUN | `n/a` | optional scenario intentionally not run to avoid disruptive dependency changes |

If no safe PR exists:

- PR scenarios must be marked `NOT_RUN_MISSING_SAFE_PR`
- they must not be treated as passed

## 4. Evidence Fields

Required evidence fields for every recorded run:

- run URL
- workflow conclusion
- event type
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
- diagnostic status
- private checkout and install status
- `decide_raw` used
- patch application
- commit, branch, or PR creation
- user-visible output notes

## 5. Success Criteria

Observation passes only if all of the following remain true:

- gate=`1` `issue_comment` runs resolve to v6 when the private dependency is available
- `workflow_dispatch` v6 `private_checkout` sanity rerun resolves to v6
- gate=`0` kill switch resolves to v5
- no `decide_raw`
- no patch application
- no file modification
- no commit, branch, or PR creation
- no unsafe approval, security, or safe-to-merge claims
- no secret or private URL exposure
- no repeated workflow instability

## 6. Failure Criteria

Observation fails if any of the following occur:

- gate=`1` repeatedly resolves to v5 without a clear fallback reason
- private checkout or install fails with a valid secret
- diagnostic fails repeatedly
- backend evidence is missing
- `decide_raw` appears
- patch or autofix side effect appears
- commit, branch, or PR creation appears
- unsafe claim appears
- secret or private URL appears
- workflow instability repeats

## 7. Decision Section

Decision options:

- `PROMOTE_V6_LAB_DEFAULT`
  - leave `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
  - treat v5 as fallback only
- `RETURN_TO_V5_SAFE`
  - set `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
  - document blocker
- `PARTIAL_PASS`
  - keep gate decision conservative
  - define exact missing evidence

Initial placeholder:

- final decision: `PARTIAL_PASS`
- final variable state: `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- v5 status after observation: temporary fallback remains active safe default
- next step: fix the gate=`1` PR-path and issue review/fix blockers, then rerun the observation matrix

Final decision detail:

- `PROMOTE_V6_LAB_DEFAULT`: rejected for Sprint 57
- `RETURN_TO_V5_SAFE`: not required as a panic rollback because several v6 paths worked
- `PARTIAL_PASS`: accepted

Reason:

- gate=`1` issue `ask` and explain-style observation succeeded on v6
- `workflow_dispatch` sanity rerun succeeded on v6
- gate=`0` kill switch behaved correctly and restored v5-side behavior
- but gate=`1` PR and non-PR review/fix observation did not provide stable, consistent v6 backend evidence
- because of that inconsistency, leaving the repository variable at `1` would be premature

Operational outcome:

- final repository variable left at `0`
- v5 remains temporary fallback and active safe default
- v5 deprecation candidate should not be proposed next yet

Sprint 58 follow-up:

- `docs/architecture/TOPOCORE_V6_PR_PATH_AND_SCOPED_COMMAND_OBSERVATION_FIX.md`
- `docs/architecture/TOPOCORE_V6_PR_OUTPUT_BACKEND_EVIDENCE_FIX.md`
- Sprint 58 targets the exact Sprint 57 blockers:
  - PR-path TopoCore backend evidence under gate=`1`
  - explicit scoped diagnostics for non-PR `review` and `fix`

Sprint 59 follow-up:

- PR paths were functional after Sprint 58, but visible PR comment output still needed explicit TopoCore backend evidence rendering for promotion
