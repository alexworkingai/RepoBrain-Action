# Public Readiness Assessment

## Current Repository Visibility

- `RepoBrain-Action`: `PRIVATE`
- TopoCore v6: `PRIVATE`
- `Elen-MCP-v.2.2.0`: `PRIVATE`

## Recommended Visibility Target

- current target:
  - `RepoBrain-Action` stays private while the TopoCore public-distribution decision remains unresolved
- future possible target:
  - public `RepoBrain-Action` after explicit approval and an approved TopoCore dependency strategy

## What Must Stay Private

- TopoCore v6 repository
- TopoCore v6 source and internal decision logic
- any real token or private key material
- consumer repository secrets such as `TOPOCORE_V6_REPO_TOKEN`

## Public Scrub Status

Public scrub improvements completed by Sprint 77:

- top-level `LICENSE` added
- local machine paths sanitized from tracked docs
- legacy release docs relabeled as historical/internal
- support and pinning policy documented
- no real secret or private key values found in tracked docs
- no private TopoCore source copied into RepoBrain-Action

## Remaining Public Blockers

1. Public visibility still requires an approved TopoCore dependency and distribution strategy beyond private beta `private_checkout`.
2. Repository visibility change requires explicit owner approval.

## User Support Implications

If `RepoBrain-Action` becomes public before the TopoCore distribution model is approved:

- users will see a public action that still depends on a private proprietary runtime boundary
- users may assume turnkey public install support that does not yet exist
- users may misunderstand the difference between public RepoBrain-Action visibility and private TopoCore access rights

## Decision

- public readiness decision: `PUBLIC_BLOCKED_BY_DISTRIBUTION_STRATEGY`
- private beta decision: `PRIVATE_BETA_RC_CONFIRMED`
- TopoCore security decision: `TOPOCORE_SECURITY_POLICY_ADOPTED`
