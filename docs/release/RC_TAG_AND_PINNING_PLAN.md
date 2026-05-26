# RC Tag And Pinning Plan

## Current Version

- `VERSION`: `0.5.0-rc.1`

## Current Git Tags

- no current release tags are required for Sprint 85 readiness

## Recommended RC Tag

- `v0.5.0-rc.1`

If `VERSION` changes before approval, the tag should match the actual release-candidate version.

## Tag Type

- annotated tag preferred

## Tag Creation

- only after explicit owner approval
- do not create the tag automatically in Sprint 85

## Consumer Pinning

- after an approved RC tag exists, selected partner docs should prefer tag or pinned SHA
- until then, the controlled pilot may still use `@main`

## Post-Public Recommendation

- avoid floating `@main` for selected partner testing once the RC tag exists

## Rollback

- tags are immutable trust anchors
- do not rewrite public tags

## Decision

- `RC_TAG_READY_PENDING_OWNER_APPROVAL`

If owner approval is later explicit and the tag is created, the decision may become:

- `RC_TAG_CREATED`
