# Team Governance Layer

## Purpose

This governance layer defines how RepoBrain changes are proposed, reviewed, validated, and accepted as a team-owned product.

It exists to keep product evolution safe, explicit, and auditable while preserving accepted runtime behavior and protected-kernel boundaries.

## Scope

This package applies to all change work after accepted Sprint 57-61 baseline.

It governs:

- ownership and change classification,
- acceptance evidence standards,
- stop-and-escalate rules,
- release discipline,
- protected-kernel disclosure boundaries.

## Governance Principles

1. Local green is required but not acceptance.
2. Live behavior and artifacts are source of truth where relevant.
3. Supported vs unsupported boundaries must stay explicit and honest.
4. Protected kernel internals are never disclosed in outward-facing surfaces.
5. Scope expansion requires explicit sprint authorization.

## Document Map

- Change classes: `docs/governance/CHANGE_CLASSES.md`
- Acceptance policy: `docs/governance/ACCEPTANCE_POLICY.md`
- Stop and escalate rules: `docs/governance/STOP_AND_ESCALATE.md`
- Release discipline: `docs/governance/RELEASE_DISCIPLINE.md`
- Protected-kernel policy: `docs/governance/PROTECTED_KERNEL_POLICY.md`

## Baseline Preservation Rule

Governance does not override accepted behavior from Sprint 57-61.

Any change that would alter accepted semantics must be explicitly classified as a governed runtime change and validated under the higher-risk path.
