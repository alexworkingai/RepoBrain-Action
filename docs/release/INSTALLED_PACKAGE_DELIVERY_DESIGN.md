# Installed Package Delivery Design

## Purpose

This document records the Sprint 87 delivery design for proving external `installed_package` runtime mode without `private_checkout`.

## Selected Delivery Path

- selected delivery path: `temporary_controlled_artifact_proof`
- Sprint 87 proof uses a private TopoCore workflow artifact consumed by an external workflow with `RB_TOPOCORE_V6_RUNTIME_MODE=installed_package`
- the proof workflow downloads the approved wheel artifact plus SHA-256 sidecar, verifies the hash, and then installs the wheel in the external runner
- this is acceptable as a runtime-proof path because it avoids private source checkout in the consumer repository while keeping delivery under owner-controlled scope

## Rejected Alternatives

- `GitHub Packages / private package registry`
  - rejected for Sprint 87 because the package delivery channel is not yet operationally configured for this pilot
- `private source checkout`
  - rejected because Sprint 87 must prove installed-package delivery without `private_checkout`
- `managed runtime`
  - rejected for Sprint 87 because it is future architecture, not current partner-pilot plumbing

## Token Model

- use a scoped private credential for artifact access only
- do not use a shared broad PAT
- do not expose token values in workflow logs
- keep per-partner or equally narrow runtime access as the long-term partner model
- Sprint 87 finding: the currently available scoped credential could not read the private GitHub Actions artifact, so the exact blocker became `TOKEN_SCOPE_NOT_READY`

## Artifact/Package Integrity

- build a wheel artifact in the private TopoCore repository
- publish a SHA-256 sidecar file with the wheel artifact
- verify the downloaded artifact hash before installation in the external workflow
- keep artifact acquisition read-only and avoid source-repo checkout in the consumer workflow

## Source Checkout Avoided

- source checkout avoided: `yes` for the private TopoCore repository in the external proof workflow
- consumer repository checkout remains normal because RepoBrain still analyzes the consumer repo
- `.topocore-v6` source checkout must not appear in the installed-package proof path

## Wheel Readability Caveat

- a plain Python wheel may still contain readable implementation files
- Sprint 87 does not claim stronger secrecy than that
- this is acceptable only for controlled selected-partner proof, not for broad public distribution or Marketplace delivery

## Partner Rollout Implication

- if token-scoped artifact or package delivery becomes operational, selected partner rollout can proceed on an owner-approved, controlled installed-package path
- until then, public visibility remains blocked by token-scoped runtime delivery proof

## Production Hardening Next Step

- move from temporary controlled artifact proof to a stable private package or artifact delivery channel
- keep integrity checks and narrow credentials
- consider managed runtime or stronger artifact hardening if broader distribution is needed
