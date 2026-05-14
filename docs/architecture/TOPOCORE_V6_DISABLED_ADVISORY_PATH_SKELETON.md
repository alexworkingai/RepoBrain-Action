# TopoCore v6 Disabled Advisory Path Skeleton

## 1. Purpose

Sprint 28 introduces a hard-disabled advisory path skeleton.

Current truth:

- it is not active shadow mode
- it is not canary
- it is not route migration
- it does not replace v5/TKYA
- it does not call TopoCore v6
- it does not change GitHub runtime behavior

This sprint exists to create a small, isolated no-op module that future guarded work can target without affecting current RepoBrain behavior.

## 2. Relationship to Sprints 26-27

See:

- `docs/architecture/TOPOCORE_V6_PHASE_1_2_CLOSEOUT_AND_PHASE_3_SCOPE.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_PATH_RUNTIME_SEAM_DESIGN.md`

Relationship summary:

- Sprint 26 defined Phase 3
- Sprint 27 designed the runtime seam
- Sprint 28 creates a hard-disabled no-op skeleton for later guarded work

## 3. Skeleton Behavior

Current behavior:

- disabled by default
- explicit disabled flag also returns a no-op result
- enabled flag does not call real v6 yet
- artifact flag does not persist or publish artifacts
- fail-closed flag is recorded but does not change live runtime
- the result remains safe, compact, and JSON-serializable

## 4. Environment Flags

Design-level flags:

- `RB_TOPOCORE_V6_SHADOW_ENABLED=0|1`
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0|1`
- `RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED=0|1`

Rules:

- defaults are safe
- all current behavior remains no-op unless future approved work connects this skeleton
- Sprint 28 does not wire these flags into GitHub runtime

## 5. Input and Output Boundaries

Input boundary:

- sanitized input only
- forbidden raw/internal fields are rejected

Output boundary:

- product-safe JSON-serializable output only
- no raw query, raw code, raw diff, prompts, secrets, tokens, compression stats, traces, governance internals, or `decide_raw`

## 6. What This Enables

- future tests can verify kill-switch and no-op behavior
- future runtime-adjacent work can target a safe isolated module
- future advisory path work can evolve incrementally without changing current behavior

## 7. What This Does Not Enable

- no live v6 advisory call
- no shadow mode activation
- no canary
- no route migration
- no fix migration
- no artifact persistence
- no PR/check/comment changes

## 8. Future Follow-Up

- Sprint 29 should add internal artifact guard tests and failure-isolation tests around this skeleton
- Sprint 30 should review Phase 3 and decide go/no-go for any future runtime-adjacent experiment

See also:

- `docs/architecture/TOPOCORE_V6_ADVISORY_PATH_GUARD_TESTS.md`
