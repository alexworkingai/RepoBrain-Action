# Installed Package Live Proof

## Purpose

This document records the Sprint 86 through Sprint 90 work to prove external `installed_package` runtime mode in a partner-like external workflow without `private_checkout` or private source checkout.

## Proof Target

- target repository: `alexworkingai/Elen-MCP-v.2.2.0`
- decisive proof issue: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/37`
- decisive proof branch: `codex/sprint-90-installed-package-proof`
- goal: external workflow using `RB_TOPOCORE_V6_RUNTIME_MODE=installed_package`

## Workflow Mode

- requested mode: `installed_package`
- selected delivery path: `fine_grained_pat_actions_read_artifact_download`
- private_checkout avoided: `yes`
- source checkout avoided: `yes` for private TopoCore source checkout

## Historical Trace

- Sprint 87 established the external installed-package proof branch and narrowed the first failure to `TOKEN_SCOPE_NOT_READY`
- Sprint 88 selected the GitHub-supported authorization path and surfaced the owner-side gate as `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- Sprint 89 correctly stopped because the required secret was absent

## Runtime Package Source Type

- private build source: TopoCore private workflow artifact
- private workflow run: `https://github.com/alexworkingai/topocore/actions/runs/26719642497`
- artifact name: `topocore-v6-runtime-wheel`
- artifact digest: `sha256:aa70729efa6bb229a7ad559ca1b5c893fa63e680df82e34884f87d366ac8f354`
- package import name: `topocore_v6`
- honest caveat: a normal wheel may still contain readable Python implementation files; Sprint 90 does not claim stronger secrecy than that

## Private Runtime Validation

- local private wheel build: passed
- clean install/import from artifact: passed in the private validation environment
- public facade capability `run_audit_score_v1`: present
- contract `topocore.audit_score.v1`: present
- no source snippets or private paths are recorded here

## Commands Run

### Sprint 90 decisive installed-package proof

- proof issue:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/37`
- workflow branch:
  - `codex/sprint-90-installed-package-proof`
- workflow mode:
  - `workflow_dispatch`
- doctor proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749906900`
- status proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749940756`
- audit proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749942289`
- score proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749943941`
- ask initial proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749945553`
- ask refreshed after RepoBrain `main` docs update:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26750529959`

### Sprint 90 control smoke on main

- doctor control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749992255`
- status control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749993658`
- audit control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749995358`
- score control run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26749997090`

## Artifact Preflight Result

- secret present: `yes`
- artifacts listed: `yes`
- target artifact found: `yes`
- artifact downloaded: `yes`
- digest verified: `yes`
- wheel installed: `yes`
- package imported: `yes`
- `run_audit_score_v1`: `yes`
- `topocore.audit_score.v1`: `yes`
- result: `INSTALLED_PACKAGE_PREFLIGHT_STATUS=PASS`

## Results

### Installed-package proof branch

- doctor reached `installed_package`
- status reached `installed_package`
- dependency mode reported as `installed_private_package`
- audit ran in real `v6-enriched scoring`
- score ran in real `v6-enriched scoring`
- backend resolved `auto -> v6`
- fallback stayed `no / none`
- private TopoCore source checkout was not used
- private_checkout fallback was not used

### Control smoke on main

- controlled `private_checkout` beta path stayed green
- doctor: `PASS`
- status: `success`
- audit: `v6-enriched scoring`, `77 / 100 GOOD`
- score: `v6-enriched scoring`, `77 / 100 GOOD`

## Backend Evidence

### Installed-package proof branch

- doctor:
  - runtime requested/effective: `installed_package / installed_package`
  - backend resolved: `not_applicable`
  - result: `PASS`
- status:
  - runtime requested/effective: `installed_package / installed_package`
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
  - initial proof run succeeded but still reflected the pre-merge blocked docs snapshot
  - refreshed proof run surfaced:
    - `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`
    - `INSTALLED_PACKAGE_LIVE_PROOF_PASSED`
    - next step: explicit owner approval

## Safety Result

- no private checkout source path exposed in the installed-package proof path
- no private TopoCore source exposed
- no secret value exposed
- no mutation
- no v5
- no repobrain-community

## Current Blockers

- installed-package runtime proof itself is no longer blocked
- remaining gate is explicit owner approval for the public visibility switch and selected partner pilot
- broader hardened delivery options such as managed runtime or compiled artifacts remain future work, not Sprint 90 blockers

## Conclusion

- `INSTALLED_PACKAGE_LIVE_PROOF_PASSED`
- Sprint 90 completed the decisive external installed-package runtime proof with real `v6` enrichment and no private source checkout.
- This document does not claim a public switch, Marketplace publication, or stronger secrecy than a scoped private wheel-based delivery path actually provides.
