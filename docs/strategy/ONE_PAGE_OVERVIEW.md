# RepoBrain One-Page Overview

## What It Is

RepoBrain is a governed repository cognition runtime with explicit safety boundaries, operator-readable readiness, and artifact-backed evidence.

## Current Surfaces

1. GitHub mode (primary): `ask/review/fix`.
2. External GitHub mode foundation (bounded): `doctor/help/ask/review/fix` with bounded Review Candidate and Fix-Lite Candidate behavior.
3. External CLI mode (bounded): `ask` only.
4. MCP surface (bounded): `ask` only.

## What Is Proven

- GitHub-primary product flow is established.
- External GitHub mode foundation works as a bounded third-party public runtime surface.
- External CLI ask path works on a real third-party repository.
- MCP ask-only contract is explicit and bounded.
- Governance/packaging/startup-readiness docs align with accepted behavior.

## What Is Not Claimed

- Patch application, file modification, commit creation, branch pushing, or PR creation in the external public surface.
- MCP breadth beyond ask.
- Marketplace/admin/billing readiness.
- Full external GitHub-native review/fix parity.
- Security verdicts, safe-to-merge claims, or approval/rejection decisions.

## Why It Is Interesting

RepoBrain emphasizes governed execution and bounded trust over broad autonomous claims.
That makes it easier to evaluate, operate, and review in real team workflows.

## Suggested Evaluation Path

1. Validate GitHub mode with readiness + artifacts.
2. Validate external GitHub mode foundation on a real third-party PR.
3. Validate external CLI ask-only path.
4. Validate MCP ask-only path with explicit unsupported checks.

## References

- `docs/strategy/PROVEN_CAPABILITIES_SUMMARY.md`
- `docs/startup/STARTUP_READINESS.md`
- `docs/packaging/PACKAGING_OVERVIEW.md`
