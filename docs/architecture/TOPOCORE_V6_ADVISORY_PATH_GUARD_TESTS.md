# TopoCore v6 Advisory Path Guard Tests

## 1. Purpose

Sprint 29 strengthens guard tests around the disabled advisory path skeleton.

Current truth:

- it does not activate shadow mode
- it does not call TopoCore v6
- it does not change GitHub runtime behavior
- it does not replace v5/TKYA

This sprint exists to prove the isolated shadow-path skeleton remains safe, inert, and product-safe while it is disconnected from live RepoBrain runtime flow.

## 2. Relationship to Sprint 28

See:

- `docs/architecture/TOPOCORE_V6_DISABLED_ADVISORY_PATH_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_PATH_RUNTIME_SEAM_DESIGN.md`
- `docs/architecture/TOPOCORE_V6_PHASE_1_2_CLOSEOUT_AND_PHASE_3_SCOPE.md`

Relationship summary:

- Sprint 28 created the isolated no-op skeleton
- Sprint 29 verifies that skeleton stays safe under environment flags, invalid inputs, nested forbidden fields, and forbidden-output scenarios

## 3. Guard Areas

Sprint 29 guard coverage focuses on:

- disabled/default no-op
- explicit disabled no-op
- enabled-not-implemented behavior
- artifact flag safety
- fail-closed recording without behavior change
- forbidden input rejection
- nested forbidden-field detection
- forbidden output prevention
- sanitized failure categories
- no runtime wiring
- no `topocore_v6` dependency
- fix-command conservatism

## 4. What Sprint 29 Proves

Sprint 29 proves that:

- the skeleton is safe to keep in the repo while disconnected
- default behavior remains inert
- the enabled flag still does not activate v6
- artifacts cannot be persisted or published
- forbidden fields are blocked
- no runtime path is changed

## 5. What Sprint 29 Does Not Prove

Sprint 29 does not prove:

- any live v6 advisory call
- any real shadow mode
- any canary behavior
- any route migration
- any v5/v6 parity result
- any fix migration
- any production dependency strategy

## 6. Future Follow-Up

- Sprint 30 should be Phase 3 Review / Go-No-Go
- Sprint 30 should decide whether the project is ready to propose a future controlled advisory shadow experiment
- Sprint 30 must not itself become canary or route migration unless separately approved

See also:

- `docs/architecture/TOPOCORE_V6_PHASE_3_REVIEW_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_CONTROLLED_ADVISORY_EXPERIMENT_RUNBOOK.md`
- `docs/architecture/TOPOCORE_V6_STILL_DISABLED_ADVISORY_BOUNDARY.md`
