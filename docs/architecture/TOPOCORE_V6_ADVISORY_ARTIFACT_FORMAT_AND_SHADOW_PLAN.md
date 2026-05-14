# TopoCore v6 Advisory Artifact Format and Shadow Plan

## 1. Purpose

Sprint 24 defines the advisory artifact format and the concrete shadow-mode implementation plan.

Current truth:

- it does not activate shadow mode
- it does not wire TopoCore v6 into GitHub runtime
- it does not replace v5/TKYA
- it does not require TopoCore v6 in default CI
- it prepares the artifact layer needed before any future advisory shadow-mode implementation

This sprint may add safe, dependency-free helper code for in-memory artifact construction, but it must not change runtime behavior.

## 2. Relationship to Sprints 16-23

See:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`

Relationship summary:

- Sprint 23 defined shadow-mode go/no-go criteria
- Sprint 24 defines the safe advisory artifact format and the planning boundary for future implementation

## 3. Advisory Artifact Definition

An advisory artifact is:

- a sanitized, product-safe internal or manual record
- built from a sanitized v5 primary snapshot
- built from a sanitized v6 advisory snapshot
- built from a sanitized decision-diff report
- never built from raw engine objects
- never built from raw TopoCore internals
- never shown directly to users

The artifact exists to preserve structured comparison evidence without exposing internals or letting advisory data affect current RepoBrain behavior.

## 4. Artifact Schema

The intended schema is compact and JSON-serializable:

- `schema_version`
- `artifact_kind`
- `mode`
- `command`
- `source`
- `v5_primary_snapshot`
- `v6_advisory_snapshot`
- `decision_diff`
- `classification`
- `retention`
- `safety`

The schema may evolve later, but it must remain sanitized and product-safe.

## 5. Allowed Fields

Safe allowed fields include:

- `command`
- safe route, status, or action category
- selected safe chunk ids or overlap counts
- safe reason code
- sanitized failure category
- severity
- go/no-go hint
- fixture name
- validation run label

Allowed fields must remain compact and must not include raw source payloads.

## 6. Forbidden Fields

Forbidden fields include:

- `decide_raw`
- `compression_stats`
- `trace`
- `raw_trace`
- raw query text
- raw code
- raw diff
- prompts
- system prompts
- hidden prompts
- governance internals
- event internals
- artifact internals
- secrets
- tokens
- API keys
- private keys
- `.env` contents
- raw exception dumps

If any forbidden field appears, artifact generation must fail or the content must be stripped before artifact creation succeeds.

## 7. Retention and Persistence Rules

Retention rules for this phase:

- Sprint 24 does not write artifacts to disk
- future manual/local runs may print compact summaries only
- future artifact persistence must be opt-in
- default persist must be `false`
- artifacts must be local and manual first
- no artifact should be uploaded or published to PR comments or checks by default
- retention must not include raw source payloads

## 8. Go/No-Go Hint Rules

The advisory artifact should include a compact go/no-go hint:

- `info` or `low` -> `go_candidate`
- `medium` -> `needs_review`
- `high` -> `blocked`
- `fix` command with mismatch cannot be `go_candidate`
- any forbidden-output issue is always `blocked`
- any v6-more-permissive result in sensitive cases is `blocked`

The hint is only an internal/manual classification cue. It is not a runtime routing decision and not a patch authorization signal.

## 9. Kill-Switch Implementation Plan

Future runtime-adjacent design, not implemented in Sprint 24:

- `RB_TOPOCORE_V6_SHADOW_ENABLED=0` disables all advisory calls
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0` disables artifact persistence
- missing `topocore_v6` falls back to v5-only behavior
- v6 failure produces sanitized advisory failure only
- v6 failure does not fail the main command
- v6 failure does not alter comments or checks
- v6 failure does not trigger patch or fix behavior

Sprint 24 defines these controls as design targets only. It does not implement runtime flags.

## 10. Future Shadow-Mode Implementation Plan

Future staged plan:

Stage 1:

- manual/local artifact production using fixtures

Stage 2:

- manual/local decision-diff artifact integration

Stage 3:

- disabled-by-default advisory path design review

Stage 4:

- runtime-adjacent PR/CI validation branch

Stage 5:

- limited advisory-only shadow experiment after explicit approval

Rules:

- no stage may skip safety gates
- fix path remains late or last
- canary is later than shadow mode

## 11. Stop Conditions

Future shadow implementation must stop if:

- forbidden output appears
- v6 is more permissive than v5 in blocked, fix, or security-sensitive cases
- high-severity mismatches are unresolved
- default CI requires private TopoCore v6
- v6 failure changes user-visible output
- patch or fix behavior changes
- `decide_raw` is called or exposed

## 12. Explicit Non-Goals for Sprint 24

- no runtime code changes to command flow
- no shadow-mode activation
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no patch behavior change
- no workflow changes
- no `action.yml` changes
- no `topocore_v6` dependency
- no `topocore_v6` import
- no `create_topocore()` call
- no `decide()` call
- no `decide_external()` call
- no `decide_raw()` call
- no LLM provider change
- no GitHub Models prompt behavior change
- no `repobrain-community` change
- no live GitHub API usage
- no live GitHub Models usage
- no artifact upload or publish behavior

## 13. Acceptance Criteria

Sprint 24 is complete only if:

- the new advisory artifact architecture document exists
- the artifact format is defined
- retention and sanitization rules are defined
- go/no-go hint rules are defined
- kill-switch design is defined
- future shadow-mode implementation stages are defined
- forbidden fields are documented
- optional helper and tests, if added, are dependency-free and safe
- no runtime behavior changes are introduced
- no v6 runtime wiring is introduced
- v5/TKYA remains the active primary runtime
