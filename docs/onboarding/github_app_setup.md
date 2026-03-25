# RepoBrain GitHub App Setup (Foundation)

## Scope

This document defines the Sprint 52 foundation-only onboarding path:

- GitHub App-first installation assumptions
- required permissions and configuration inputs
- selected-repository rollout defaults
- first-run install readiness validation

It does **not** claim full Marketplace/public distribution readiness yet.

## Installation Model

RepoBrain should be operated with a GitHub App-first trust model:

1. Install the GitHub App to the target organization/repository.
2. Prefer **selected repositories** over org-wide rollout while validating.
3. Configure App installation inputs (ID, installation ID, private key, webhook secret).
4. Use RepoBrain workflow + deferred privileged publisher path as already established.

## Required Configuration Inputs

Set these for App-first readiness checks:

- `RB_GH_APP_ID`
- `RB_GH_APP_INSTALLATION_ID`
- one of:
  - `RB_GH_APP_PRIVATE_KEY` (recommended)
  - `RB_GH_APP_PRIVATE_KEY_PATH`
- `RB_GH_APP_WEBHOOK_SECRET` (recommended before external webhook exposure)
- `RB_GH_APP_REPOSITORY_SELECTION` (`selected` recommended, `all` allowed)
- `RB_GH_APP_SELECTED_REPOS` (comma-separated list when selection mode is `selected`)

See `docs/onboarding/permissions.md` for permission rationale.

## Selected Repository Rollout (Recommended)

Default rollout mode for safety:

- `RB_GH_APP_REPOSITORY_SELECTION=selected`
- `RB_GH_APP_SELECTED_REPOS=owner/repo-a,owner/repo-b`

This keeps first adoption bounded and auditable before broader rollout.

## Readiness Validation

Run:

```bash
python scripts/check_install_readiness.py \
  --workflow .github/workflows/repobrain.yml \
  --output-json artifacts/onboarding/repobrain_install_readiness.json \
  --output-md artifacts/onboarding/repobrain_install_readiness.md
```

Possible overall statuses:

- `READY`
- `MISSING_PERMISSION`
- `MISSING_CONFIG`
- `UNSUPPORTED_SETUP`

The checker includes explicit next steps for each failing condition.

## Workflow Artifact

The `RepoBrain` workflow now uploads onboarding readiness artifacts:

- artifact name: `repobrain-install-readiness`
- files:
  - `artifacts/onboarding/repobrain_install_readiness.json`
  - `artifacts/onboarding/repobrain_install_readiness.md`

Use this artifact to confirm operator readiness without changing normal Ask/Review/Fix comment surfaces.
