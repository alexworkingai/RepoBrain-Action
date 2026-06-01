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
- Sprint 90 result:
  - owner-issued artifact credential was verified present
  - artifact preflight passed
  - external installed-package proof reached real `v6`
  - private TopoCore source checkout remained avoided
  - the remaining gate is explicit owner approval for the public switch and selected partner pilot

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
