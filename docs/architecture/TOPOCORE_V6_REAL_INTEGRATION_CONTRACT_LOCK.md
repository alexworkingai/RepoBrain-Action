# TopoCore v6 Real Integration Contract Lock

## 1. Purpose

Sprint 41 starts the direct v5 to v6 replacement track.

Current truth:

- Sprint 41 uses the real available TopoCore v6 repository and API
- Sprint 41 locks the integration contract needed for Sprint 42
- Sprint 41 does not switch RepoBrain runtime to v6
- Sprint 41 does not replace v5 yet
- v5/TKYA remains the current active runtime until a later backend-switch sprint
- TopoCore v6 is no longer treated as theoretical

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 41:
  - `e96744c Docs: add TopoCore v6 manual evidence checkpoint`
- Sprint 40 closed Phase 7 as stabilization baseline
- previous NO-GO was for premature advisory experiment implementation
- new decision:
  - direct lab migration to v6 is now the intended development track
- current runtime behavior remains unchanged at Sprint 41 start

## 3. Reframed Strategy

Old strategy:

- advisory, shadow, and no-go preparation
- avoid runtime changes

New strategy:

- direct v6 replacement track
- use v6 as target backend
- keep v5 fallback during transition
- move in controlled implementation sprints
- stop creating extra advisory-only checkpoints unless a real blocker appears

## 4. Real TopoCore v6 Repository Discovery

Discovery summary:

- RepoBrain-Action repository was inspected from its current git root
- a local sibling repository named `topocore` was found in the same project workspace
- TopoCore v6 package metadata was confirmed through its `pyproject.toml`
- public API and contract files were inspected under the package `topocore_v6`
- no absolute local paths are recorded here
- no private URLs or secrets are recorded here

Inspected public modules:

- `topocore_v6.__init__`
- `topocore_v6.public.api`
- `topocore_v6.public.disclosure`
- `topocore_v6.public.models`
- `topocore_v6.contracts.engine`
- `topocore_v6.contracts.summaries`

| API surface | Actual symbol/module found | Status | Notes |
|---|---|---|---|
| factory or constructor | `topocore_v6.create_topocore` and `topocore_v6.public.api.create_topocore` | Found | Stable public factory exists. |
| request object | `topocore_v6.EngineRequest` and `topocore_v6.contracts.engine.EngineRequest` | Found | Publicly exported at top level. |
| query object | `topocore_v6.EngineQuery` and `topocore_v6.contracts.engine.EngineQuery` | Found | Publicly exported at top level. |
| candidate object | `topocore_v6.EngineCandidate` and `topocore_v6.contracts.engine.EngineCandidate` | Found | Publicly exported at top level. |
| decision method | `TopoCoreV6.decide` | Found | Public hash-only product result exists. |
| external or product-safe decision method | `TopoCoreV6.decide_external` | Found | External safe view exists and was probed locally. |
| external decision or result type | `ExternalDecisionView` and `TopoCoreV6Result` | Found | Both are public, with different disclosure levels. |
| typed summary input | `EngineRequest.policy` consumed by `topocore_v6.app_shell.envelope_builder.RequestEnvelopeBuilder` | Found | Real keys differ from current RepoBrain preview keys. |
| policy or governance input | `EngineRequest.policy` with summary-family keys | Found | Governance enters through policy payload, not separate facade args. |
| error type | No dedicated public facade exception export found | Partial | Public integration should sanitize generic import or runtime exceptions. |
| version or capability metadata | `topocore_v6.__version__`, `version_info`, and `TopoCoreV6.health()` | Found | Health reports version, release stage, and API stability. |

## 5. Public API Contract

Real v6 contract RepoBrain should use:

- allowed import path:
  - `topocore_v6`
- allowed public symbols:
  - `create_topocore`
  - `TopoCoreV6`
  - `EngineRequest`
  - `EngineQuery`
  - `EngineCandidate`
  - `TopoCoreV6Result`
  - `ExternalDecisionView`
- factory creation:
  - `facade = create_topocore()`
- request construction:
  - `EngineRequest(task_type=..., query=EngineQuery(...), candidates=[...], limits={...}, policy={...})`
- candidate construction:
  - `EngineCandidate(chunk_id=..., score_local=..., signature=..., file_path=..., line_start=..., line_end=...)`
- typed summary payload expectations:
  - `policy["evidence_summary"]`
  - `policy["bit_matrix_summary"]`
  - `policy["verification_summary"]`
  - `policy["project_audit_summary"]`
  - `policy["risk_summary"]`
  - `policy["scenario_summary"]`
  - optional `policy["artifacts"]`
- decision call to use:
  - `facade.decide(request)`
- product-safe output call to use:
  - `facade.decide_external(request)`
- error handling expectations:
  - import and runtime exceptions must be treated as sanitized integration failures
  - no public facade-specific error contract is currently exported
- what must not be used:
  - internal v6 modules as stable integration dependencies
  - raw traces or internal workflow result fields for RepoBrain output shaping
  - `decide_raw`

Current rule:

- RepoBrain must use only TopoCore v6 public facade and public contracts
- RepoBrain must not depend on internal v6 modules
- `decide_raw` remains forbidden

## 6. Mapping from Current RepoBrain Adapter to Real v6

| RepoBrain current concept | Current placeholder or preview shape | Real TopoCore v6 target concept | Adapter action needed | Sprint 42 priority |
|---|---|---|---|---|
| `task_type` | top-level `task_type` string | `EngineRequest.task_type` | Direct mapping | High |
| `query` | plain `query` string | `EngineQuery(text=...)` | Direct mapping | High |
| candidate refs | `chunk_id`, `score_local`, free-form `metadata` | `EngineCandidate(chunk_id, score_local, signature, file_path, line_start, line_end)` | Map only supported public fields; stop using free-form metadata | High |
| summary bundle | broad free-form summary bundle | `EngineRequest.policy` summary families | Reshape into exact policy families | High |
| evidence summary | `evidence_summary` free-form mapping | `policy["evidence_summary"]` with numeric counters and hashes | Normalize field names and defaults | High |
| unknowns | `unknowns_summary` | likely `evidence_summary.unknown_count` and possibly `scenario_summary` | Convert from narrative shape to count-and-hash shape | High |
| risk hints | `risk_items` list | `policy["risk_summary"]` | Aggregate into severity/count fields | High |
| review draft | `review_draft_summary` | no direct public contract field found | Keep on RepoBrain side or map only safe derived signals | Medium |
| fix governance summary | `fix_draft_summary` | no dedicated public contract field found; governance inferred through policy and request context | Derive safe policy cues or keep local until contract expands | High |
| policy payload | current policy includes non-contract keys | `policy` with exact summary keys expected by envelope builder | Replace preview-only keys with real keys | High |
| safe external decision | current advisory snapshot expects `safe_reason_code`, `needs_more_information_reason`, `blocked_reason_code`, `confidence_hint` | `ExternalDecisionView(status, action, reference_hash, selected_count, blocked, confidence_band, message_code, hash_only)` | Update snapshot extractor to real fields | High |
| blocked, needs more information, proceed states | RepoBrain-side synthetic statuses | `ExternalDecisionView.status` and `action` | Map directly from external view | High |
| confidence hint | `confidence_hint` | `confidence_band` | Rename and adapt | High |
| failure category | RepoBrain-local categories | RepoBrain-local categories remain local | Preserve sanitized local taxonomy | Medium |

## 7. Compatibility Result

Compatibility status:

- Compatible with adapter changes

Exact changes needed:

- replace free-form candidate metadata with real `EngineCandidate` public fields
- construct `EngineQuery(text=...)` without the current unsupported `task_type` argument
- convert current preview policy keys into the real summary-family keys used by TopoCore v6
- adapt RepoBrain safe snapshot extraction to `ExternalDecisionView` fields:
  - `status`
  - `action`
  - `reference_hash`
  - `selected_count`
  - `blocked`
  - `confidence_band`
  - `message_code`
- stop assuming `safe_reason_code`, `blocked_reason_code`, and `needs_more_information_reason` are provided by v6 public output
- treat public facade exceptions as sanitized integration failures

Current conclusion:

- current adapter skeleton cannot be used unchanged
- no public API blocker was found
- the required work is adapter reshaping, not TopoCore public-API invention

## 8. Sprint 42 Implementation Target

Sprint 42 target:

- Sprint 42 - Real TopoCore v6 Adapter Implementation

Expected goal:

- convert `RepoBrainTopoCoreV6Adapter` from preview-only to real v6 request adapter
- call the public v6 facade in local, manual, or controlled test path
- return a RepoBrain-safe result object
- keep v5 runtime fallback
- no GitHub runtime switch yet unless explicitly approved

## 9. TopoCore Team Escalation Criteria

TopoCore team is needed only if:

- public API is unclear
- public facade is missing required fields
- typed summary contract is incompatible
- external decision view does not provide enough safe output
- import or package structure is unstable
- behavior contradicts documented v6 contract

Current assessment:

- RepoBrain-Action can proceed without blocking on TopoCore team now

See also:

- `docs/architecture/TOPOCORE_V6_REAL_ADAPTER_IMPLEMENTATION.md`

## 10. Non-Goals for Sprint 41

Current non-goals:

- no runtime backend switch
- no v5 removal
- no GitHub workflow changes
- no `action.yml` changes
- no `topocore_v6` dependency in `pyproject` or `requirements`
- no default CI private dependency
- no GitHub runtime v6 call
- no `decide_raw`
- no patch or fix behavior change
- no PR comment or check behavior change
- no `repobrain-community` change

## 11. Acceptance Criteria

Sprint 41 is complete only if:

- the real TopoCore v6 public API was inspected
- the integration contract document exists
- actual API symbols are recorded without leaking private paths or secrets
- mapping from RepoBrain adapter to real v6 contract exists
- compatibility status is explicit
- Sprint 42 implementation target is clear
- local contract probe exists
- contract probe is disabled or skipped safely by default
- tests for probe behavior exist and pass
- default CI still does not require `topocore_v6`
- runtime behavior remains unchanged
