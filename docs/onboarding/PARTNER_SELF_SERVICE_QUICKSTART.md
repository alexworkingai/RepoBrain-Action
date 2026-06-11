# Partner Self-Service Quickstart

Purpose:
- describe the intended Phase 1 partner self-service onboarding shape for the public RepoBrain action
- keep current product truth honest while Sprint 93C-Sprint 93E finish the remaining hosted verification and rollout work

Current truth:
- RepoBrain-Action is public
- TopoCore v6 remains private and server-side
- Sprint 93A prepared the self-service foundation
- Sprint 93B implements the public action-side GitHub OIDC identity envelope
- full hosted self-service onboarding is still not a completed production path yet

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

## Why `id-token: write` appears now

`id-token: write` is now required for the Sprint 93B action-side OIDC envelope path.

Sprint 93B now implements:
- GitHub OIDC identity acquisition in the public action
- a default OIDC audience
- a sanitized identity envelope
- a clear failure path when `id-token: write` is missing

Current truth remains:
- hosted API verification is not live in Sprint 93B
- automatic tenant provisioning is not live in Sprint 93B
- partner self-service public action is not yet fully live
- Sprint 93C is still required for hosted trust verification and provisioning

## Action inputs carried forward from Sprint 93A into Sprint 93B

The public action now exposes these optional inputs without making them mandatory for legacy operation:
- `profile`
- `terms_accepted`
- `api_url`
- `oidc_audience`
- `self_service_mode`

Current truth:
- they are optional and non-breaking
- `self_service_mode` now enables action-side OIDC and terms gating
- they still do not create a full hosted self-service production path by themselves
- hosted verification and auto-provisioning still belong to Sprint 93C

## Data boundary for later Phase 1 hosted flow

Intended data sent to the hosted RepoBrain API in later Phase 1:
- GitHub repository identity from verified workflow context
- requested RepoBrain command such as `/repobrain score` or `/repobrain audit`
- bounded repository evidence needed for the requested analysis
- workflow or run metadata needed for request validation and safe reporting

What Sprint 93B adds now:
- GitHub OIDC token acquisition in the action when available
- a sanitized `repobrain.github_oidc_identity.v1` envelope for future hosted verification
- safe refusal when `self_service_mode: "true"` is enabled without `terms_accepted: "true"` or `id-token: write`

Data not sent by default:
- full repository archive
- secrets
- private tokens
- TopoCore runtime files
- private backend traces
- manually collected partner metadata from the RepoBrain owner

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

## What Sprint 93B still does not do

Sprint 93B does not implement:
- hosted backend auto-provisioning
- hosted OIDC JWT verification
- automatic tenant registration
- a dashboard
- an owner/admin panel
- a GitHub App onboarding path
- enterprise self-hosted runtime distribution

These remain future Phase 1 or later-phase items and should not be described as already live.
