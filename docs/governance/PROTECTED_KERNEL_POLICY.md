# Protected Kernel Policy

## Policy Statement

RepoBrain uses a protected internal kernel. That kernel is not publicly documented at implementation level.

All outward-facing surfaces must stay public-safe.

## Never Disclose

Do not disclose in outward-facing docs/help/examples/artifacts:

- internal architecture,
- internal module composition,
- internal file paths,
- kernel schema internals,
- reconstructable internal contracts,
- implementation wiring details that enable reverse engineering.

## Allowed Public-Safe Abstractions

Use abstractions such as:

- governed repository cognition,
- bounded decision runtime,
- evidence-aware orchestration,
- protected internal kernel,
- safe capability surface,
- model-agnostic orchestration layer,
- public-safe/operator-safe outputs.

## Capability Surface Rule

Capability surfaces may expose behavior and outcome categories.
They may not expose kernel design.

## Disclosure Review Rule

Any outward text change touching kernel-adjacent language requires explicit protected-kernel review.

If disclosure risk is ambiguous, stop and escalate.

## Examples and Help Text Rule

Help text and examples must stay:

- truthful about supported/unsupported behavior,
- compact and operator-usable,
- free of reconstructable kernel internals.
