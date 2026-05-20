# TopoCore v6 v5 Deprecation Candidate

## 1. Purpose

Sprint 61 marks TopoCore v5 and TKYA as a deprecation candidate.
This follows Sprint 60 `PROMOTE_V6_LAB_DEFAULT`.
v6 `issue_comment` lab mode is now the active lab default.
v5 remains available only as fallback and safety net.
This sprint does not remove v5 code.
This sprint does not change runtime behavior.

## 2. Current Operating State

Latest accepted `main` before Sprint 61:

- `e9db63e Record fresh PR v6 observation results`

Repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Current operating state:

- active lab default: `v6`
- fallback: `v5`
- kill switch: set `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- `workflow_dispatch` v6 `private_checkout`: still available
- v5: fallback-only and deprecation candidate

## 3. Evidence Basis

Sprint 61 relies on Sprint 60 promotion evidence:

- fresh PR fixture: `#112`
- PR ask:
  - `requested=auto`
  - `resolved=v6`
  - `fallback=no`
- PR review:
  - `requested=auto`
  - `resolved=v6`
  - `fallback=no`
- PR verify:
  - `verify_report_only` scoped evidence
  - visible backend evidence present
- `workflow_dispatch` sanity:
  - `requested=v6`
  - `resolved=v6`
  - `fallback=false`
- gate=`0` kill switch:
  - `requested=v5`
  - `resolved=v5`
  - private checkout and install skipped

Safety basis:

- no `decide_raw`
- no patch application
- no file modification by RepoBrain
- no commit, branch, or PR creation by RepoBrain
- no unsafe approval or security claims
- no secret or private URL exposure

## 4. v5 Status

- v5 is no longer the target runtime
- v5 remains as a temporary fallback
- v5 remains available for the emergency gate=`0` kill switch
- v5 remains available for dependency-failure fallback
- v5 is now a deprecation candidate
- v5 removal is not approved

## 5. Deprecation Candidate Meaning

Deprecation candidate means:

- docs and policy status only
- no runtime behavior change
- no file deletion
- no fallback disablement
- no workflow or `action.yml` contract break
- no Marketplace or production claim
- explicit next step is code-level deprecation preparation

It does not mean:

- v5 files are removed
- fallback is disabled
- all users are on production v6
- public GitHub contract has changed

## 6. What Must Stay Working

- gate=`1` v6 `issue_comment`
- gate=`0` v5 kill switch
- `workflow_dispatch` v6 `private_checkout`
- fallback when the v6 dependency is unavailable
- no `decide_raw`
- no patch or autofix
- no commit, branch, or PR creation
- safe diagnostics
- visible backend evidence

## 7. Code-Level Deprecation Entry Gates

Before code-level deprecation can be introduced:

- v6 active lab default remains stable
- gate=`0` kill switch remains green
- `workflow_dispatch` v6 sanity remains green
- PR ask and review evidence remain visible and v6-backed
- PR verify scoped or report-only behavior remains explicit
- issue-only scoped unsupported behavior remains explicit
- no patch or autofix behavior appears
- no user-visible regression appears in normal comments
- explicit approval exists

## 8. Removal Entry Gates

Before v5 removal can be proposed:

- v5 has been code-level deprecated for at least one checkpoint
- a v5-off test plan exists
- all v5-specific tests are classified:
  - migrate
  - keep fallback
  - remove
- a fallback replacement or rollback path exists
- workflow and action defaults are intentionally updated
- private dependency stability is accepted
- public docs are updated
- explicit approval exists

## 9. Fast Next Step

Recommended next sprint:

- `Sprint 62 - Prepare Code-Level v5 Deprecation Flags and Tests`

Recommended scope:

- no deletion
- add deprecation markers or warnings in docs and tests if safe
- classify v5 tests
- define v5-off simulation
- preserve the kill switch
- keep patch and autofix out of scope

Follow-up:

- `docs/architecture/TOPOCORE_V6_CODE_LEVEL_V5_DEPRECATION_PREP.md`
- `docs/architecture/TOPOCORE_V6_OPT_IN_V5_OFF_SIMULATION.md`
- v5 remains fallback-only and is still not removed in Sprint 62.
- v5-off simulation now exists, but it is opt-in and does not change the default fallback posture.
- `docs/architecture/TOPOCORE_V6_AUTHORITATIVE_DISABLE_V5_DEFAULT.md`
- Sprint 64 changes the default posture:
  - v5 is now disabled by default
  - deprecated v5 is emergency opt-in only through `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1`
  - v5 is still not physically removed
- Sprint 65 advances the candidate state to runtime removal:
  - deprecated v5 runtime execution is removed
  - legacy `lite` execution is removed
  - old env values are now safe unsupported diagnostics
  - see `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`

## 10. Non-Goals

- no runtime behavior change
- no workflow or `action.yml` change
- no repository variable change
- no v5 removal
- no v5 file deletion
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change
