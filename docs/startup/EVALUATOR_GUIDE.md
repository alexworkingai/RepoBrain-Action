# Evaluator Guide

## Who Should Evaluate Now

Good fit now:

- engineering teams evaluating governed PR/repository assistance,
- operators able to run GitHub workflow validation and collect artifacts,
- design partners who can work with bounded capability surfaces.

Not a fit yet:

- users expecting full external review/fix parity,
- users expecting marketplace-style turnkey onboarding at scale.

## Minimal Evaluation Sequence

1. Confirm setup/readiness path is explicit and actionable.
2. Validate GitHub mode on an open PR (`help`, `ask`, `review`, `fix` with safe expectations).
3. Validate external GitHub mode foundation on a third-party repo (`doctor`, `help`, `ask`, `review`, `fix`).
4. Validate external ask path on local third-party checkout.
5. Validate MCP ask path and unsupported block behavior for non-ask capability.

## Success Criteria

Evaluation is successful when:

1. Supported behaviors match docs.
2. Unsupported behaviors block honestly and explicitly.
3. Artifacts are coherent with command outcomes.
4. Operator can identify next action without guesswork.

## Evidence to Inspect

- readiness artifacts (`repobrain-install-readiness`)
- audit artifacts (`repobrain-audit`)
- diagnostic summary (`repobrain-diagnostic-summary`)
- evidence pack (`repobrain-tkya-evidence-pack`)
- benchmark artifact when applicable (`repobrain-stability-benchmark`)

## Stop Conditions

Stop and escalate when:

1. docs and live behavior diverge,
2. supported/unsupported boundary is ambiguous,
3. setup requires out-of-scope capability expansion,
4. outward wording would risk protected-kernel disclosure.
