# TopoCore v6 Real Adapter Implementation

## 1. Purpose

Sprint 42 implements the real TopoCore v6 adapter.

Current truth:

- Sprint 42 uses the public v6 contract confirmed in Sprint 41
- Sprint 42 does not switch GitHub runtime to v6 yet
- Sprint 42 does not remove v5
- Sprint 42 does not change PR comments or checks
- Sprint 42 prepares Sprint 43 for backend switching

## 2. Current Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 42:
  - `dec5728 Add real TopoCore v6 contract probe`
- Sprint 41 status:
  - compatibility is `compatible_with_adapter_changes`
  - real local contract probe passed
  - no TopoCore team escalation was needed

## 3. Real Public API Used

Sprint 42 adapter implementation uses only the public `topocore_v6` surface:

- `topocore_v6`
- `create_topocore`
- `EngineRequest`
- `EngineQuery`
- `EngineCandidate`
- `decide_external`
- `ExternalDecisionView`

Current rule:

- `decide_raw` remains forbidden

## 4. Adapter Mapping

RepoBrain to real v6 mapping:

- `task_type` -> `EngineRequest.task_type`
- `query` -> `EngineQuery.text`
- candidate refs -> supported `EngineCandidate` fields only
- summaries -> `EngineRequest.policy` summary-family keys
- limits -> `EngineRequest.limits`
- safe decision -> `ExternalDecisionView` safe fields

## 5. Safe External Decision Extraction

Extracted fields:

- `status`
- `action`
- `reference_hash`
- `selected_count`
- `blocked`
- `confidence_band`
- `message_code`

Current rule:

- no raw v6 result object is exposed

## 6. Runtime Boundary

Current runtime boundary:

- the adapter can now build and call real v6 in explicit local, manual, or controlled test paths
- GitHub runtime is not switched
- v5/TKYA remains the active runtime
- backend selection is left for Sprint 43

## 7. Sprint 43 Target

Sprint 43 target:

- Sprint 43 - Runtime Backend Switch: v5/v6 Selectable

Expected scope:

- add selectable backend config
- keep v5 fallback
- enable v6 in lab or runtime only
- start with low-risk commands
- no fix migration yet unless explicitly approved

## 8. Non-Goals

Current non-goals:

- no GitHub runtime backend switch
- no v5 removal
- no workflow change
- no `action.yml` change
- no default CI private dependency
- no `decide_raw`
- no patch or fix behavior change
- no PR, check, or comment behavior change
- no `repobrain-community` change
