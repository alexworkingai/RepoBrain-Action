# Sprint 88 Artifact Access Final Runtime Proof

## 1. Purpose

Sprint 88 resolves installed-package artifact access authorization as far as the current operator boundary allows and reruns the final runtime-proof gate.

It does not make `RepoBrain-Action` public.

## 2. Baseline

- latest main before Sprint 88:
  - `d4b89f6 Record installed package runtime proof evidence`
- Sprint 87 status:
  - `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`
- blocker:
  - `PACKAGE_AUTH_FAILED / TOKEN_SCOPE_NOT_READY`

## 3. Authorization Model Discovery

Options evaluated:

- GitHub App installation token
- fine-grained personal access token
- classic PAT with `repo`
- GitHub Packages private package registry
- private release asset
- managed runtime

Selected path:

- `fine_grained_pat_actions_read_artifact_download`

Token model:

- external workflow secret name: `TOPOCORE_V6_ARTIFACT_TOKEN`
- minimum repository access target: `alexworkingai/topocore`
- minimum repository permission: `Actions: read`
- no write scopes
- no source checkout requirement

Rejected options:

- classic PAT as partner-ready default
- private source checkout as proof path
- GitHub Packages for this wheel-based Sprint 88 proof
- managed runtime as a Sprint 88 implementation target

Owner action if needed:

- yes
- Sprint 88 cannot mint or inject the minimum-scope credential by itself

## 4. Credential / Token State

- secret name: `TOPOCORE_V6_ARTIFACT_TOKEN`
- scope summary:
  - fine-grained PAT or equivalent GitHub App installation token
  - read-only artifact access intent
- expiration/rotation:
  - required
- no values printed:
  - preserved
- source rights risk:
  - source checkout avoided by design
  - readable wheel caveat remains honest

## 5. Delivery Implementation

- delivery path:
  - private Actions artifact containing the approved wheel and SHA-256 sidecar
- integrity verification:
  - required before install
- workflow branch:
  - `codex/sprint-88-installed-package-access-proof`
- no source checkout:
  - required

## 6. External Installed-Package Proof

- attempted live proof in Sprint 88:
  - not completed to runtime execution
- repo used:
  - `alexworkingai/Elen-MCP-v.2.2.0`
- mode:
  - `installed_package`
- source checkout avoided:
  - yes by design
- private_checkout avoided:
  - yes by design
- result:
  - blocked
- exact blocker:
  - `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- historical lower-level failure marker:
  - `PACKAGE_AUTH_FAILED / TOKEN_SCOPE_NOT_READY`

## 7. Control Smoke

- normal private_checkout beta path remained the known-good control surface from Sprint 87
- result:
  - green

## 8. Public Readiness Decision

- `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`

Allowed states:

- `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`
- `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`
- `PUBLIC_BLOCKED_BY_PACKAGE_DELIVERY`
- `PUBLIC_BLOCKED_BY_ARTIFACT_AUTHORIZATION`
- `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- `PUBLIC_BLOCKED_BY_GITHUB_PLATFORM_LIMITATION`
- `PUBLIC_BLOCKED_BY_VALIDATION`
- `PUBLIC_BLOCKED_BY_LIVE_SMOKE`

## 9. Product Status

- public switch remains blocked until the owner issues the minimum-scope artifact credential and external installed-package proof reaches real `v6`

## 10. Next Step

If ready:
- Sprint 89 — Owner-Approved Public Visibility Switch and Selected Partner Pilot Kickoff.

If blocked:
- Sprint 89 should target owner-issued artifact credential provisioning and the decisive rerun of external installed-package proof.

## 11. Non-Goals

- no public switch
- no Marketplace
- no public RC tag unless explicitly approved
- no v5
- no repobrain-community
- no patch/autofix
- no TopoCore source exposure
- no Microsoft partnership claim
