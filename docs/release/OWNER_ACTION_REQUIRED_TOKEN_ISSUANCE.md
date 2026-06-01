# Owner Action Required Token Issuance

## Purpose

This document records the exact owner-side action that was required to unblock Sprint 88 through Sprint 90 installed-package runtime proof, and the fact that the owner action is now complete.

## Required Credential

- secret name created in `alexworkingai/Elen-MCP-v.2.2.0`: `TOPOCORE_V6_ARTIFACT_TOKEN`
- preferred credential type: fine-grained personal access token
- acceptable stronger alternative: GitHub App installation token

## Exact Minimum Scope

For the fine-grained PAT path:

- resource owner: `alexworkingai`
- repository access: `Only select repositories`
- selected repository: `alexworkingai/topocore`
- repository permission: `Actions: Read`
- no write permissions
- no `Contents: read` unless an alternate delivery path is explicitly approved

For the GitHub App path:

- install only where needed
- repository selection limited to `alexworkingai/topocore`
- minimum repository permission: `Actions: read`
- no source-repo collaborator grant

## Expiration

- expiration is required
- shortest practical expiration is preferred for the proof token
- rotate before partner rollout if the proof token ages out or is reused

## Target Repository and Secret Placement

- target secret location: `alexworkingai/Elen-MCP-v.2.2.0`
- target secret name: `TOPOCORE_V6_ARTIFACT_TOKEN`
- do not print the token value in logs, docs, workflow output, or chat

## Why Existing Token Was Not Enough

- the older external token path supported controlled private source checkout scenarios
- it did not provide the required cross-repo private Actions artifact read for the approved installed-package proof path
- Sprint 87 therefore failed with `PACKAGE_AUTH_FAILED`
- exact blocker label became `TOKEN_SCOPE_NOT_READY`

## How It Was Verified

1. verify the secret `TOPOCORE_V6_ARTIFACT_TOKEN` exists in `alexworkingai/Elen-MCP-v.2.2.0`
2. rerun the installed-package proof workflow branch after the secret exists
3. confirm private TopoCore source checkout is still avoided
4. confirm artifact digest verification passes
5. confirm `/repobrain doctor` and `/repobrain status` report `installed_package`
6. confirm `/repobrain audit` and `/repobrain score` resolve `auto -> v6` with fallback `no / none`

## What Not To Grant

- no broad classic PAT as partner-ready default
- no shared owner token
- no source-repo collaborator access unless separately approved
- no write scopes
- no TopoCore source rights

## Current Sprint 90 State

- owner action required: `no`
- owner action completed: `yes`
- exact historical blocker state: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- Sprint 90 verification confirmed the secret now exists without printing its value
- decisive installed-package proof was rerun and passed
- public visibility is no longer blocked by artifact-token issuance; the remaining gate is explicit owner approval for the public switch and selected partner pilot
