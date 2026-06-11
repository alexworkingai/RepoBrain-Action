# Sprint 93B OIDC Identity Envelope

## Purpose

Sprint 93B implements the public action side of the GitHub OIDC identity flow for Phase 1 partner self-service.

This sprint does not make partner self-service fully live.
It adds action-side token acquisition, a sanitized identity envelope, and safe gating while preserving the private TopoCore boundary.

## Implemented in Sprint 93B

- GitHub Actions OIDC token acquisition through the action runtime when `id-token: write` is available
- default OIDC audience handling with `repobrain-api`
- optional custom audience through `oidc_audience`
- sanitized `repobrain.github_oidc_identity.v1` envelope construction
- safe `self_service_mode` gating for:
  - `terms_accepted: "true"`
  - GitHub OIDC availability
- backward-compatible non-self-service behavior when `self_service_mode` is disabled

## Deferred to Sprint 93C

Sprint 93B does not implement:
- hosted API contract
- OIDC JWT trust verification
- issuer, audience, expiration, or claim enforcement in a backend
- automatic tenant provisioning
- quota profile activation through hosted policy
- public-safe hosted response contract

## Envelope contract

The action now builds a sanitized envelope with:
- repository identity metadata
- workflow and run metadata
- action identity metadata
- command metadata
- self-service config metadata
- OIDC availability and redacted token status

The public action does not log:
- raw OIDC JWT
- `ACTIONS_ID_TOKEN_REQUEST_TOKEN`
- authorization headers
- private runtime paths

## Safety invariants preserved

- RepoBrain-Action remains a thin public client
- TopoCore v6 remains private and server-side
- no owner-generated onboarding token path
- no manual partner registration path
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
- no score authority change
- no governance overclaim beyond current script truth

## Current status

- Sprint status: `SPRINT_93B_OIDC_IDENTITY_ENVELOPE_READY` after validation
- Not claimed: `PARTNER_SELF_SERVICE_PUBLIC_ACTION_FULLY_LIVE`
- Sprint 93C now provides hosted verification and tenant provisioning boundaries
- Next required sprint: Sprint 93D for the end-to-end action-to-hosted partner workflow
