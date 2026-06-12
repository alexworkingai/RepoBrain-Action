# Partner Self-Service Quickstart

Purpose:
- describe the intended Phase 1 partner self-service onboarding shape for the public RepoBrain action
- keep current product truth honest while Sprint 93D-Sprint 93E finish the remaining hardening and trusted-partner validation work

Current truth:
- RepoBrain-Action is public
- TopoCore v6 remains private and server-side
- Sprint 93A prepared the self-service foundation
- Sprint 93B implements the public action-side GitHub OIDC identity envelope
- Sprint 93C implements the hosted trust verification and auto-provisioning boundary
- Sprint 93D now wires the end-to-end action-to-hosted self-service path for supported commands
- Sprint 93E adds the trusted-partner validation runbook and evidence template
- final trusted-partner live validation still remains pending for Sprint 93E

## Intended Phase 1 partner flow

1. Add the RepoBrain workflow file to your repository.
2. Allow the minimal GitHub Actions permissions required by the workflow.
3. Use `/repobrain` commands from issue comments or PR comments.
4. Do not request a RepoBrain owner token.
5. Do not wait for manual partner registration from the RepoBrain owner.
6. Do not install or download TopoCore.
7. Receive public-safe score and audit results in GitHub comments.

## Example workflow shape

Use the current self-service workflow shape as a foundation:

- `docs/examples/repobrain_partner_self_service_workflow.yml`

Key properties of this shape:
- `contents: read`
- `issues: write`
- `pull-requests: write`
- `id-token: write`
- no RepoBrain owner-generated secret
- no TopoCore package install
- no TopoCore source checkout

Current action reference truth:
- the example uses `alexworkingai/RepoBrain-Action@main` because Sprint 93A does not introduce a new release alias or onboarding tag
- immutable tag or alias decisions remain future release-management work

## Validation before final Phase 1 PASS

Trusted-partner self-service is close to the intended Phase 1 shape, but the final PASS state is still gated on live validation.

Use these documents before describing the flow as fully trusted-partner ready:

- runbook: `docs/release/SPRINT_93E_TRUSTED_PARTNER_VALIDATION_RUNBOOK.md`
- evidence template: `docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md`
- primary smoke checklist: `docs/repobrain_93e_self_service_smoke.md`
- secondary smoke checklist: `docs/repobrain_93e_community_self_service_smoke.md`

Current status remains:

- `SPRINT_93E_HARDENING_READY_LIVE_VALIDATION_PENDING`

Do not claim from this quickstart alone:

- unrestricted public launch
- Marketplace readiness
- enterprise readiness
- production certification
- security certification
- final trusted-partner PASS without live Issue and PR validation on both selected repositories

## Why `id-token: write` appears now

`id-token: write` is now required for the Sprint 93B action-side OIDC envelope path.

Sprint 93B now implements:
- GitHub OIDC identity acquisition in the public action
- a default OIDC audience
- a sanitized identity envelope
- a clear failure path when `id-token: write` is missing

Current truth remains:
- hosted API verification is implemented as a Sprint 93C boundary
- automatic tenant provisioning is implemented as a Sprint 93C boundary
- Sprint 93D now wires the end-to-end action-to-hosted flow for supported commands
- partner self-service public action is still not yet fully live and is not claimed as fully live
- Sprint 93E is still required for trusted partner hardening/live validation

## Action inputs carried forward from Sprint 93A into Sprint 93B

The public action now exposes these optional inputs without making them mandatory for legacy operation:
- `profile`
- `terms_accepted`
- `api_url`
- `oidc_audience`
- `self_service_mode`

Current truth:
- they are optional and non-breaking
- `self_service_mode` now enables action-side OIDC, terms gating, hosted request sending, and hosted response rendering for supported commands
- the action-side payload now matches the Sprint 93C hosted contract boundary
- `api_url` is required when self-service mode is enabled for hosted `ask`, `audit`, or `score`
- they still do not create a final trusted-partner validated production path by themselves
- final hardening and trusted partner validation still belong to Sprint 93E

## Data boundary for later Phase 1 hosted flow

Current data sent to the hosted RepoBrain API in Sprint 93D:
- GitHub repository identity from verified workflow context
- requested RepoBrain command such as `/repobrain score` or `/repobrain audit`
- bounded repository evidence needed for the requested analysis
- workflow or run metadata needed for request validation and safe reporting

What Sprint 93B adds:
- GitHub OIDC token acquisition in the action when available
- a sanitized `repobrain.github_oidc_identity.v1` envelope for future hosted verification
- safe refusal when `self_service_mode: "true"` is enabled without `terms_accepted: "true"` or `id-token: write`

What Sprint 93C adds:
- hosted request/response contract for `POST /v1/github/actions/audit`
- server-side GitHub OIDC JWT verification boundary
- claim consistency checks between verified JWT claims and the action identity envelope
- automatic tenant/repository provisioning boundary
- default partner-pilot quota boundary
- private hosted TopoCore adapter boundary

Data not sent by default:
- full repository archive
- secrets
- private tokens
- TopoCore runtime files
- private backend traces
- manually collected partner metadata from the RepoBrain owner

What Sprint 93D adds now:
- real action-side hosted API request sending for supported self-service commands
- public-safe hosted success rendering back into the existing GitHub comment flow
- public-safe hosted error rendering for missing `api_url`, quota, OIDC, and availability failures
- bounded evidence packets only; no full repository archive upload

## TopoCore boundary

Always preserve these rules:
- TopoCore v6 remains private
- TopoCore v6 runs server-side
- TopoCore v6 remains private and server-side
- partners must not receive TopoCore source
- partners must not install a TopoCore package or container on their runner for the Phase 1 public thin-client direction
- RepoBrain comments and diagnostics must remain public-safe

## No-manual-token onboarding invariant

Partner self-service means:
- no RepoBrain-issued partner token
- no manual partner registration by the RepoBrain owner
- no manual partner metadata intake by the RepoBrain owner
- no owner approval queue for the intended trusted partner pilot flow
- partner opt-in happens by adding the workflow file to the partner repository

Still required from the partner side:
- repository admin or workflow-maintainer access to add the workflow
- GitHub Actions permissions that allow the workflow to run
- `id-token: write` when validating the action-side OIDC identity envelope
- acceptance that RepoBrain may apply automatic quotas and abuse protection server-side in later Phase 1

## What Sprint 93D still does not do

Sprint 93D does not implement:
- final trusted-partner live validation
- final hardening signoff
- a dashboard
- an owner/admin panel
- a GitHub App onboarding path
- enterprise self-hosted runtime distribution

These remain Sprint 93E or later-phase items and should not be described as already live.
