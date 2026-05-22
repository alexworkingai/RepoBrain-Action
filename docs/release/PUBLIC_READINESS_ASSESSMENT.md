# Public Readiness Assessment

## Current Repository Visibility

- `RepoBrain-Action`: `PRIVATE`
- TopoCore v6: `PRIVATE`
- `Elen-MCP-v.2.2.0`: `PRIVATE`

## Recommended Visibility Target

- recommended current target:
  - `RepoBrain-Action` stays private while release-candidate and scrub blockers are resolved
- future possible target:
  - public `RepoBrain-Action` after explicit approval and scrub completion

## What Must Stay Private

- TopoCore v6 repository
- TopoCore v6 source and decision internals
- any real token or private key material
- consumer repository secrets such as `TOPOCORE_V6_REPO_TOKEN`

## Public Blockers

1. No top-level `LICENSE`.
2. Historical docs still expose local operator paths such as `D:\\ARIADNA_Minsk\\...`.
3. Historical docs still include old v5/community-era narratives that are acceptable as internal history but not yet scrubbed for public visibility.
4. Legacy release docs (`docs/release_merge_plan.md`, `docs/release_execution_report.md`, `docs/release_final_checklist.md`) reflect an older release track and would need relabeling or public-safe replacement.
5. Public support expectations are not yet formalized.

## Required Scrub Before Public

- add a top-level license decision and file
- scrub or clearly relabel historical docs with local machine paths
- scrub or clearly relabel stale historical community/v5 release narratives
- separate public-facing release docs from internal historical release docs
- formalize public support boundary and escalation path

## User Support Implications

If `RepoBrain-Action` becomes public too early:

- new users will see historical docs that do not match the current product path
- users may assume Marketplace-level turnkey support that does not exist yet
- users may misunderstand the private TopoCore dependency model

## Decision

- release/public decision: `PUBLIC_BLOCKED_BY_SCRUB`
- recommended current release path: `PRIVATE_BETA_RC_READY`
