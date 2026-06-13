# GitHub App Private Control Repo Setup

## Control Repo Role

The private RepoBrain control repo is the runtime location for the Sprint 94D worker foundation. It should:
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
Sprint 94D adds the private worker foundation that consumes those queue markers.

The private control repo is where Sprint 94D should:
- discover queued comments
- validate GitHub App installation identity
- load repository and PR context through the installation token
- run private TopoCore
- publish the final public-safe result comment

Final score and audit reports do not come from Sprint 94C alone.

## Private Control Worker Setup

Private control worker setup:
- store GitHub App private key only in the private control repo
- mint installation token inside the private control repo
- run queue worker in private control context only
- configure TopoCore entrypoint only in the private control repo
- never put TopoCore credentials in partner repo
- never put GitHub App private key in public `RepoBrain-Action`
- run in dry-run or stub mode first
- then run against trusted partner repos

## Minimal Operator Checklist

1. Confirm Sprint 94C partner workflow creates queue markers.
2. Confirm GitHub App is installed on the selected repository.
3. Confirm control repo has App ID and private key.
4. Confirm installation token can be minted.
5. Run the auth check workflow.
6. Run the queue worker in dry-run.
7. Run the queue worker with stub TopoCore.
8. Run the queue worker with the real private TopoCore entrypoint.
9. Verify the public result comment.
10. Verify no token, path, or private data leakage.

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
