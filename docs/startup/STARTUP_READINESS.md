# Startup Readiness (Current Stage)

## Purpose

This document explains RepoBrain readiness at the current startup stage: externally evaluable, pre-marketplace, and intentionally bounded.

## What RepoBrain Is Today

RepoBrain is a governed repository cognition runtime with:

- GitHub-native ask/review/fix as primary surface,
- external GitHub mode foundation (third-party doctor/help/ask plus bounded Review Candidate and Fix-Lite Candidate through the public `repobrain-community` host),
- external ask-only CLI surface,
- MCP ask-only surface,
- explicit safety/governance and auditable artifacts.

## What Is Ready to Evaluate

1. GitHub mode behavior and artifacts.
2. External GitHub mode foundation path on a third-party repository.
3. External CLI ask path on a third-party repository checkout.
4. MCP ask contract and honest unsupported blocking.
5. Operator readiness flow for GitHub App setup.

## What Is Intentionally Bounded

1. External GitHub mode foundation remains bounded:
   - `/repobrain review` is a bounded read-only Review Candidate,
   - `/repobrain fix` is a bounded Fix-Lite Candidate manual-only patch suggestion,
   - no patch application, file modification, commit creation, branch pushing, or PR creation is claimed.
2. MCP capabilities beyond ask are unsupported.
3. Marketplace/admin/billing surfaces are not part of this stage.

## Why This Is Pre-Marketplace

RepoBrain has repeatable packaging, governance, and bounded external evaluation, but does not claim broad distribution maturity yet.

## Readiness References

- Evaluator guide: `docs/startup/EVALUATOR_GUIDE.md`
- External evaluation path: `docs/startup/EXTERNAL_EVALUATION_PATH.md`
- Readiness matrix: `docs/startup/READINESS_MATRIX.md`
- Product boundaries: `docs/startup/PRODUCT_BOUNDARIES.md`
- Design partner overview: `docs/startup/DESIGN_PARTNER_OVERVIEW.md`
- Strategic package index: `docs/strategy/ATTENTION_PACK_INDEX.md`
