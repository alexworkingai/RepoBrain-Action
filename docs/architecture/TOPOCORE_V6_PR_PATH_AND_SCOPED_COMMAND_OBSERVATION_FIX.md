# TopoCore v6 PR Path and Scoped Command Observation Fix

## 1. Purpose

Sprint 58 fixes the blockers found in Sprint 57 observation.
The goal is stable v6 backend evidence for PR paths and clear scoped behavior for non-PR `review` and `fix` commands.
This sprint does not remove v5.
This sprint does not enable patch application.

## 2. Sprint 57 Baseline

Latest accepted `main` before Sprint 58:

- `270b253 Record v6 observation window results`

Sprint 57 decision:

- `PARTIAL_PASS`

Passed observation paths:

- issue `ask` on v6
- issue explain-style `ask` on v6
- `workflow_dispatch` v6 sanity
- gate=`0` kill switch

Failed or incomplete observation paths:

- PR `ask` / `review` / `verify` evidence
- non-PR `review` / `fix` observation usefulness

## 3. Root Cause

Sprint 58 root cause is split across three narrow seams.

PR ask and review evidence problem:

- live Sprint 57 runs showed the action step warning `Unexpected input(s) 'topocore_backend'`
- the runtime still had legacy `RB_TKYA_BACKEND=v5`
- when `RB_TOPOCORE_BACKEND` was not reliably present at runtime, backend resolution fell back to the legacy v5-side selector
- that produced PR audit payloads such as `tky_engine=topocore_v5` and `tkya_backend=v5` without explicit TopoCore requested or resolved fields

PR verify evidence problem:

- verify uses the GitHub checks and workflow-report path rather than the retrieval-backed local TopoCore provider path
- Sprint 57 therefore produced a valid verification comment, but not a stable TopoCore backend evidence surface for observation

Non-PR review and fix scope problem:

- non-PR `review` and `fix` returned PR-only guidance before emitting scoped backend diagnostics
- the command result was safe, but not useful for observation because it did not expose whether the scope was intentionally unsupported or whether any backend evidence was applicable

## 4. Fix

Sprint 58 applies three targeted fixes.

PR backend evidence propagation:

- the workflow action step now exports `RB_TOPOCORE_BACKEND` explicitly at the workflow environment boundary
- `action.yml` now prefers workflow-provided `RB_TOPOCORE_BACKEND` before falling back to the local action input default
- this keeps gate=`1` PR paths from silently collapsing onto legacy `RB_TKYA_BACKEND=v5` when the action-input seam is unreliable in live runs

Scoped command diagnostics:

- non-PR `review` now returns an explicit scoped message for `unsupported_issue_context`
- non-PR `fix` now returns an explicit scoped message for `unsupported_issue_context`
- these scoped results include safe backend and scope diagnostics instead of ambiguous PR-only guidance
- fix-lite scoped results also emit `patch_authorized=false` and `patch_applied=false`

Verify observation surface:

- PR `verify` now emits an explicit scoped observation block
- verify still reports PR checks directly, but it now adds safe backend-diagnostic fields and a `scope_status=verify_report_only` marker
- this makes the observation result explicit instead of leaving backend evidence absent

## 5. Evidence Fields

Sprint 58 standardizes or preserves the following observation fields:

- `requested_backend`
- `resolved_backend`
- `backend_mode`
- `fallback_used`
- `fallback_reason`
- `scope_status` when the command is intentionally scoped or report-only
- `patch_authorized` for fix-lite scoped outcomes
- `patch_applied` for fix-lite scoped outcomes

Interpretation:

- explicit TopoCore backend fields are authoritative for v6 observation
- legacy `TKYA backend` anchors may remain in audit payloads for compatibility
- `scope_status` distinguishes a deliberate scoped result from an accidental silent fallback

## 6. Safety Boundaries

Sprint 58 preserves these safety boundaries:

- no `decide_raw`
- no patch application
- no file modifications by RepoBrain behavior
- no commit, branch, or PR creation by RepoBrain behavior
- no `safe-to-merge` claim
- no security approval claim
- no PR approval or rejection claim
- no `repobrain-community` change

## 7. Post-Merge Observation Subset

Required rerun subset after the fix is available on `main`:

- `OBS-03` issue review-like
- `OBS-04` PR ask
- `OBS-05` PR review
- `OBS-06` PR verify
- `OBS-07` issue fix-lite governance
- `OBS-08` `workflow_dispatch` sanity
- `OBS-09` gate=`0` kill switch

Interpretation rules:

- PR ask and PR review should emit explicit TopoCore backend requested and resolved fields
- PR verify may pass either with explicit backend evidence or with the explicit scoped result defined in Sprint 58
- non-PR review and non-PR fix should no longer be counted as ambiguous failures when they intentionally return scoped unsupported diagnostics

## 8. Promotion Decision Rule

Decision rule after the Sprint 58 rerun subset:

- if the fixed subset passes and no safety failures occur, the gate may be left at `1` as the active v6 lab default
- if any major blocker remains, return the gate to `0`
- v5 is still not removed in Sprint 58

## 9. Non-Goals

- no v5 removal
- no v5 code deprecation yet unless separately approved
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change
