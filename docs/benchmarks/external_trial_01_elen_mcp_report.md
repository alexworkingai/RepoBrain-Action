# External Trial #01 Report вЂ” alexworkingai/Elen-MCP-v.2.2.0

## Trial Identity

- trial id: `external-repo-trial-01`
- repository: `alexworkingai/Elen-MCP-v.2.2.0`
- scope: first real third-party validation of RepoBrain external mode
- sprint narrative source: accepted Sprint 59 outcomes

## What This Trial Proved

1. External mode executes against a real third-party repository checkout.
2. External `ask` path works and returns governed answer output.
3. External `review` path is blocked explicitly as unsupported (honest failure mode).
4. This is an external execution path, not yet full GitHub-native PR runtime in target repository.
5. The same ask-first boundary can be exposed through the thin MCP surface with identical honest unsupported behavior.

## Benchmark Narrative (Concise)

Sprint 59 establishes that RepoBrain can be run outside its home repository with reproducible, operator-usable flow for ask scenarios. It does not claim external parity for review/fix yet. The honest unsupported block is part of the product trust contract, not a silent failure.

## Operator Interpretation Guide

Treat this trial as:

- `PASS` for external ask viability,
- `PARTIAL` for broader external command coverage,
- non-pass for external review/fix support (expected at current maturity stage).

## Evidence Expectations

For each trial execution, capture:

1. exact command string,
2. stdout status/decision,
3. artifacts/log references,
4. operator blockers (if any),
5. final verdict classification.

Use template:

- `docs/trials/external_repo_trial_evidence_template.md`

## Explicit Non-Claims

This report does **not** claim:

- external review support,
- external fix support,
- production-complete third-party GitHub App integration from external mode alone.

## Next Validation Step

Run a repeated external ask on the same repository with different scoped queries and confirm artifact/log consistency, then prioritize external review/fix enablement only when explicit product scope allows it.

