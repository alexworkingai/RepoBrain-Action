# Public Readiness Assessment

## Current Repository Visibility

- `RepoBrain-Action`: `PRIVATE`
- TopoCore v6: `PRIVATE`
- `Elen-MCP-v.2.2.0`: `PRIVATE`

## Current Product Truth

- audit and score run live in real `v6`-enriched mode when the authorized private runtime is available
- doctor and status are report-only and truthful about runtime state
- operational `/repobrain ask` now answers runtime/workflow/public-readiness questions as a status/ops response rather than a generic review-style synthesis
- no patch/autofix
- no RepoBrain-created branch, commit, or PR behavior
- no `v5`
- no `repobrain-community`
- enterprise P0 hardening from Sprint 86 remains in place before any public switch

## What Must Stay Private

- TopoCore v6 repository
- TopoCore v6 source and internal implementation details
- any real token or private key material
- consumer repository secrets such as `TOPOCORE_V6_REPO_TOKEN`

## Public Scrub Status

Public scrub improvements completed before Sprint 84:

- top-level `LICENSE` exists
- local machine paths have been sanitized from tracked docs
- no private TopoCore source is present in RepoBrain-Action
- no real secret or private key values are present in tracked docs
- command/docs/support surface is aligned with current product behavior

## Runtime Distribution Status

Sprint 84 selected a near-term partner-testing runtime model:

- decision: `INSTALLED_PRIVATE_PACKAGE_SELECTED`
- `private_checkout` remains controlled beta only
- selected partner testing should prefer installed private package mode

Important caveat:
- a standard private Python wheel can still contain readable implementation files
- this is acceptable for selected partner testing only under explicit approval and scoped access
- it is not the same as strong source secrecy or broad public distribution hardening

Sprint 87 installed-package proof update:
- selected proof path: `temporary_controlled_artifact_proof`
- private TopoCore source checkout remained avoided in the external proof branch
- external artifact delivery did not become operational with the current scoped credential
- exact blocker was identified as `TOKEN_SCOPE_NOT_READY`
- the detailed proof record is tracked in `docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md`

Sprint 87 normal control smoke:
- Elen-MCP still ran successfully in controlled `private_checkout` beta mode on main
- `/repobrain audit` remained real `v6`-enriched scoring
- `/repobrain score`, `/repobrain doctor`, and `/repobrain status` all passed with truthful runtime-mode reporting
- `/repobrain ask` now returned a precise operational status answer without secret or source leakage

## Remaining Conditions Before Visibility Change

Public visibility still requires all of the following:

1. explicit owner approval
2. selected-partner runtime/token process in place
3. no accidental source-repo access grants beyond the chosen distribution model
4. no Marketplace publication in this phase
5. final approval checklist and partner pack review completed
6. final pre-public smoke remains green on a controlled external repository
7. enterprise P0 hardening remains green, including supply-chain baseline, governance evidence, least-privilege workflow posture, and mutation-surface cleanup
8. installed-package delivery token scope must be operationally ready for external artifact or package retrieval without source checkout

## User Support Implication

If RepoBrain-Action becomes public after approval:

- the public repo still fronts a private TopoCore boundary
- selected partners may receive runtime access without source-repo access
- broader turnkey public install and Marketplace support are still future work

## Decision

- current public readiness decision: `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`
- private beta decision: `PRIVATE_BETA_RC_CONFIRMED`
- TopoCore security decision: `TOPOCORE_SECURITY_POLICY_ADOPTED`
- Marketplace decision: `MARKETPLACE_NOT_READY`

Historical state retained for traceability:

- Sprint 84 / Sprint 85 decision: `PUBLIC_READY_PENDING_OWNER_APPROVAL`
- Sprint 86 decision: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`

Sprint 85 packaging note:

- the public visibility approval checklist and selected partner pack are prepared
- the final pre-public smoke passed on Elen-MCP with doctor, status, audit, score, and ask all succeeding
- the approval pack is ready for owner review once runtime proof is no longer blocked
- tag creation remains approval-gated and is not performed automatically

Sprint 86 enterprise hardening note:

- SECURITY.md, CONTRIBUTING.md, and CODEOWNERS are now part of the pre-public baseline
- dependency review, CodeQL, SBOM, and provenance-prep workflows are prepared with least-privilege gates
- governance verification is documented with `403 => UNKNOWN`, not false PASS
- installed-package live proof remained a hard gate and is tracked separately in `docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md`
- Sprint 86 attempted installed-package proof on `alexworkingai/Elen-MCP-v.2.2.0` without `private_checkout`
- the proof path stayed safe and truthful, but external package delivery was not operationally available

Sprint 87 runtime-proof note:

- a private runtime artifact workflow now exists and produced a real wheel artifact for proof consumption
- the external proof workflow avoided private source checkout and requested true `installed_package` mode
- the blocker is now exact rather than generic: `TOKEN_SCOPE_NOT_READY`
- because of that, Sprint 87 still blocks the public switch on token-scoped delivery readiness rather than on supply-chain, mutation-surface, or ask-quality readiness
