# Partner Self-Service Quickstart

Purpose:
- describe the intended Phase 1 partner self-service onboarding shape for the public RepoBrain action
- keep current product truth honest while Sprint 93B-Sprint 93E finish the remaining identity and hosted-runtime work

Current truth:
- RepoBrain-Action is public
- TopoCore v6 remains private and server-side
- Sprint 93A prepares the self-service foundation only
- full OIDC-backed self-service onboarding is an upcoming Phase 1 implementation, not a completed production path yet

## Intended Phase 1 partner flow

1. Add the RepoBrain workflow file to your repository.
2. Allow the minimal GitHub Actions permissions required by the workflow.
3. Use `/repobrain` commands from issue comments or PR comments.
4. Do not request a RepoBrain owner token.
5. Do not wait for manual partner registration from the RepoBrain owner.
6. Do not install or download TopoCore.
7. Receive public-safe score and audit results in GitHub comments.

## Example workflow shape

Use the upcoming self-service workflow shape as a foundation:

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

`id-token: write` is included as a future-ready permission for Sprint 93B.

Sprint 93B will implement:
- GitHub OIDC identity acquisition in the public action
- a default OIDC audience
- a signed request envelope
- a clear failure path when `id-token: write` is missing

Sprint 93A does not claim that OIDC-backed onboarding is already live.

## Reserved action inputs prepared in Sprint 93A

The public action can now document these optional reserved inputs without making them mandatory:
- `profile`
- `terms_accepted`
- `api_url`
- `oidc_audience`
- `self_service_mode`

Current truth:
- they are optional and non-breaking
- they are not enforced as a production self-service path in Sprint 93A
- they exist to stabilize the public surface before Sprint 93B and Sprint 93C

## Data boundary for later Phase 1 hosted flow

Intended data sent to the hosted RepoBrain API in later Phase 1:
- GitHub repository identity from verified workflow context
- requested RepoBrain command such as `/repobrain score` or `/repobrain audit`
- bounded repository evidence needed for the requested analysis
- workflow or run metadata needed for request validation and safe reporting

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
- future OIDC-compatible runner permissions through `id-token: write`
- acceptance that RepoBrain may apply automatic quotas and abuse protection server-side in later Phase 1

## What Sprint 93A does not do

Sprint 93A does not implement:
- live OIDC token exchange
- hosted backend auto-provisioning
- automatic tenant registration
- a dashboard
- an owner/admin panel
- a GitHub App onboarding path
- enterprise self-hosted runtime distribution

These remain future Phase 1 or later-phase items and should not be described as already live.
