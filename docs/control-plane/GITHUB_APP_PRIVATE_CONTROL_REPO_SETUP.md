# GitHub App Private Control Repo Setup

## Control Repo Role

The future private RepoBrain control repo will eventually:
- hold GitHub App credentials
- mint installation tokens
- discover installed repositories
- process the GitHub-native request queue
- run private TopoCore
- post public-safe results back to partner repos

This file is a setup guide and template only.
It does not create a private repo from `RepoBrain-Action`.

## Required Secrets And Variables

Secrets:
- `REPOBRAIN_GITHUB_APP_PRIVATE_KEY`

Variables or secrets:
- `REPOBRAIN_GITHUB_APP_ID`

Optional:
- `REPOBRAIN_ALLOWED_INSTALLATION_OWNER`
- `REPOBRAIN_BETA_MODE`
- `REPOBRAIN_LOG_LEVEL`

Must not store:
- partner personal access tokens
- owner-generated onboarding tokens
- TopoCore credentials in partner repos
- raw installation tokens in artifacts or logs

## Token Generation Strategy

Recommended strategy:
- use GitHub App authentication inside the private control workflow
- mint a short-lived installation token
- use the installation token only for selected installed repos
- never print the token
- never persist the token to artifacts

Guidance:
- prefer GitHub-native or minimal audited approaches
- do not depend on paid third-party services
- do not expose Authorization headers, bearer strings, JWTs, or private keys

## Queue Processing Relationship

Sprint 94C adds the public-side queue marker and contract only.

The private control repo is where Sprint 94D should:
- discover queued comments
- validate GitHub App installation identity
- load repository and PR context through the installation token
- run private TopoCore
- publish the final public-safe result comment

Final score and audit reports do not come from Sprint 94C alone.

## Minimal Validation Target For 94B

The private control repo auth layer should eventually prove:
- App ID configured
- private key configured
- installation token can be minted
- installed repositories can be listed
- selected repo identity can be resolved

Sprint 94B in `RepoBrain-Action` only provides:
- docs
- templates
- contracts

## Failure Statuses

- `GITHUB_APP_ID_MISSING`
- `GITHUB_APP_PRIVATE_KEY_MISSING`
- `GITHUB_APP_TOKEN_MINT_FAILED`
- `GITHUB_APP_NO_INSTALLATIONS_FOUND`
- `GITHUB_APP_REPO_NOT_INSTALLED`
- `GITHUB_APP_PERMISSION_MISSING`
- `GITHUB_APP_TOKEN_LEAKAGE_DETECTED`
