# Partner Runtime Access Runbook

## Purpose

This runbook defines the selected partner runtime access model for RepoBrain.

## Selected Partner Access Model

- per-partner token or equivalently scoped credential
- read-only access
- explicit expiration
- rotation required
- revocation required

## Credential Requirements

- one credential per partner or per partner-controlled environment
- no shared broad PAT
- no shared owner token
- no uncontrolled source-repo access

## Rotation

- define expiration before issuance
- rotate on schedule
- rotate immediately after suspected exposure

## Revocation

- revoke on incident
- revoke on offboarding
- revoke if policy or scope is violated

## Incident Response

1. revoke the affected partner credential
2. inspect access logs and issuance records
3. rotate any related internal credentials if needed
4. pause partner runtime access until scope is revalidated

## What Not To Give Partners

- TopoCore source-repo collaborator access unless explicitly approved
- owner token
- broad PAT
- TopoCore source license

## Installed Private Package Delivery Model

- preferred selected-partner path
- deliver a private runtime package or approved runtime artifact
- keep consumer repositories free of private source checkout by default
- operational live-proof status is tracked separately in `docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md`
- Sprint 86 result:
  - local package/install proof passed
  - external delivery/install proof was still blocked
- Sprint 87 result:
  - private workflow artifact proof path was built successfully
  - external proof still blocked on `TOKEN_SCOPE_NOT_READY`
- Sprint 88 result:
  - selected authorization path is `fine_grained_pat_actions_read_artifact_download`
  - exact remaining gate is `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
  - do not issue partner rollout approval for this mode until `TOPOCORE_V6_ARTIFACT_TOKEN` exists and the external proof reaches real `v6` without source checkout
- Sprint 89 result:
  - the owner-token gate was rechecked before any new proof attempt
  - `TOPOCORE_V6_ARTIFACT_TOKEN` was still missing in the external consumer repository
  - no decisive installed-package rerun is claimed until the owner-side secret exists
- Sprint 90 result:
  - the owner-token gate was rechecked again before any new proof attempt
  - `TOPOCORE_V6_ARTIFACT_TOKEN` was still missing in the external consumer repository
  - no decisive installed-package rerun is claimed until the owner-side secret exists

## Package Caveat

- a plain Python wheel may still contain readable implementation
- this is acceptable only for selected partner testing under scoped access and explicit approval

## Stronger Future Options

- managed runtime
- compiled or signed runtime artifact
- GitHub App installation token instead of a fine-grained PAT for stronger lifecycle control

## Operational Checklist

1. issue per-partner credential
2. confirm read-only scope
3. confirm expiration
4. confirm revocation owner
5. confirm partner received setup instructions
6. confirm no TopoCore source rights were granted
7. confirm the credential can retrieve the approved private runtime artifact or package without source checkout
