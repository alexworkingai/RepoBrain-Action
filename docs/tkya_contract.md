# Protected Kernel Decision Contract (Public-Safe)

## Scope

This document describes the public-safe decision boundary between RepoBrain and its protected internal kernel.

It is intentionally limited to operator-safe and public-safe behavior.
It does not disclose internal kernel structure, internal schema design, module layout, implementation paths, or reconstructable execution wiring.

## Public-Safe Decision Boundary

RepoBrain receives a protected decision outcome from its internal kernel and uses that outcome to drive:

- bounded command behavior,
- governance-aware execution,
- compact user-facing responses,
- public-safe and operator-safe artifacts.

Public documentation describes only externally relevant behavior and supported output categories.

## What Public-Safe Surfaces May Expose

Outward-facing surfaces may expose only high-level, product-safe decision truth such as:

- decision category,
- execution/governance outcome,
- boundedness and safety markers,
- public-safe diagnostics,
- explicit supported/unsupported capability results.

These are operational outcomes for safe usage, not disclosures of internal kernel design.

## Behavioral Guarantees

RepoBrain preserves the following public-safe guarantees:

1. Safety and governance outcomes are respected as hard runtime boundaries.
2. Bounded execution remains explicit rather than implied.
3. Public outputs stay usersafe and avoid protected kernel disclosure.
4. Audit/evidence artifacts preserve decision truth at a public-safe or operator-safe level without exposing protected internal implementation.

## Audit and Evidence Boundary

RepoBrain exports decision and governance truth through artifacts designed for safe interpretation.

These artifacts are intended to help operators understand:

- what outcome occurred,
- whether execution was allowed, bounded, or blocked,
- what capability surface is supported,
- how to interpret the current result safely.

They do not disclose internal kernel layout, internal contracts, or reconstructable implementation details.

## What This Document Intentionally Does Not Disclose

This document does not define or expose:

- internal kernel object names,
- internal field schemas,
- internal route/control enumerations,
- internal module/file organization,
- implementation-level decision wiring,
- reverse-engineering-oriented details.

## Operator Guidance

For practical usage, rely on:

- supported command/capability documentation,
- explicit blocked/unsupported behavior,
- readiness outputs,
- public-safe and operator-safe artifacts,
- user/operator runbooks.

These are sufficient for safe operation without exposing protected kernel internals.
