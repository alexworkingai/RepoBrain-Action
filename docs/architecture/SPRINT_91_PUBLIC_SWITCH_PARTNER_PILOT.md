# Sprint 91 Public Switch Partner Pilot

## 1. Purpose

Sprint 91 executes the owner-approved public visibility switch for `RepoBrain-Action`, verifies post-switch safety, and closes the selected partner pilot kickoff package.

It does not make TopoCore public.
It does not start Marketplace publication.

## 2. Baseline

- latest main before Sprint 91:
  - `bc509eb Record decisive installed package proof evidence`
- Sprint 90 status:
  - `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`
- RepoBrain-Action visibility before Sprint 91:
  - `PRIVATE`

## 3. Owner Approval

- owner approval for RepoBrain-Action public visibility:
  - yes
- owner approval for selected partner pilot preparation:
  - yes
- owner approval for `installed_package` as preferred runtime path:
  - yes
- RC tag approval:
  - deferred unless explicitly confirmed later

## 4. Pre-Switch Checks

- startup gates passed on RepoBrain-Action, Elen-MCP, and TopoCore
- Sprint 90 installed-package proof was already present and passed
- pre-switch safety scan passed
- pre-switch docs/tests were validated and merged to `main`
- TopoCore remained private before the switch
- Elen-MCP remained private before the switch

## 5. Visibility Switch Execution

- target repository:
  - `alexworkingai/RepoBrain-Action`
- switch command executed in Sprint 91:
  - `gh repo edit alexworkingai/RepoBrain-Action --visibility public --accept-visibility-change-consequences`
- post-switch visibility:
  - `RepoBrain-Action`: `PUBLIC`
  - `alexworkingai/topocore`: `PRIVATE`
  - `alexworkingai/Elen-MCP-v.2.2.0`: `PRIVATE`
- public repo URL:
  - `https://github.com/alexworkingai/RepoBrain-Action`

## 6. Post-Switch Checks

- public file accessibility rechecked for:
  - `README.md`
  - `LICENSE`
  - `SECURITY.md`
  - `CONTRIBUTING.md`
  - `action.yml`
  - `docs/commands/REPOBRAIN_COMMANDS.md`
  - `docs/partner/PARTNER_TESTING_SETUP.md`
  - `docs/release/PUBLIC_READINESS_ASSESSMENT.md`
  - `docs/release/PARTNER_TESTING_READINESS.md`
  - `docs/security/TOPOCORE_V6_HIGH_SECURITY_POLICY.md`
- usersafe scan passed again after the switch
- no secret, token-like, or private-path exposure was confirmed in tracked public content
- TopoCore source remained private and unexposed

## 7. Public Install Smoke

Safe issue:
- `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/38`

Live public-action smoke after the switch:
- doctor:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26751278884`
  - result: `PASS`
- status:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26751312946`
  - result: `success`
- audit:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26751343246`
  - result: `success`
  - mode: `v6-enriched scoring`
  - score: `77 / 100 GOOD`
  - backend: `auto -> v6`
- score:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26751372597`
  - result: `success`
  - mode: `v6-enriched scoring`
  - score: `77 / 100 GOOD`
  - backend: `auto -> v6`
- ask refresh after docs convergence:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26751908673`
  - result: `success`
  - operational answer reflected public visibility, workflow location, runtime mode, and post-switch readiness truth

Current external smoke truth:
- action source resolves from public `alexworkingai/RepoBrain-Action@main`
- Elen-MCP remained private
- TopoCore remained private
- active Elen-MCP workflow mode stayed `private_checkout` for the standard control path
- `installed_package` remains the preferred partner runtime path and its decisive proof remains passed from Sprint 90
- no mutation occurred
- no secret or TopoCore source exposure was observed in user-facing output

## 8. Partner Pilot Kickoff

- selected partner pilot docs are now finalized for the post-switch state
- runtime model remains:
  - `installed_package` preferred
  - `private_checkout` controlled beta fallback only
- onboarding email template, kickoff plan, setup guide, and runtime runbook are aligned with the public action surface and private runtime boundary
- Marketplace planning remains deferred until partner feedback exists

## 9. Product Status

- historical readiness before execution:
  - `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`
- current Sprint 91 result:
  - `PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY`

## 10. Non-Goals

- no Marketplace publication
- no TopoCore source exposure
- no TopoCore source rights
- no patch/autofix
- no mutation
- no Microsoft/GitHub partnership claim
- no public RC tag creation in Sprint 91
