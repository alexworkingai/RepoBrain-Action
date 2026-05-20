# TopoCore v5 to v6 Controlled Migration Blueprint

## 1. Purpose

This document defines the controlled migration plan from the current embedded TopoCore v5/TKYA runtime to a future TopoCore v6 public-facade integration.

Current truth:

- current runtime is embedded TopoCore v5/TKYA
- the future target is TopoCore v6 public-facade integration
- TopoCore v6 is not wired into RepoBrain-Action runtime today
- Sprint 16 is docs-only and does not implement the migration

This blueprint exists so later implementation work can move deliberately without breaking the active RepoBrain runtime, the accepted fix-path safety baseline, or the current repository-boundary split.

See also:

- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_ARTIFACT_FORMAT_AND_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_DECISION_DIFF_ARTIFACT_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_PHASE_1_2_CLOSEOUT_AND_PHASE_3_SCOPE.md`

## 2. Current Runtime Baseline

Detailed current-state evidence is documented in:

- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`

That document remains the authoritative detailed baseline. This section summarizes only the parts needed for the migration plan.

Current baseline summary:

- primary GitHub runtime flow is:
  - GitHub event
  - `.github/workflows/repobrain.yml`
  - `action.yml`
  - `scripts/run_github.py`
  - `repobrain/github_flow.py`
- primary trigger model remains:
  - `issue_comment`
  - `workflow_dispatch`
- command routing remains centered in:
  - `repobrain.commands.parse_command(...)`
  - `repobrain.github_flow.run_github_flow(...)`
- current embedded v5/TKYA path remains:
  - `repobrain/tky_local.py`
  - `repobrain/tky_engine.py`
  - `repobrain/tkya/engine.py`
  - `repobrain::tkya::vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`
- current active backend pin for GitHub-mode runtime remains:
  - `RB_TKYA_BACKEND=v5`
- current LLM provider path in live GitHub runtime remains GitHub Models through:
  - `repobrain.llm.github_models.GitHubModelsClient`
  - `repobrain.llm.github_models_embeddings.GitHubModelsEmbeddingsClient`
- current patch/fix safety stack remains:
  - `repobrain/fix/patch_extract.py`
  - `repobrain/fix/patch_guard.py`
  - `repobrain/patch_targeting.py`
  - `repobrain/patch_validator.py`
  - `repobrain/patch_governance.py`
- current boundary split remains:
  - `RepoBrain-Action` owns the primary/private GitHub runtime, tests, docs, and runtime-adjacent safety contracts
  - `repobrain-community` owns the public external GitHub foundation host and canonical install template
  - `elen-mcp-prod_v2` remains validation-only

## 3. Migration Problem Statement

This migration is not a simple adapter insertion.

Why:

- RepoBrain already has a working embedded deterministic v5/TKYA core.
- v5 contracts are still active and guarded by tests.
- TopoCore v6 has a different intended role: an independent foundation decision library rather than an embedded RepoBrain-specific vendor file.
- RepoBrain currently depends on active v5/TKYA contract shapes such as:
  - `EngineDecision`
  - `TKYResult`
  - `compression_stats`
  - hash-only trace behavior
  - current TKYA evidence-pack behavior

So the migration must preserve current behavior first, then add a gradual v6 path around it.

The problem is therefore not:

- “replace v5 with v6 in one step”

The problem is:

- “create a safe product-level bridge from RepoBrain’s current v5/TKYA runtime contract to TopoCore v6’s public facade without breaking current behavior”

## 4. v5 -> v6 Conceptual Mapping

| Current v5/TKYA side | Future v6 side | Mapping category | Notes |
|---|---|---|---|
| `EngineRequest` | `EngineRequest` | direct candidate | Same high-level role exists, but field alignment still needs verification. |
| `EngineDecision` | `decide()` result | adapter-required | RepoBrain currently expects v5-style fields that should not leak directly from v6 without shaping. |
| `TKYResult` | RepoBrain-mapped adapter output | product-mapping-required | `TKYResult` is a RepoBrain contract, not a likely direct TopoCore v6 export. |
| `route` | typed decision route / adapter policy output | adapter-required | Current route semantics are RepoBrain-visible and need explicit preservation or translation. |
| `selected_chunk_ids` | selected evidence references / adapter summary | adapter-required | v6 may carry equivalent selection intent but not the same direct field shape. |
| `compression_stats` | typed summaries / diagnostics | not portable / deprecated | Current v5 compression-stat bag is too RepoBrain-v5-specific to treat as a direct v6 contract. |
| hash-only trace | hash-only / safe external boundary | direct candidate | The safety goal remains portable even if the concrete schema changes. |
| verification fields | policy payloads / typed summaries / RepoBrain validation layer | product-mapping-required | Verification semantics belong partly to RepoBrain orchestration, not only to TopoCore. |
| `llm_intent` | RepoBrain-side LLM summary metadata | not portable / deprecated | LLM intent belongs in RepoBrain, not in TopoCore v6. |
| `llm_decision_reason_short` | RepoBrain-side decision/adapter metadata | not portable / deprecated | Current field is part of RepoBrain orchestration, not a likely v6 foundation primitive. |
| `llm_decision_reason_code` | RepoBrain-side decision/adapter metadata | not portable / deprecated | Same reasoning as above. |
| fallback lite backend | optional RepoBrain compatibility fallback | open question | Whether fallback remains at RepoBrain layer or changes after v6 integration needs an explicit product choice. |
| `RB_TKYA_BACKEND` controls | future adapter/runtime selection controls | open question | Current env contract should not be replaced casually; future controls need a controlled migration plan. |
| n/a | `create_topocore()` | direct candidate | Public facade creation should be the preferred entrypoint instead of internal imports. |
| n/a | `EngineQuery` | direct candidate | Concept aligns with current query intent but requires field-shape confirmation. |
| n/a | `EngineCandidate` | direct candidate | Candidate objects already exist conceptually in RepoBrain’s current bridge layer. |
| n/a | policy payloads | adapter-required | RepoBrain must normalize current GitHub/runtime context into a v6-safe policy payload. |
| n/a | typed summaries | product-mapping-required | RepoBrain must decide which typed summaries become private diagnostics vs public-safe outputs. |
| n/a | `decide_external()` | adapter-required | External-safe calls are conceptually useful, but RepoBrain must control when and how they are used. |
| n/a | `ExternalDecisionView` | product-mapping-required | Useful for bounded/public surfaces, but RepoBrain still needs product-level output mapping. |
| n/a | no internal module imports | direct candidate | This should be a hard rule for the migration. |
| n/a | no `decide_raw` exposure | direct candidate | External and user-facing surfaces must not expose raw internal decision payloads. |

## 5. GitHub Models LLM Role in the Future Architecture

The LLM remains in the RepoBrain layer, not inside TopoCore v6.

Current live provider family is GitHub Models.

In the future architecture:

- LLM prepares bounded summaries and explanations
- LLM does not become the final decision-maker
- LLM remains upstream of TopoCore v6, not embedded inside it

The LLM must not claim:

- safe-to-merge
- security verdict
- approval/rejection verdict
- autonomous patch application
- file modification
- commit creation
- branch creation
- PR creation

Future LLM output families should remain bounded to RepoBrain-side preparation layers such as:

- intent summary
- PR/diff/check summary
- evidence summary
- unknowns
- confidence hints
- risk hints
- patch draft only under existing Fix-Lite / no-patch governance
- human-readable explanation draft

That means the future role of GitHub Models is supportive and summarizing, not authoritative over final safe product decisions.

## 6. Proposed Target Architecture

Target flow:

`GitHub event / PR context`
-> `RepoBrain runtime collection`
-> `GitHub Models LLM summaries`
-> `RepoBrain validation / normalization`
-> `RepoBrainTopoCoreV6Adapter`
-> `TopoCore v6 public facade`
-> `RepoBrain-safe product mapping`
-> `GitHub comment/check-run output`

Architecture rules:

- TopoCore v6 must not scan GitHub.
- TopoCore v6 must not call LLM directly.
- TopoCore v6 must not become RepoBrain-specific.
- RepoBrain must not import TopoCore v6 internal modules.
- external users must not see:
  - `decide_raw` output
  - workflow internals
  - governance internals
  - event/artifact internals
  - `compression_stats`
  - raw traces
  - raw query text

The adapter must therefore be a product boundary, not only a type conversion boundary.

## 7. Migration Strategy

### Phase A - current baseline freeze

Freeze the current v5/TKYA runtime truth and keep the linkage docs/test guards authoritative.

### Phase B - v5/v6 mapping

Map current RepoBrain v5/TKYA expectations to v6 public-facade concepts with explicit compatibility decisions.

### Phase C - LLM summary contract

Define the exact RepoBrain-side summary objects the adapter can consume without letting LLM output act as the final decision.

### Phase D - optional adapter skeleton

Create an internal adapter shell such as `RepoBrainTopoCoreV6Adapter` without enabling it in runtime routing yet.

### Phase E - fake/stub v6 tests

Add fake/stub tests that validate shape compatibility and safe product mapping before any live integration.

### Phase F - local/private v6 validation

Exercise the adapter in local/private validation only, without enabling the path in public runtime behavior.

### Phase G - shadow mode: v5 primary, v6 advisory

Keep v5 as the runtime authority while v6 produces advisory outputs for comparison only.

### Phase H - decision diff diagnostics

Record structured differences between v5 and v6 outcomes to identify semantic drift before any user-visible route migration.

### Phase I - first controlled canary

Enable a tightly bounded canary path only after shadow-mode evidence is stable.

### Phase J - progressive route migration

Move route classes gradually, not all at once, with explicit regression gates and product-level review.

### Phase K - v5 retirement planning only after proof

Consider retirement planning only after v6 has enough evidence, diagnostics, and product-level safety proof to replace v5 behavior responsibly.

Sprint 16 covers only the design/blueprint for this sequence. Later sprints would implement the actual adapter and runtime work.

## 8. First Migration Target Recommendation

The first implementation target after Sprint 16 should be:

- adapter-only bridge first

It should not begin with:

- ask-first
- review-first
- fix-first

Why:

- current runtime is stable and test-protected
- direct behavior replacement is risky
- an adapter-only bridge allows shape validation without changing product behavior
- shadow-mode evidence should come before any canary

Fix migration should be late or last because fix carries the strictest safety stack:

- extraction
- guard
- targeting
- validation
- retry/fallback
- patch governance
- safe `no_patch` behavior

## 9. Failure Taxonomy

Future v6 integration should classify failures into explicit groups:

- LLM summary issue
- RepoBrain adapter issue
- insufficient GitHub data
- user request ambiguity
- v5/v6 semantic mismatch
- TopoCore v6 platform issue
- policy/security block
- private dependency/install issue

Bounded retry guidance:

- policy/security block: `0` LLM retries
- schema/format issue: `1` repair retry
- weak evidence/unknowns: `1` repair retry or stop with `needs_more_information`
- adapter bug: `0` LLM retries, developer issue
- insufficient source data: ask user or produce safe no-result / no-patch output

There must be no infinite retry loop that keeps asking the LLM until TopoCore accepts the payload.

## 10. Repo Boundary Rules

### RepoBrain-Action owns

- primary/private GitHub runtime
- current v5/TKYA contract truth
- future v6 adapter around the public facade
- GitHub Models LLM orchestration
- safe product-level output mapping
- tests/docs/regression guards

### TopoCore v6 owns

- foundation decision library
- public facade
- decision contracts
- typed-summary ingestion
- safe external decision boundary

### repobrain-community owns

- public external GitHub foundation host
- reusable external workflow
- public install template
- bounded external command surface

### elen-mcp-prod_v2

- validation-only surface

## 11. Explicit Non-Goals

Sprint 16 non-goals:

- no runtime code changes
- no workflow changes
- no `action.yml` changes
- no `topocore_v6` dependency addition
- no `topocore_v6` import
- no replacement of `RB_TKYA_BACKEND=v5`
- no removal of the v5 vendor file
- no patch/fix behavior change
- no LLM provider code change
- no external community workflow change
- no Marketplace/package strategy
- no safe-to-merge or security verdict claims

## 12. Acceptance Criteria

Sprint 16 is complete only if:

- the new blueprint document exists
- it clearly states v5 is the current active runtime
- it clearly states v6 is the future target
- it correctly separates `RepoBrain-Action`, TopoCore v6, `repobrain-community`, and the validation repository responsibilities
- it explains GitHub Models as the current LLM provider path
- it defines v5->v6 mapping categories
- it recommends adapter-only bridge as the first implementation target
- it defines shadow-mode and decision-diff strategy
- it includes failure taxonomy and bounded retry guidance
- it contains no false claim that v6 is already wired
- it contains no autofix, patch application, file modification, commit creation, branch push, PR creation, full review parity, security verdict, safe-to-merge, approval, or rejection claims
- it preserves the rule that no runtime behavior was changed in Sprint 16
