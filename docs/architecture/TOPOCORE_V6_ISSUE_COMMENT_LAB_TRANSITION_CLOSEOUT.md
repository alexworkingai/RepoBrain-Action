# TopoCore v6 Issue Comment Lab Transition Closeout

## 1. Purpose

Sprint 54 closes the controlled `issue_comment` TopoCore v6 lab transition.
Sprint 53 operational checks proved both gate-enabled v6 behavior and gate-disabled v5 behavior.
The repository variable is currently intentionally left at `0`.
This sprint does not change runtime behavior.

## 2. Current Operational State

Current repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`

Operational meaning:

- `issue_comment` stays v5-side by default
- private TopoCore v6 checkout and install do not run for `issue_comment`
- v6 lab mode is available but disabled

Enabling v6 lab requires:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

## 3. Evidence: Gate Enabled

`RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Observed:

- `TKY mode requested: local`
- `TKY mode used: local`
- `TKYA mode: topocore_v6`
- `TopoCore backend mode: auto`
- `TopoCore backend requested: auto`
- `TopoCore backend resolved: v6`
- `TopoCore fallback used: no`
- `TopoCore fallback reason: none`
- TopoCore v6 external decision influenced route and rationale:
  - `route: REVIEW`
  - `status: needs_review`
  - `action: investigate`
  - `message_code: DEEP_REVIEW_RECOMMENDED`

Clarification:

- legacy `TKYA backend: v5` may still appear as an anchor in some output paths
- the authoritative v6 proof is:
  - `TKYA mode: topocore_v6`
  - `TopoCore backend resolved: v6`

## 4. Evidence: Gate Disabled / Kill Switch

`RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`

Observed:

- `TKY mode requested: auto`
- `TKY mode used: baseline`
- `TKYA backend: v5`
- `TKYA mode: baseline-policy`
- `TopoCore backend mode: v5`
- `TopoCore backend requested: v5`
- `TopoCore backend resolved: v5`

Clarification:

- the kill switch works
- v5-side behavior remains available
- private checkout and install should not run in this state

## 5. Safety Boundaries Preserved

- no v5 removal
- no production or Marketplace switch
- no default CI private dependency
- no `decide_raw`
- no patch application
- no file modification
- no commit creation
- no branch creation
- no PR creation
- no safe-to-merge claim
- no security approval verdict
- no PR approval or rejection claim
- no `repobrain-community` change

## 6. Maintained Operating Model

Default safe operating mode:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- `issue_comment` remains v5-side
- `workflow_dispatch` v6 `private_checkout` remains available for manual validation

Controlled v6 lab mode:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
- `issue_comment` uses `tky_mode=local` and `topocore_backend=auto`
- private checkout and install can run
- TopoCore v6 can resolve
- v5 fallback remains available because strict v6 is not default

Emergency disable:

- set `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- or delete the repository variable

## 7. Remaining Known Limitations

- this is still lab mode, not a production or Marketplace release
- private TopoCore v6 dependency is still required for `issue_comment` v6 lab mode
- default operational state is currently disabled with gate `0`
- v5 still exists and remains fallback
- fix-lite remains decision and governance only
- patch application remains out of scope
- non-PR issue LLM policy still blocks LLM, as shown in outputs
- verification was `NOT_RUN` for the operational checks
- evidence came from a safe `issue_comment ask` command, not broad production load

## 8. Next Decision Options

Option A - Maintain current safe mode

- keep `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- use `workflow_dispatch` or temporary gate=`1` checks when needed
- no immediate sprint required

Option B - Operate v6 lab mode

- set `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
- keep monitoring logs and diagnostics
- keep the kill switch documented
- still no v5 removal

Option C - Start v5 deprecation planning

- docs and test planning only first
- no deletion until separate approval
- must define rollback and coverage gates

## 9. Recommended Next Step

Given the repository variable is intentionally left at `0`, the recommended next step is:

- no immediate runtime sprint
- keep the current safe gate-disabled state
- if development continues, the next sprint should be docs and test planning only:
  - `Sprint 55 - v5 Deprecation Readiness Assessment`
- do not start v5 removal yet

See also:

- `docs/architecture/TOPOCORE_V6_V5_DEPRECATION_READINESS_ASSESSMENT.md`

## 10. Non-Goals

- no runtime behavior change
- no workflow or `action.yml` change
- no repository variable change
- no v5 removal
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change
