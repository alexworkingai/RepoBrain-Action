# Sprint 89 Owner Token Installed-Package Proof

## 1. Purpose

Sprint 89 verifies whether the owner-issued artifact credential exists and reruns the decisive external `installed_package` proof only if that prerequisite is complete.

It does not make `RepoBrain-Action` public.

## 2. Baseline

- latest main before Sprint 89:
  - `df97d1f Record installed package authorization proof evidence`
- Sprint 88 status:
  - `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- blocker:
  - missing `TOPOCORE_V6_ARTIFACT_TOKEN`

## 3. Token / Credential

- secret name:
  - `TOPOCORE_V6_ARTIFACT_TOKEN`
- intended type:
  - fine-grained PAT or GitHub App installation token
- minimum intent:
  - read private Actions artifact from `alexworkingai/topocore`
  - `Actions: read`
- expiration and rotation:
  - required
- values printed:
  - no
- owner action completed:
  - no

## 4. Artifact Access Preflight

Expected preflight path:

1. list artifacts
2. find `topocore-v6-runtime-wheel`
3. download artifact
4. verify SHA-256 sidecar
5. install `topocore_v6-0.30.0-py3-none-any.whl`
6. import `topocore_v6`
7. detect `run_audit_score_v1`
8. detect `topocore.audit_score.v1`

Sprint 89 result:

- the required secret was still absent at startup
- no artifact preflight was re-run
- no new proof evidence is claimed

## 5. External Installed-Package Proof

- repo used:
  - `alexworkingai/Elen-MCP-v.2.2.0`
- workflow branch:
  - not recreated in Sprint 89 because the startup hard stop triggered first
- issue URL:
  - none in Sprint 89
- runtime mode requested:
  - `installed_package`
- runtime mode used:
  - not reached
- private_checkout avoided:
  - yes by policy
- source checkout avoided:
  - yes by policy for the intended proof path
- doctor/status/audit/score/ask result:
  - not rerun in installed-package mode
- backend evidence:
  - not reached
- safety result:
  - no token values printed
  - no source exposure
  - no private-path exposure

## 6. Control Surface

- Sprint 88 control smoke remains the latest live runtime evidence on the known-good path
- no Sprint 89 change was made to the normal controlled `private_checkout` path

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

- public visibility remains blocked until the owner issues the minimum-scope artifact credential and the external installed-package proof reaches real `v6`

## 9. Next Step

If ready:
- Sprint 90 - Owner-Approved Public Visibility Switch and Selected Partner Pilot Kickoff.

If blocked:
- Sprint 90 should target owner token issuance, actual artifact preflight, and the decisive installed-package rerun.

## 10. Non-Goals

- no public switch
- no Marketplace
- no public RC tag unless separately approved
- no v5
- no repobrain-community
- no patch/autofix
- no TopoCore source exposure
- no Microsoft partnership claim
