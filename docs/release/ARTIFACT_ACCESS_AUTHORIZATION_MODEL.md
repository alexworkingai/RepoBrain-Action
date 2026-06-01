# Artifact Access Authorization Model

## Purpose

This document records the Sprint 88 decision for external access to the approved private TopoCore runtime artifact without private source checkout.

## Current Blocker

- previous blocker: `TOKEN_SCOPE_NOT_READY`
- Sprint 88 clarification: the remaining gate is no longer runtime ambiguity
- the remaining gate is issuance of a GitHub-supported minimum-scope credential for external artifact retrieval

## Options Evaluated

### Option A: GitHub App installation token

- can be scoped to selected repositories
- can be scoped to minimum repository permissions
- GitHub documents installation tokens as valid for private Actions artifact endpoints when the app has `Actions: read`
- strongest long-term operational model among GitHub-native options
- not provisioned in Sprint 88

### Option B: Fine-grained personal access token

- GitHub documents fine-grained PATs as valid for private Actions artifact endpoints with repository permission `Actions: read`
- can be limited to `alexworkingai/topocore`
- faster near-term pilot path than creating a new GitHub App
- still requires explicit owner issuance and expiration management

### Option C: Classic PAT with `repo`

- GitHub documents classic PATs with `repo` as valid for private Actions artifact endpoints
- too broad for selected-partner runtime delivery by default
- not accepted as the partner-ready path
- only acceptable as an explicitly approved temporary diagnostic, which Sprint 88 does not use

### Option D: GitHub Packages private package registry

- package permissions are workable in some GitHub registries
- not selected for Sprint 88
- GitHub Packages does not provide a first-class Python package registry for this wheel-based proof path
- package auth guidance also leans on package-specific access management or classic package scopes, which is not a better short-term fit than artifact read

### Option E: Private release asset

- technically possible with a token
- broader repository/release coupling than Actions artifact read
- not selected because artifact read with `Actions: read` is narrower

### Option F: Managed runtime

- future architecture option
- not implemented in Sprint 88

## Selected Sprint 88 Path

- selected path: `fine_grained_pat_actions_read_artifact_download`
- preferred longer-term hardening path: GitHub App installation token with the same narrow repository intent
- reason for selecting fine-grained PAT now:
  - narrower than classic `repo`
  - operationally simpler than introducing a new GitHub App during this sprint
  - sufficient on paper for the private Actions artifact endpoints RepoBrain needs

## Token Permissions

Minimum target shape:

- repository access: `alexworkingai/topocore` only
- repository permission: `Actions: read`
- metadata visibility: repository metadata only
- no write scopes
- no collaborator grant
- no source checkout requirement

## Expiration and Rotation

- expiration required
- short-lived token preferred
- rotate on first use for partner rollout if the proof token was issued earlier
- rotate immediately on suspected exposure
- revoke on offboarding or incident

## Source Checkout Avoidance

- external consumer workflow must not checkout private TopoCore source
- external consumer workflow must not create `.topocore-v6`
- runtime installation must come from the approved wheel artifact only
- digest verification must run before install

## Source-Rights Risk

- selected artifact path avoids private source checkout
- selected artifact path does not grant source-repo collaborator access
- honest caveat: a normal Python wheel may still contain readable implementation files
- Sprint 88 does not claim stronger secrecy than that

## Rejected Options

- classic PAT as default partner credential
- private source checkout as proof path
- GitHub Packages for this wheel-based proof sprint
- managed runtime as a Sprint 88 implementation target

## Owner Actions Required

- owner must issue the selected minimum-scope credential or approve an equivalent GitHub App installation
- owner must store the credential in `alexworkingai/Elen-MCP-v.2.2.0` as `TOPOCORE_V6_ARTIFACT_TOKEN`
- owner must avoid granting a broad PAT unless explicitly authorizing a temporary diagnostic-only exception

## Final Decision

- `ARTIFACT_ACCESS_OWNER_ACTION_REQUIRED`
- Sprint 88 resolves the authorization model but does not complete live installed-package proof because the minimum-scope credential has not yet been issued into the external workflow.

## References

- GitHub Actions artifacts REST API: `https://docs.github.com/en/rest/actions/artifacts`
- GitHub App installation tokens: `https://docs.github.com/en/enterprise-cloud@latest/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app`
- GitHub Packages permissions: `https://docs.github.com/en/packages/learn-github-packages/about-permissions-for-github-packages`
- Sharing private actions/workflows across repos: `https://docs.github.com/en/actions/how-tos/reuse-automations/share-across-private-repositories`
