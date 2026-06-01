# Installed Package Live Proof

## Purpose

This document records the Sprint 86 through Sprint 90 work to prove external `installed_package` runtime mode in a partner-like external workflow without `private_checkout` source checkout.

## Proof Target

- target repository: `alexworkingai/Elen-MCP-v.2.2.0`
- proof issue from Sprint 87: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/35`
- Sprint 88 proof branch target: `codex/sprint-88-installed-package-access-proof`
- goal: external workflow using `RB_TOPOCORE_V6_RUNTIME_MODE=installed_package`

## Workflow Mode

- requested mode: `installed_package`
- selected delivery path: `fine_grained_pat_actions_read_artifact_download`
- private_checkout avoided: `yes`
- source checkout avoided: `yes` for private TopoCore source checkout

## Runtime Package Source Type

- private build source: TopoCore private workflow artifact
- private workflow run: `https://github.com/alexworkingai/topocore/actions/runs/26719642497`
- artifact name: `topocore-v6-runtime-wheel`
- artifact digest: `sha256:aa70729efa6bb229a7ad559ca1b5c893fa63e680df82e34884f87d366ac8f354`
- package import name: `topocore_v6`
- honest caveat: a normal wheel may still contain readable Python implementation files; Sprint 88 does not claim stronger secrecy than that

## Private Runtime Validation

- local private wheel build: passed
- clean install/import from artifact: passed in the private validation environment
- public facade capability `run_audit_score_v1`: present
- contract `topocore.audit_score.v1`: present
- no source snippets or private paths are recorded here

## Commands Run

### Sprint 88 installed-package authorization proof

- proof issue:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/36`
- workflow branch:
  - `codex/sprint-88-installed-package-access-proof`
- workflow mode:
  - `workflow_dispatch`
- doctor proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26734273501`
- comment payload used:
  - `/repobrain doctor`

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

### Sprint 88 authorization result

- authorization model selected: `fine_grained_pat_actions_read_artifact_download`
- owner-side credential issuance still pending
- the workflow-only proof branch now reaches a dedicated installed-package credential preflight seam
- no new external installed-package runtime start can be honestly claimed until `TOPOCORE_V6_ARTIFACT_TOKEN` exists with the selected minimum scope

### Sprint 89 owner-token verification result

- startup recheck:
  - `gh secret list --repo alexworkingai/Elen-MCP-v.2.2.0`
- expected secret:
  - `TOPOCORE_V6_ARTIFACT_TOKEN`
- observed result:
  - secret still absent
- proof rerun:
  - not attempted
- reason:
  - Sprint 89 hard stop requires stopping before proof when the owner-issued artifact credential is still missing

### Sprint 90 owner-token verification result

- startup recheck:
  - `gh secret list --repo alexworkingai/Elen-MCP-v.2.2.0`
- expected secret:
  - `TOPOCORE_V6_ARTIFACT_TOKEN`
- observed result:
  - secret still absent
- decisive proof rerun:
  - not attempted
- reason:
  - Sprint 90 hard stop requires stopping before proof when the owner-issued artifact credential is still missing

## Results

### Installed-package proof branch

- the proof workflow path exists and stays source-checkout-free by design
- the selected credential model is now explicit and GitHub-supported
- Sprint 88 ran a fresh external proof workflow on `codex/sprint-88-installed-package-access-proof`
- the run stopped at the new installed-package credential preflight step before any private checkout or RepoBrain runtime startup
- doctor/status/audit/score therefore cannot yet be claimed as executed in external installed-package mode during Sprint 88

### Failure class

- historical sanitized failure class: `PACKAGE_AUTH_FAILED`
- historical exact blocker: `TOKEN_SCOPE_NOT_READY`
- current Sprint 88 blocker: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- observed trigger: the approved fine-grained artifact-read credential model is known, but the corresponding secret `TOPOCORE_V6_ARTIFACT_TOKEN` is not yet provisioned in `alexworkingai/Elen-MCP-v.2.2.0`
- Sprint 89 verification result:
  - blocker unchanged
  - no new artifact access preflight result can be claimed because the required secret was still absent
- Sprint 90 verification result:
  - blocker still unchanged
  - no new preflight or runtime evidence can be claimed because the required secret was still absent again

## Backend Evidence

### Installed-package proof branch

- backend result: not reached in Sprint 88
- reason: owner-side minimum-scope credential issuance is still pending
- false `v6` enrichment claim: `no`
- false installed-package success claim: `no`

### Normal control smoke on main

- issue:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/36`
- doctor:
  - run:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26734288528`
  - backend resolved: `not_applicable`
  - result: `PASS`
- status:
  - run:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26734289658`
  - backend resolved: `not_applicable`
  - result: `success`
- audit:
  - run:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26734289953`
  - backend requested/resolved: `auto / v6`
  - fallback: `no / none`
  - result: `v6-enriched scoring`, `77 / 100 GOOD`
- score:
  - run:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26734290692`
  - backend requested/resolved: `auto / v6`
  - fallback: `no / none`
  - result: `v6-enriched scoring`, `77 / 100 GOOD`
- ask:
  - run:
    - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26734291673`
  - backend requested/resolved: `auto / v6`
  - fallback: `not_applicable / none`
  - operational status answer quality: improved
  - public readiness surfaced as: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`

## Safety Result

- no private checkout source path exposed in the installed-package proof design
- no private TopoCore source exposed
- no secret value exposed
- no mutation
- no v5
- no repobrain-community

## Current Blockers

- minimum-scope external artifact credential is not yet provisioned
- current blocker category: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- previous lower-level failure marker remains relevant: `TOKEN_SCOPE_NOT_READY`
- the proof path remains blocked until an external workflow can fetch the approved private runtime artifact without source checkout and without widening access to TopoCore source
- Sprint 89 confirms the blocker remains owner action, not a newly observed runtime or contract defect
- Sprint 90 confirms the blocker still remains owner action, not a newly observed runtime or contract defect

## Conclusion

- `INSTALLED_PACKAGE_LIVE_PROOF_BLOCKED`
- Sprint 88 resolved the supported authorization model and narrowed the exact owner-side action required.
- Sprint 89 rechecked the decisive proof gate, found the required secret still missing, and correctly stopped without fabricating new installed-package runtime evidence.
- Sprint 90 rechecked the decisive proof gate again, found the required secret still missing, and correctly stopped without recreating the proof branch or fabricating new installed-package runtime evidence.
- This document does not claim live external installed-package success without new runtime evidence.
