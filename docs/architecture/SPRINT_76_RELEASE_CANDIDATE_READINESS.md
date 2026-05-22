# Sprint 76 - Release Candidate and Public Readiness Assessment

> Historical readiness checkpoint. Public-scrub, license, TopoCore security, support, and positioning gates were advanced further in `docs/architecture/SPRINT_77_PUBLIC_SCRUB_LICENSE_TOPOCORE_SECURITY_POSITIONING.md`.

## Purpose

Sprint 76 assesses RepoBrain-Action release-candidate, public-readiness, and Marketplace-readiness status.
It follows Sprint 75 onboarding and troubleshooting polish.
This sprint does not change runtime policy or enable patch/autofix.

## Baseline

- RepoBrain-Action latest main before Sprint 76: `4d88beb Polish external onboarding and troubleshooting`
- Sprint 70 command matrix passed
- Sprint 71 retrieval quality passed
- Sprint 72 verify productionized
- Sprint 73 fix productized
- Sprint 74 security/fork safety passed
- Sprint 75 onboarding/troubleshooting passed

## Readiness Rubric

Categories used:

1. runtime readiness
2. command readiness
3. external install readiness
4. security readiness
5. public repository scrub readiness
6. Marketplace readiness
7. release engineering readiness

Decision labels:

- `READY`
- `READY_WITH_NOTES`
- `BLOCKED`
- `NOT_APPLICABLE`
- `NEEDS_APPROVAL`

## Public Scrub Audit

Findings:

- secret/token/private key values:
  - none found in tracked content
- private paths:
  - historical docs still contain local Windows paths such as `<LOCAL_PROJECT_ROOT>\\...`
- private TopoCore source:
  - not present in product repo
- v5 residue:
  - no active runtime residue
  - historical docs still mention v5 as history
- `repobrain-community` dependency:
  - no active dependency
  - historical docs still mention community-era history
- unsafe claims:
  - active docs do not claim patch/autofix, merge approval, or security approval
- permission overreach:
  - active external example remains read-mostly

Public scrub conclusion:

- `PUBLIC_BLOCKED_BY_SCRUB`

## Action Metadata Audit

- `action.yml` name updated from pilot-era `RepoBrain Local MVP` to `RepoBrain Action`
- description updated to match the current product surface
- branding metadata added
- safe defaults remain intact
- no v5/community input surface is reintroduced
- `GITHUB_ACTION_PATH` use remains correct
- caller repo root continues to use `github.workspace`

## Repository Visibility Recommendation

- TopoCore v6:
  - `PRIVATE`
- RepoBrain-Action:
  - keep `PRIVATE` for now
  - recommended decision: `PRIVATE_BETA_RC_READY`
- Elen-MCP-v.2.2.0:
  - keep `PRIVATE`
- `repobrain-community`:
  - no product role
  - archive later if desired

## Release Artifacts Created

- `docs/release/RELEASE_CANDIDATE_CHECKLIST.md`
- `docs/release/PUBLIC_READINESS_ASSESSMENT.md`
- `docs/release/MARKETPLACE_READINESS_ASSESSMENT.md`
- `docs/release/RELEASE_NOTES_RC1.md`

## Live RC Smoke Result

Not run in Sprint 76.

Reason:

- this sprint focused on release/public-readiness assessment and scrub classification
- live command path was already validated through Sprints 69 to 75

## Blockers And Gaps

Blockers:

- no top-level `LICENSE`
- historical docs still expose local Windows paths
- historical docs still include old community/v5 narratives that need public-safe relabeling or relocation
- Marketplace/public tag and support policy are not finalized
- private TopoCore dependency means public/Marketplace install still needs an approved product strategy

Deferred:

- actual public-visibility flip
- Marketplace publication
- legacy release-doc cleanup outside the new release-readiness path

## Product Status

- overall release decision: `PRIVATE_BETA_RC_READY`
- public visibility decision: `PUBLIC_BLOCKED_BY_SCRUB`
- Marketplace decision: `MARKETPLACE_NOT_READY`

## Next Step

Sprint 77 - Public Scrub, License, and Support Policy Gate

## Non-Goals

- no v5
- no repobrain-community
- no patch/autofix
- no runtime policy change
- no visibility switch in Sprint 76
- no Marketplace publication in Sprint 76
