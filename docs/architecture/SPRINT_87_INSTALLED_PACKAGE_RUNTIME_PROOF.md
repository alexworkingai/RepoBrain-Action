# Sprint 87 Installed Package Runtime Proof

## 1. Purpose

- Sprint 87 proves external installed-package runtime delivery and hardens ask operational quality.
- It does not make RepoBrain-Action public.

## 2. Baseline

- latest main before Sprint 87: `bece7b7 Record enterprise P0 hardening live evidence`
- Sprint 86 status: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`
- installed package blocker: external package/artifact delivery was not yet operationally proven

## 3. Delivery Design

- selected delivery path: `temporary_controlled_artifact_proof`
- token model: scoped private artifact access only
- artifact integrity: wheel artifact plus SHA-256 verification
- source checkout avoidance: required for private TopoCore source in the external workflow
- wheel readability caveat: plain Python wheel readability remains an honest caveat

## 4. Private Runtime Artifact

- artifact type: private wheel artifact
- version/hash if safe: pending final live evidence update
- capability present: expected
- validation result: pending final live evidence update
- no source details are recorded here

## 5. External Workflow Proof

- repo used: `alexworkingai/Elen-MCP-v.2.2.0`
- branch/PR if any: pending final live evidence update
- workflow mode: `installed_package`
- private_checkout avoided: target `yes`
- source checkout avoided: target `yes` for private TopoCore source
- commands run: doctor, status, audit, score, ask
- run URLs: pending final live evidence update
- result: pending final live evidence update

## 6. Ask Operational Quality

- problem: operational ask questions returned a weaker review-style synthesis than needed
- implementation: detect operational status intent and answer with workflow/runtime/public-readiness status from safe diagnostics and release docs
- examples/tests: covered in Sprint 87 focused tests
- live ask result: pending final live evidence update

## 7. Public Readiness Decision

- pending final live evidence update
- allowed outcomes:
  - `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`
  - `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`
  - `PUBLIC_BLOCKED_BY_PACKAGE_DELIVERY`
  - `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`
  - `PUBLIC_BLOCKED_BY_ARTIFACT_SECURITY`
  - `PUBLIC_BLOCKED_BY_VALIDATION`
  - `PUBLIC_BLOCKED_BY_LIVE_SMOKE`

## 8. Product Status

- pending final live evidence update

## 9. Next Step

- if ready: Sprint 88 - Owner-Approved Public Visibility Switch and Selected Partner Pilot Kickoff
- if blocked: Sprint 88 targets the exact remaining blocker

## 10. Non-Goals

- no public switch
- no Marketplace
- no public RC tag unless explicitly approved
- no v5
- no repobrain-community
- no patch/autofix
- no TopoCore source exposure
- no Microsoft partnership claim
