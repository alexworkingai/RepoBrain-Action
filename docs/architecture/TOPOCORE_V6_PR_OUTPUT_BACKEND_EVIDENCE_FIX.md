# TopoCore v6 PR Output Backend Evidence Fix

## 1. Purpose

Sprint 59 fixes the remaining Sprint 58 post-merge PR output evidence blocker.
PR `ask`, `review`, and `verify` were functionally useful after Sprint 58, but they did not expose sufficient visible TopoCore backend evidence for promotion.
This sprint makes PR output and audit evidence explicit.
This sprint does not remove v5.
This sprint does not enable patch application.

## 2. Post-Sprint 58 Baseline

Latest accepted `main` before Sprint 59:

- `93e08e8 Fix v6 PR path backend evidence`

Post-merge live subset result:

- `PARTIAL_PASS`

Passed:

- `workflow_dispatch` sanity
- issue-only scoped `review` / `fix` behavior
- gate=`0` kill switch

Remaining blocker:

- PR `ask` / `review` / `verify` output did not expose stable backend evidence visibly enough for promotion

## 3. Root Cause

Sprint 59 root cause is primarily an output-layer visibility gap, with a smaller normalization gap.

Output template omission:

- PR `ask` and PR `review` already carried backend evidence into the audit summary
- but the relevant TopoCore fields were rendered only inside the collapsed Evidence and diagnostics `<details>` block and the audit-anchor block inside it
- that was not strong enough for live promotion evidence because the visible comment body did not surface requested or resolved backend state directly

Audit field normalization gap:

- TopoCore evidence can arrive under multiple keys such as `requested_backend`, `resolved_backend`, `backend_mode`, `fallback_used`, and `fallback_reason`
- some paths also still retain legacy TKYA or engine markers for compatibility
- Sprint 58 preserved the data, but did not normalize it into one visible section shared by PR `ask`, PR `review`, PR `verify`, and scoped command output

Verify report-only path omission:

- PR `verify` already emitted a scoped diagnostics block after Sprint 58
- but Sprint 59 aligns it with the same explicit runtime backend evidence section used elsewhere so the report-only path is visually consistent with PR `ask` and PR `review`

## 4. Fix

Sprint 59 applies a targeted rendering fix.

Backend evidence normalization:

- `repobrain/output_md.py` now normalizes backend evidence keys before rendering
- the normalization layer safely resolves:
  - `requested_backend` / `topocore_backend_requested`
  - `resolved_backend` / `topocore_backend_resolved`
  - `backend_mode` / `topocore_backend_mode`
  - `fallback_used` / `topocore_fallback_used`
  - `fallback_reason` / `topocore_fallback_reason`
  - `tkya_mode` or the legacy `tky_engine` label fallback
- missing values render safely as `n/a`
- scoped or report-only values render safely as `not_applicable` or the explicit scope code already present in the audit summary

Backend evidence rendering:

- PR `ask` output now includes a visible `Runtime backend evidence` section near the top-level comment body
- PR `review` output now includes the same visible section near the top-level comment body
- PR `verify` output inherits the same visible section through the shared scoped-command renderer
- scoped unsupported output also uses the same shared evidence renderer, preserving explicit scope and patch-safety markers

Missing-field handling:

- the renderer does not invent v6 values
- unknown or absent values stay `n/a`
- report-only or unsupported scopes keep explicit `scope_status` and `not_applicable` style values when backend resolution is not meaningful

## 5. Evidence Fields

Sprint 59 explicitly renders the following evidence fields:

- `TKY mode requested`
- `TKY mode used`
- `TKYA mode`
- `TopoCore backend requested`
- `TopoCore backend resolved`
- `TopoCore backend mode`
- `TopoCore fallback used`
- `TopoCore fallback reason`
- `Scope status` when applicable
- `Patch authorized` for scoped fix-lite outcomes
- `Patch applied` for scoped fix-lite outcomes

## 6. Safety Boundaries

Sprint 59 preserves these safety boundaries:

- no `decide_raw`
- no patch application
- no file modifications by RepoBrain behavior
- no commit, branch, or PR creation by RepoBrain behavior
- no `safe-to-merge` claim
- no security approval claim
- no PR approval or rejection claim
- no `repobrain-community` change

## 7. Post-Merge Live Subset Required

Because `issue_comment` executes `main`, live verification happens after merge.

Required post-merge subset:

- gate=`1` PR `ask`
- gate=`1` PR `review`
- gate=`1` PR `verify`
- `workflow_dispatch` sanity
- gate=`0` kill switch

Interpretation:

- promotion requires visible PR output evidence, not only functional PR answers
- PR `verify` may use `scope_status=verify_report_only`, but it still needs explicit backend evidence or explicit not-applicable diagnostics

## 8. Promotion Decision Rule

- if PR output now shows `resolved_backend=v6` under gate=`1` and safety criteria pass, `PROMOTE_V6_LAB_DEFAULT` may be selected
- if PR output is still missing evidence, keep gate=`0` and fix the exact remaining output blocker
- v5 is still not removed in Sprint 59

## 9. Non-Goals

- no v5 removal
- no v5 code deprecation yet unless separately approved
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change
