# Installed Package Live Proof

## Purpose

This document records the Sprint 86 and Sprint 87 work to prove external `installed_package` runtime mode in a partner-like external workflow without `private_checkout` source checkout.

## Proof Target

- target repository: `alexworkingai/Elen-MCP-v.2.2.0`
- proof issue: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/35`
- target branch for proof workflow: `codex/sprint-87-installed-package-proof`
- goal: external workflow using `RB_TOPOCORE_V6_RUNTIME_MODE=installed_package`

## Workflow Mode

- requested mode: `installed_package`
- selected delivery path: `temporary_controlled_artifact_proof`
- private_checkout avoided: `yes`
- source checkout avoided: `yes` for private TopoCore source checkout

## Runtime Package Source Type

- private build source: TopoCore private workflow artifact
- private workflow run: `https://github.com/alexworkingai/topocore/actions/runs/26719642497`
- artifact name: `topocore-v6-runtime-wheel`
- artifact digest: `sha256:aa70729efa6bb229a7ad559ca1b5c893fa63e680df82e34884f87d366ac8f354`
- package import name: `topocore_v6`
- honest caveat: a normal wheel may still contain readable Python implementation files; Sprint 87 does not claim stronger secrecy than that

## Private Runtime Validation

- local private wheel build: passed
- clean install/import from artifact: passed in the private validation environment
- public facade capability `run_audit_score_v1`: present
- contract `topocore.audit_score.v1`: present
- no source snippets or private paths are recorded here

## Commands Run

### Sprint 87 installed-package proof branch

- doctor proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720020510`
- workflow mode:
  - `workflow_dispatch`
- comment payload used:
  - `/repobrain doctor`

### Sprint 87 normal control smoke on main

- doctor control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720037313`
- status control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720061021`
- audit control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720074002`
- score control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720091792`
- ask control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720109327`

## Results

### Installed-package proof branch

- the proof workflow reached the artifact-download preflight step and failed before RepoBrain command execution
- `private_checkout` steps were skipped
- no private TopoCore source checkout occurred
- no `.topocore-v6` source path was exposed to RepoBrain
- doctor/status/audit/score did not execute in installed-package mode because the runtime artifact could not be fetched with the available scoped credential

### Failure class

- sanitized failure class: `PACKAGE_AUTH_FAILED`
- exact blocker: `TOKEN_SCOPE_NOT_READY`
- observed trigger: the scoped credential could read the private source repo for controlled checkout scenarios, but it could not read GitHub Actions artifacts from the private TopoCore workflow run

## Backend Evidence

### Installed-package proof branch

- backend result: not reached
- reason: package delivery failed before RepoBrain runtime startup
- false `v6` enrichment claim: `no`
- false installed-package success claim: `no`

### Normal control smoke on main

- doctor:
  - backend resolved: `not_applicable`
  - result: `PASS`
- status:
  - backend resolved: `not_applicable`
  - result: `success`
- audit:
  - backend requested/resolved: `auto / v6`
  - fallback: `no / none`
  - result: `v6-enriched scoring`, `77 / 100 GOOD`
- score:
  - backend requested/resolved: `auto / v6`
  - fallback: `no / none`
  - result: `v6-enriched scoring`, `77 / 100 GOOD`
- ask:
  - backend requested/resolved: `auto / v6`
  - fallback: `not_applicable / none`
  - operational status answer quality: improved

## Safety Result

- no private checkout source path exposed in the installed-package proof branch
- no private TopoCore source exposed
- no secret value exposed
- no mutation
- no v5
- no repobrain-community

## Current Blockers

- package artifact delivery is not yet accessible with the current scoped credential
- exact blocker category: `TOKEN_SCOPE_NOT_READY`
- the proof path remains blocked until an external workflow can fetch the approved private runtime artifact or package without widening access to TopoCore source

## Conclusion

- `INSTALLED_PACKAGE_LIVE_PROOF_BLOCKED`
- Sprint 87 improved delivery design, operational ask quality, and proof plumbing, but public-switch readiness remains blocked until the package/artifact token scope is operationally ready for external installed-package delivery.
