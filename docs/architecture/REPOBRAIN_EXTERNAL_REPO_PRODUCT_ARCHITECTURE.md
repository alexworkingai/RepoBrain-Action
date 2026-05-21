# RepoBrain External Repo Product Architecture

## Purpose

This document records the working product architecture after Sprint 69.
It replaces the old community-hosted bridge model with a direct pilot-consumer model.

## Final Repository Structure

- `topocore`
  - private permanently
  - TopoCore v6 engine and private decision logic
- `RepoBrain-Action`
  - main product repository
  - GitHub Action, docs, tests, and onboarding
- `Elen-MCP-v.2.2.0`
  - first external pilot consumer repository
- `repobrain-community`
  - retired from the working product architecture
  - optional archival later

## Private/Public Recommendation

- `topocore`: private permanently
- `RepoBrain-Action`: private during pilot, prepare for public only after explicit scrub/release readiness work
- `Elen-MCP-v.2.2.0`: private pilot consumer repository
- `repobrain-community`: not part of the product; archive later if desired

## Why `repobrain-community` Is Removed From Architecture

`repobrain-community` added an extra bridge layer without adding current product value.
After Sprint 68, the v6-only transition was already complete, so keeping a separate install bridge would only add:

- duplicate onboarding truth
- duplicate workflow ownership
- more places for stale runtime claims to survive
- more difficulty proving which repository is the actual product host

Current policy is direct:

- product action lives in `RepoBrain-Action`
- private engine lives in `topocore`
- pilot consumer repositories install directly from `RepoBrain-Action`

## TopoCore v6 Private Dependency Model

TopoCore v6 remains private and is never copied into consumer repositories.
The consumer workflow checks out the private repository at runtime using a repository secret.

## External Repo Pilot Model

The external consumer repository owns:

- caller workflow file
- repository secrets/variables
- issue and PR smoke evidence
- its own app code and validation lifecycle

`RepoBrain-Action` owns:

- action implementation
- onboarding docs/examples
- product regression tests
- current runtime and safety truth

## Security Boundaries

- TopoCore v6 source stays private
- no patch/autofix by default
- no file modification by RepoBrain behavior
- no RepoBrain-created commit/branch/PR behavior
- no `repobrain-community` dependency in active product runtime/onboarding

## Next Product Roadmap

Next external-product work should focus on:

- command-matrix validation on the pilot consumer repo
- visible backend evidence across issue and PR scopes
- hardening caller-repo install/readiness guidance
- release-readiness review for wider distribution
