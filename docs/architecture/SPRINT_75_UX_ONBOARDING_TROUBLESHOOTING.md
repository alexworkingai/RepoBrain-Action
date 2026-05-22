# Sprint 75 - UX, Onboarding, and Troubleshooting

## Purpose

Sprint 75 polishes external user onboarding, command UX, and troubleshooting.
This follows Sprint 74 security/permissions/fork hardening.
This sprint does not change runtime policy or enable patch/autofix.

## Baseline

- RepoBrain-Action latest main before Sprint 75: `be5a40e Harden external security permissions and fork safety`
- Sprint 70 command matrix passed
- Sprint 71 retrieval quality passed
- Sprint 72 verify productionized
- Sprint 73 fix productized
- Sprint 74 security/fork safety passed

## UX Policy

User personas:

- external repository admin
- repo contributor
- operator/developer

Supported commands:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`

Unsupported commands:

- `/repobrain status`
- `/repobrain doctor`
- `/repobrain fix-lite`

Issue vs PR scope:

- issue: help/ask/locate/explain supported
- issue review/verify/fix: scoped unsupported or safe guidance
- PR ask/review/verify/fix supported
- verify is informational only
- fix is no-patch/no-mutation governance only

## Docs Created And Updated

Created:

- `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- `docs/commands/REPOBRAIN_COMMANDS.md`
- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

Updated:

- `README.md`
- `docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md`
- `docs/USER_GUIDE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/EXTERNAL_MODE.md`
- `docs/REPO_BOUNDARY_CONTRACT.md`
- `docs/onboarding/permissions.md`
- `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`

## Troubleshooting Coverage

| Failure | Cause | User-visible symptom | Fix | Tested or guarded by |
|---|---|---|---|---|
| action not found | private action access or Actions policy too strict | `Unable to resolve action ... repository not found` | enable private action access, allow external actions, check exact ref | `tests/test_external_onboarding_ux_docs.py` |
| missing token | `TOPOCORE_V6_REPO_TOKEN` not configured | private checkout fails before RepoBrain starts | create token and add repo secret | `tests/test_external_onboarding_ux_docs.py` |
| private checkout failed | token access/ref problem | setup fails before backend execution | fix token/repo access and rerun | `tests/test_external_onboarding_ux_docs.py` |
| verify `NOT_RUN` | no concrete checks/statuses/workflow runs observed | informational verify report | inspect limitations and check setup | `tests/test_external_onboarding_ux_docs.py` |
| fix `BLOCKED_BY_SAFETY` | mutation request | no-patch safety response | ask for proposal/governance only | `tests/test_external_onboarding_ux_docs.py` |
| review/verify/fix in issue | unsupported scope | issue-safe guidance | run in PR context | `tests/test_external_onboarding_ux_docs.py` |

## Diagnostic UX Review

No runtime output markdown changes were made in Sprint 75.
The main UX problem was documentation fragmentation, not a rendering bug.

Deferred noisy areas:

- deeper output compaction for secondary diagnostics if future users still report noise

## Optional Live UX Smoke

Not run in Sprint 75.
Reason: the sprint focus was docs consolidation and static truth alignment, not another command matrix.

## Tests And Static Guards

Added:

- `tests/test_external_onboarding_ux_docs.py`

Updated:

- `tests/test_external_security_permissions_fork_safety.py`
- `tests/test_github_app_onboarding_docs.py`
- `tests/test_repobrain_community_removed_from_product.py`

## Defects And Gaps

Fixed now:

- active external onboarding was fragmented across several docs
- README understated supported commands
- troubleshooting truth was not centralized
- unsupported command spellings were not documented in one place

Deferred:

- some historical internal docs still mention old surfaces, but they are not active user-facing install docs
- no live UX smoke evidence was collected in this sprint

Not defects:

- verify remains informational only
- fix remains no-patch/no-mutation only

## Product Status

`UX_ONBOARDING_TROUBLESHOOTING_PASSED`

## Next Step

Sprint 76 - Release Candidate and Marketplace/Public Readiness Assessment

## Non-Goals

- no v5
- no repobrain-community
- no patch/autofix
- no runtime policy change
- no production/Marketplace switch yet
- no RepoBrain-created branch/commit/PR behavior
