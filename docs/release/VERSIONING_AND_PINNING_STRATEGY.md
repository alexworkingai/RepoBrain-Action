# Versioning And Pinning Strategy

## Current VERSION

- `0.5.0-rc.1`

## Current Tag State

- no Git tags currently exist

## Private Beta Recommendation

For a controlled private pilot:

- `@main` is acceptable only for tightly controlled pilot repositories
- immutable SHA pinning is better for reproducibility and rollback safety

## Public Release Recommendation

For a public release:

- use immutable tags
- examples:
  - `v0.5.0-rc.1`
  - `v0.5.0`
- users should pin to a tag or SHA, not a floating `main`

## Marketplace Readiness

Marketplace preparation requires a stable tag strategy and release discipline.

## TopoCore v6 Dependency

TopoCore v6 remains private.
Its token and ref strategy must stay explicit and documented.

## Decision

- `TAG_STRATEGY_READY_FOR_PRIVATE_RC`
- public tag creation is pending explicit approval
- no tags are created in Sprint 77
