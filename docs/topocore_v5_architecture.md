# Protected Kernel Architecture (Public-Safe)

## Scope

RepoBrain is powered by a protected internal kernel.

This document intentionally uses high-level product-safe abstractions only:

- governed repository cognition
- bounded decision runtime
- evidence-aware orchestration
- model-agnostic orchestration layer

## Public-Safe Architecture View

1. Input normalization and policy context preparation.
2. Evidence selection and bounded decision generation.
3. Governance-aware execution outcome (`route`, `execution_mode`, policy reasons).
4. Structured artifact export with public-safe/operator-safe separation.

## What Is Intentionally Not Disclosed

- internal module composition
- internal file paths
- kernel schema internals
- implementation wiring details

## Operator Relevance

Operators should rely on:

- readiness status,
- command outcomes,
- audit/evidence artifacts,
- explicit supported/unsupported capability contracts.

This is sufficient for safe operation without exposing protected internals.
