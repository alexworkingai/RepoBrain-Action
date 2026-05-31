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
- version/hash if safe:
  - artifact name: `topocore-v6-runtime-wheel`
  - digest: `sha256:aa70729efa6bb229a7ad559ca1b5c893fa63e680df82e34884f87d366ac8f354`
- capability present: yes
- validation result:
  - private build/install/import proof passed
  - `run_audit_score_v1` remained present
- no source details are recorded here

## 5. External Workflow Proof

- repo used: `alexworkingai/Elen-MCP-v.2.2.0`
- proof branch: `codex/sprint-87-installed-package-proof`
- workflow mode: `installed_package`
- private_checkout avoided: yes
- source checkout avoided: yes for private TopoCore source checkout
- commands run:
  - installed-package proof doctor dispatch
  - main-path control smoke for doctor, status, audit, score, and ask
- proof run URLs:
  - private artifact build: `https://github.com/alexworkingai/topocore/actions/runs/26719642497`
  - installed-package proof doctor: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720020510`
- control smoke run URLs:
  - doctor: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720037313`
  - status: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720061021`
  - audit: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720074002`
  - score: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720091792`
  - ask: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26720109327`
- result:
  - installed-package proof branch blocked before RepoBrain startup
  - exact blocker: `TOKEN_SCOPE_NOT_READY`
  - control smoke on the normal runtime path stayed green

## 6. Ask Operational Quality

- problem: operational ask questions returned a weaker review-style synthesis than needed
- implementation: detect operational status intent and answer with workflow/runtime/public-readiness status from safe diagnostics and release docs
- examples/tests:
  - `tests/test_operational_ask_quality.py`
- live ask result:
  - answer now included workflow location, runtime mode, public-readiness status, installed-package proof status, backend evidence, and no-mutation safety
  - user-visible route was `FAST`, not misleading `REVIEW`

## 7. Public Readiness Decision

- `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`
- exact blocker: the current scoped credential could not retrieve the private runtime artifact from GitHub Actions artifacts, so external installed-package delivery is still not operationally proven

## 8. Product Status

- `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`

## 9. Next Step

- Sprint 88 should operationalize a package or artifact delivery path whose token scope works in an external workflow without source checkout
- only after that proof passes should owner approval for a public visibility switch be reconsidered

## 10. Non-Goals

- no public switch
- no Marketplace
- no public RC tag unless explicitly approved
- no v5
- no repobrain-community
- no patch/autofix
- no TopoCore source exposure
- no Microsoft partnership claim
