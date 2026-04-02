# Protected Kernel Contract (Public-Safe)

## Scope

This document defines the outward-facing contract between RepoBrain orchestration and the protected internal kernel.

It is intentionally product-safe and does not disclose internal kernel structure, module layout, or implementation paths.

## Core Decision Object

RepoBrain consumes a canonical decision object named `EngineDecision`.

Public-safe required fields:

- `route`
- `selected_chunk_ids`
- `compression_stats` (safe structured diagnostics only)
- `execution_mode`
- `llm_intent`
- `llm_decision_reason_short`
- `llm_decision_reason_code`

## Route Contract

The route vocabulary remains:

- `FAST`
- `DEEP`
- `WAIT`
- `REFUSE`
- `BLOCK`
- `REVIEW`

These route labels are stable orchestration categories, not disclosures of kernel internals.

## Behavioral Guarantees

1. Safety routes (`WAIT/REFUSE/BLOCK`) are respected as hard orchestration outcomes.
2. Non-safety routes (`FAST/DEEP/REVIEW`) remain bounded by runtime governance.
3. LLM execution is policy-governed and can be runtime-overridden safely.
4. Public outputs remain usersafe and avoid internal kernel disclosure.

## Audit/Evidence Guarantees

RepoBrain exports canonical decision truth through audit/evidence artifacts with public-safe and operator-safe boundaries.

The contract exposes decision categories and governance outcomes, not internal kernel implementation details.
