# Sprint 90 Decisive Installed-Package Proof

## 1. Purpose

Sprint 90 verifies the owner-issued artifact token and runs the decisive external `installed_package` proof after the authorization gate is complete.

It does not make `RepoBrain-Action` public.

## 2. Baseline

- latest main before Sprint 90:
  - `3fffeba Record owner token proof blocked state`
- Sprint 89 status:
  - `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- prior blocker:
  - missing `TOPOCORE_V6_ARTIFACT_TOKEN`

## 3. Token / Credential State

- secret name:
  - `TOPOCORE_V6_ARTIFACT_TOKEN`
- present:
  - yes
- scope summary:
  - target private repo: `alexworkingai/topocore`
  - minimum intended permission: `Actions: read`
  - write scopes: none
- expiration and rotation:
  - required
- values printed:
  - no
- owner action completed:
  - yes

## 4. Artifact Preflight

Observed preflight steps:

1. artifacts listed
2. target artifact found
3. artifact downloaded
4. SHA-256 sidecar verified
5. wheel located
6. wheel installed
7. `topocore_v6` imported
8. `run_audit_score_v1` detected
9. `topocore.audit_score.v1` detected

Sprint 90 result:

- workflow branch: `codex/sprint-90-installed-package-proof`
- doctor proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749906900`
- artifacts listed: yes
- target artifact found: yes
- artifact downloaded: yes
- digest verified: yes
- wheel installed: yes
- package imported: yes
- capability detected: yes
- contract detected: yes
- result:
  - `INSTALLED_PACKAGE_PREFLIGHT_STATUS=PASS`

## 5. External Installed-Package Proof

- repo used:
  - `alexworkingai/Elen-MCP-v.2.2.0`
- workflow branch:
  - `codex/sprint-90-installed-package-proof`
- issue URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/37`
- run URLs:
  - doctor:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749906900`
  - status:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749940756`
  - audit:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749942289`
  - score:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749943941`
  - ask initial proof run:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749945553`
  - ask refreshed after RepoBrain `main` docs update:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26750529959`
- runtime mode requested:
  - `installed_package`
- runtime mode used:
  - `installed_package`
- doctor result:
  - `PASS`
  - dependency mode: `installed_private_package`
- status result:
  - `success`
  - dependency mode: `installed_private_package`
- audit result:
  - `v6-enriched scoring`
  - backend: `auto -> v6`
  - fallback: `no / none`
  - final score: `77 / 100 GOOD`
- score result:
  - `v6-enriched scoring`
  - backend: `auto -> v6`
  - fallback: `no / none`
  - final score: `77 / 100 GOOD`
- ask result:
  - initial run succeeded but still surfaced the pre-merge blocked readiness docs snapshot
  - refreshed run succeeded with:
    - `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`
    - `INSTALLED_PACKAGE_LIVE_PROOF_PASSED`
    - next step: explicit owner approval
- private_checkout avoided:
  - yes
- source checkout avoided:
  - yes for private TopoCore source
- safety result:
  - no token values printed
  - no TopoCore source exposure
  - no private-path exposure in user-facing output
  - no mutation

## 6. Control Smoke

- control issue:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/37`
- control doctor run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749992255`
- control status run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749993658`
- control audit run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749995358`
- control score run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749997090`
- result:
  - controlled `private_checkout` beta path remains green
  - audit and score stayed `v6-enriched scoring`
  - no secret or source exposure
  - no mutation

## 7. Public Readiness Decision

- `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`

Historical blocked states retained for traceability:

- `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
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

- decisive installed-package runtime proof is complete
- remaining gate is explicit owner approval for the public visibility switch and selected partner pilot

## 9. Next Step

If ready:
- Sprint 91 - Owner-Approved Public Visibility Switch and Selected Partner Pilot Kickoff.

If blocked later by a new signal:
- Sprint 91 should target the exact newly observed blocker rather than reopening installed-package proof ambiguity.

## 10. Non-Goals

- no public switch
- no Marketplace
- no public RC tag unless separately approved
- no v5
- no repobrain-community
- no patch/autofix
- no TopoCore source exposure
- no Microsoft partnership claim
