# TopoCore v6 Adapter Skeleton

## 1. Purpose

Sprint 18 introduces an inert adapter skeleton only.

Current truth:

- Sprint 18 adds a small code-level adapter shape for future TopoCore v6 preparation
- it does not wire TopoCore v6 into runtime
- it does not replace v5/TKYA
- it does not require `topocore_v6` in CI

This sprint exists to create a safe implementation foothold without changing current runtime routing or behavior.

## 2. Relationship to Sprint 16 and Sprint 17

See:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`

Relationship:

- Sprint 16 defined the controlled migration strategy
- Sprint 17 defined the GitHub Models LLM summary contract
- Sprint 18 introduces a code-level adapter shape for future implementation work

See also:

- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`

Sprint 18 still does not wire TopoCore v6 into live RepoBrain runtime.

## 3. Adapter Skeleton Scope

The Sprint 18 adapter skeleton:

- builds request previews
- maps validated summaries into policy payloads
- preserves safe candidate refs
- blocks unsafe raw candidate metadata
- does not call TopoCore v6

The skeleton is intentionally limited to preview-building and compatibility-shaping only.

## 4. Non-Goals

- no runtime routing switch
- no shadow mode
- no canary
- no `topocore_v6` dependency
- no `topocore_v6` import
- no `create_topocore()` call
- no `decide()` call
- no `decide_external()` call
- no v5 removal
- no fix migration
- no patch behavior change

## 5. Future Follow-Up

The next sprint may define fixture contracts or adapter compatibility tests for fake or stub v6 decisions.

That follow-up should still avoid live runtime switching unless explicitly approved.
