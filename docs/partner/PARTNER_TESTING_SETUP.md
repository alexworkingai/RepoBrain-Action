# Partner Testing Setup

## What RepoBrain Is

RepoBrain is a GitHub-native Repository Intelligence and Quality Scoring Platform delivered through GitHub Actions.

## What Partners Are Testing

Selected partners are testing:

- repository-wide audit quality
- compact score quality
- setup diagnostics
- runtime/status diagnostics
- ask-style repository guidance
- the selected `installed_private_package` runtime path only after it is operationally proven

## What RepoBrain Does Not Do

- it does not expose TopoCore source rights
- it does not apply patches or autofixes
- it does not create branches, commits, or PRs
- it does not give merge approval
- it does not give security approval

## Prerequisites

- GitHub repository admin access for the partner repository
- permission to use external GitHub Actions
- authorized RepoBrain public visibility after owner approval
- authorized TopoCore runtime access for the selected partner
- BYO-LLM or user-paid model/provider access if needed

## Repository Admin Steps

1. confirm GitHub Actions use is allowed
2. add the required runtime credential using placeholders only
3. install the RepoBrain workflow in the partner repository
4. verify the workflow keeps read-mostly permissions

## Workflow Install

- use the canonical install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- use the example workflow only as a bounded reference
- keep runtime mode explicit

## Permissions Baseline

- `contents: read`
- `models: read` when applicable
- `checks: read`
- `statuses: read`
- `actions: read`
- `issues: write`
- `pull-requests: read`

## Runtime Mode

Preferred selected-partner mode:

- `installed_private_package`

This is preferred because it avoids source checkout into the consumer repository workspace.
Current live-proof status is tracked in `docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md`.
Sprint 86 truth:

- local packaging truth passed
- external installed-package delivery proof is still blocked
- partner onboarding on this mode must wait until that blocker is cleared

Sprint 88 truth:

- the supported authorization model is now selected
- the remaining gate is `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- partner onboarding on this mode must wait until `TOPOCORE_V6_ARTIFACT_TOKEN` is issued with the minimum required scope and the external proof reaches real `v6`

## `private_checkout`

- beta-only fallback
- not preferred for selected partner testing
- acceptable only in tightly controlled cases

## Secret and Runtime Credential Setup

Use placeholders only:

- `<PARTNER_RUNTIME_TOKEN>`
- `<PRIVATE_TOPOCORE_RUNTIME_ARTIFACT>`
- `<MODEL_PROVIDER_CONFIGURATION>`

Do not store shared owner credentials in partner repositories.

## BYO-LLM / User-Paid Model

Partners are expected to use their own model/provider access according to the documented BYO-LLM model.

## First Smoke Commands

1. `/repobrain doctor`
2. `/repobrain status`
3. `/repobrain audit`
4. `/repobrain score`
5. `/repobrain ask`

## Expected Outputs

- doctor should pass or produce a clear non-blocking warning
- status should show the supported command surface and runtime mode truth
- audit should produce a full repository report
- score should produce a compact summary of the same guarded audit engine
- ask should answer a bounded repository question
- if installed-package mode is requested before the runtime package/artifact is really deliverable, doctor and status should warn truthfully and audit/score should stay on static fallback rather than falsely claiming `v6`

## Troubleshooting

- start with `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- use `/repobrain doctor` first when setup is unclear
- use `/repobrain audit` when `/repobrain score` is too compact

## Feedback Submission

Use `docs/partner/PARTNER_FEEDBACK_TEMPLATE.md` to report setup friction, output quality, false positives/negatives, and security concerns.
