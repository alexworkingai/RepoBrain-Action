# Sprint 90 Decisive Installed-Package Proof

## 1. Purpose

Sprint 90 verifies whether the owner-issued artifact token now exists and runs the decisive external `installed_package` proof only if that prerequisite is complete.

It does not make `RepoBrain-Action` public.

## 2. Baseline

- latest main before Sprint 90:
  - `3fffeba Record owner token proof blocked state`
- Sprint 89 status:
  - `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- blocker:
  - missing `TOPOCORE_V6_ARTIFACT_TOKEN`

## 3. Token / Credential State

- secret name:
  - `TOPOCORE_V6_ARTIFACT_TOKEN`
- present:
  - no
- scope summary:
  - target private repo: `alexworkingai/topocore`
  - minimum intended permission: `Actions: read`
  - write scopes: none
- expiration and rotation:
  - required
- values printed:
  - no
- owner action completed:
  - no

## 4. Artifact Preflight

Expected preflight path:

1. list artifacts
2. find `topocore-v6-runtime-wheel`
3. download artifact
4. verify SHA-256 sidecar
5. locate `topocore_v6-0.30.0-py3-none-any.whl`
6. install wheel
7. import `topocore_v6`
8. detect `run_audit_score_v1`
9. detect `topocore.audit_score.v1`

Sprint 90 result:

- the required secret was still absent at startup
- no artifact preflight was rerun
- no new proof evidence is claimed

## 5. External Installed-Package Proof

- repo used:
  - not rerun in Sprint 90
- workflow branch:
  - not recreated in Sprint 90 because the startup hard stop triggered first
- issue URL:
  - none in Sprint 90
- runtime mode requested:
  - `installed_package`
- runtime mode used:
  - not reached
- doctor/status/audit/score/ask result:
  - not rerun
- backend evidence:
  - not reached
- private_checkout avoided:
  - yes by policy
- source checkout avoided:
  - yes by policy for the intended proof path
- safety result:
  - no token values printed
  - no source exposure
  - no private-path exposure

## 6. Control Smoke

- Sprint 89 and Sprint 88 control evidence remain the latest live green control path
- Sprint 90 did not modify the normal controlled `private_checkout` runtime path

## 7. Public Readiness Decision

- `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`

Ready state once decisive proof succeeds:

- `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`

Allowed blocked states remain:

- `PUBLIC_BLOCKED_BY_TOKEN_PERMISSION`
- `PUBLIC_BLOCKED_BY_ARTIFACT_AUTHORIZATION`
- `PUBLIC_BLOCKED_BY_PACKAGE_DELIVERY`
- `PUBLIC_BLOCKED_BY_ARTIFACT_DIGEST`
- `PUBLIC_BLOCKED_BY_PACKAGE_INSTALL`
- `PUBLIC_BLOCKED_BY_CAPABILITY`
- `PUBLIC_BLOCKED_BY_CONTRACT_REJECTION`
- `PUBLIC_BLOCKED_BY_GITHUB_PLATFORM_LIMITATION`
- `PUBLIC_BLOCKED_BY_VALIDATION`
- `PUBLIC_BLOCKED_BY_LIVE_SMOKE`

## 8. Product Status

- public visibility remains blocked until the owner issues the minimum-scope artifact credential and the decisive external installed-package proof reaches real `v6`

## 9. Next Step

If ready:
- Sprint 91 - Owner-Approved Public Visibility Switch and Selected Partner Pilot Kickoff.

If blocked:
- Sprint 91 should target owner token issuance, actual artifact preflight, and the decisive installed-package rerun.

## 10. Non-Goals

- no public switch
- no Marketplace
- no public RC tag unless separately approved
- no v5
- no repobrain-community
- no patch/autofix
- no TopoCore source exposure
- no Microsoft partnership claim
