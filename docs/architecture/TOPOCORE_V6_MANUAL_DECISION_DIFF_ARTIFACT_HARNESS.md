# TopoCore v6 Manual Decision-Diff Artifact Harness

## 1. Purpose

Sprint 25 integrates the manual/local validation harness with the decision-diff and advisory-artifact helpers.

Current truth:

- it remains manual/local only
- it is not shadow mode
- it is not canary
- it does not change GitHub runtime
- it does not replace v5/TKYA
- it does not require TopoCore v6 in default CI

The purpose is to let developers generate sanitized manual comparison evidence from local fixtures without affecting any live RepoBrain behavior.

## 2. Relationship to Sprints 16-24

See:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_ARTIFACT_FORMAT_AND_SHADOW_PLAN.md`

Relationship summary:

- Sprint 22 created the decision-diff helper
- Sprint 24 created the advisory artifact helper
- Sprint 25 connects both to the manual/local harness only

## 3. Manual Harness Flow

Current manual flow:

`RB_TOPOCORE_V6_LOCAL_VALIDATE=1`
-> build adapter preview
-> call local/private TopoCore v6 public facade if available
-> build sanitized v6 advisory snapshot
-> pair with sanitized fixture v5 primary snapshot
-> build decision-diff report
-> build advisory artifact in memory
-> print compact safe summary

This remains an opt-in local developer path. It is not part of normal RepoBrain command execution.

## 4. JSON Output Mode

Optional environment flag:

- `RB_TOPOCORE_V6_LOCAL_ARTIFACT_JSON=1`

Rules:

- JSON mode is opt-in
- output is stdout only
- no disk writes occur
- output must remain sanitized
- no raw query, raw code, raw diff, secrets, or internal traces are allowed

## 5. Safety Boundaries

- no `decide_raw`
- no `compression_stats`
- no raw traces
- no governance internals
- no raw query, code, or diff
- no secrets or tokens
- no artifact publishing
- no PR comments or checks
- no patch application

## 6. What This Enables

- developers can manually compare fixture-based v5 primary snapshots with local v6 advisory behavior
- developers can inspect sanitized decision-diff severity and go/no-go hints
- artifacts can support future shadow-mode readiness discussions
- this still does not affect users or runtime behavior

## 7. What This Does Not Enable

- no live shadow mode
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no GitHub runtime integration
- no public or external behavior change

## 8. Future Follow-Up

The next sprint may define:

- a human review checklist for manual artifacts, or
- a disabled-by-default shadow-mode implementation plan with exact env gates

Any follow-up must still avoid live runtime changes unless explicitly approved.
