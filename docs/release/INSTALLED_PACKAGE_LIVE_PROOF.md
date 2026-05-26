# Installed Package Live Proof

## Purpose

This document records the Sprint 86 attempt to prove `installed_package` runtime mode in a partner-like external workflow without `private_checkout` source checkout.

## Proof Target

- target repository: `alexworkingai/Elen-MCP-v.2.2.0`
- target branch for proof workflow: `codex/sprint-86-installed-package-proof`
- goal: external workflow using `RB_TOPOCORE_V6_RUNTIME_MODE=installed_package`

## Workflow Mode

- requested mode: `installed_package`
- source checkout avoided: `yes`
- private TopoCore source checkout avoided: `yes`

## Runtime Package Source Type

- intended source: approved private package or runtime artifact delivery path
- current operational source: not configured in the external workflow yet
- local private packaging truth:
  - private wheel build and install succeeded in a clean local environment
  - public facade still exposed `run_audit_score_v1`
  - readable `.py` implementation remains an accepted selected-partner caveat, not strong secrecy

## Commands Run

- doctor proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455084053`
- status proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455128599`
- audit proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455131085`
- score proof run:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455134051`

## Results

- all four proof runs completed successfully at the workflow level
- `private_checkout` steps were skipped in the proof workflow
- doctor/status correctly reported:
  - requested mode: `installed_package`
  - effective mode: `installed_package_unavailable`
  - dependency mode: `installed_private_package_unavailable`
- audit and score did not claim `v6` enrichment
- audit fell back to:
  - `static scoring with v6 contract-ready guard`
- score fell back to:
  - `static scoring with v6 contract-ready guard`

## Backend Evidence

- doctor:
  - backend resolved: `not_applicable`
  - fallback reason: `doctor_diagnostic_report`
- status:
  - backend resolved: `not_applicable`
  - fallback reason: `status_report_only`
- audit:
  - backend requested/resolved: `auto / not_applicable`
  - fallback reason: `audit_v6_capability_unavailable_static_scoring`
- score:
  - backend requested/resolved: `auto / not_applicable`
  - fallback reason: `audit_v6_capability_unavailable_static_scoring`

## Safety Result

- no private checkout source path exposed
- no private TopoCore source exposed
- no secret value exposed
- no mutation
- no v5
- no repobrain-community

## Current Blockers

- package registry or artifact delivery path is not yet operational in the external workflow
- the proof workflow can request `installed_package`, but it cannot yet install an approved private runtime package/artifact without reverting to source checkout
- token scope and delivery mechanics for package-only external installation are not yet operationally proven
- because of that, real external `v6` enrichment in `installed_package` mode is not yet live-proven

## Conclusion

- `INSTALLED_PACKAGE_LIVE_PROOF_BLOCKED`
- Sprint 86 local packaging truth is positive, but the public-switch gate remains blocked until external installed-package delivery is operationally proven without `private_checkout`.
