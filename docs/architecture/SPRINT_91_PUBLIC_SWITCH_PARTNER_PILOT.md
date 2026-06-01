# Sprint 91 Public Switch Partner Pilot

## 1. Purpose

Sprint 91 executes the owner-approved public visibility switch for `RepoBrain-Action` and prepares the selected partner pilot kickoff.

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
  - deferred unless explicitly confirmed later in Sprint 91

## 4. Pre-Switch Checks

- startup gates passed on RepoBrain-Action, Elen-MCP, and TopoCore
- Sprint 90 installed-package proof is present and passed
- TopoCore remains private
- Elen-MCP remains private
- final pre-switch safety scan must pass before visibility changes

## 5. Visibility Switch Execution

- planned for Sprint 91 after pre-switch docs/tests are validated on `main`
- target repository:
  - `alexworkingai/RepoBrain-Action`
- non-target repositories that must remain private:
  - `alexworkingai/topocore`
  - `alexworkingai/Elen-MCP-v.2.2.0`

## 6. Post-Switch Checks

- verify RepoBrain-Action is public
- verify TopoCore stays private
- verify Elen-MCP stays private
- verify public docs render safely
- verify no secrets, private paths, or TopoCore source details are exposed

## 7. Public Install Smoke

- run public-action smoke against Elen-MCP after the switch
- verify doctor, status, audit, score, and ask
- confirm `installed_package` remains the preferred runtime path

## 8. Partner Pilot Kickoff

- selected partner pilot docs will be finalized in Sprint 91
- runtime model remains:
  - `installed_package` preferred
  - `private_checkout` controlled beta fallback only
- feedback template and onboarding materials remain part of the required package

## 9. Product Status

- pre-switch status:
  - `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`
- post-switch target:
  - `PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY`

## 10. Non-Goals

- no Marketplace publication
- no TopoCore source exposure
- no TopoCore source rights
- no patch/autofix
- no mutation
- no Microsoft/GitHub partnership claim
