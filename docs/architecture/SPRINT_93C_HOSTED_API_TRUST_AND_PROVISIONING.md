# Sprint 93C Hosted API Trust And Provisioning

## Purpose

Sprint 93C implements the hosted RepoBrain API trust boundary for Phase 1 partner self-service.

This sprint does not make partner self-service fully live.
It defines and validates the hosted request/response contract, server-side GitHub OIDC verification, claim consistency checks, automatic tenant provisioning, quota enforcement, and the private hosted TopoCore adapter boundary.

## Hosted API contract

- Endpoint: `POST /v1/github/actions/audit`
- Request version: `repobrain.github_action_audit_request.v1`
- Response version: `repobrain.github_action_audit_response.v1`
- Identity version: `repobrain.github_oidc_identity.v1`
- Tenant version: `repobrain.partner_tenant.v1`
- Quota version: `repobrain.partner_quota.v1`

The hosted handler is implemented as a pure service boundary rather than a web framework route.
That keeps the trust logic testable without claiming a production deployment surface yet.

## GitHub OIDC server-side verification

Sprint 93C adds a server-side GitHub OIDC verifier that supports:
- issuer validation
- audience validation
- discovery and JWKS lookup
- signature verification
- expiration and not-before validation
- required GitHub claim enforcement
- claim consistency checks against the action identity envelope

Raw OIDC JWT values are not logged, rendered, or returned in responses.

## Claim consistency boundary

Verified JWT claims must match the action-provided identity envelope for:
- repository full name
- repository id
- repository owner
- repository owner id
- workflow run metadata
- actor metadata
- workflow identity
- event/ref/sha metadata

Mismatch fails closed with a public-safe error response.

## Automatic tenant provisioning

Sprint 93C adds an in-memory tenant provisioning boundary for:
- deterministic tenant id creation from `owner_id + repository_id`
- automatic create-or-update behavior
- no owner-generated onboarding token
- no manual partner registration
- no manual approval requirement in the default partner-pilot path

Production persistence remains a later deployment concern and is not claimed here.

## Default quota boundary

Sprint 93C adds a default `partner_pilot_auto` quota policy boundary:
- audit/score: `20` runs per repository per UTC day
- ask: `20` runs per repository per UTC day
- premium narrative path: `5` runs per repository per UTC day

This is the default partner-pilot quota boundary for the hosted self-service trust path.

Quota is enforced before TopoCore.
Quota failures remain public-safe and do not expose private runtime details.

## Private hosted TopoCore boundary

Sprint 93C adds a private hosted TopoCore adapter boundary:
- TopoCore remains score authority
- TopoCore remains private and server-side only
- no TopoCore source, runtime package, container, or path is returned to the public action
- no mutation behavior is introduced

The default public repository implementation keeps the adapter injectable and unavailable by default.
That preserves the boundary without overclaiming live hosted runtime access from this repository alone.

## Action-side alignment

Sprint 93B created the action-side identity envelope.
Sprint 93C aligns the action-side request payload with the hosted contract and stores only a redacted request preview.

Actual outbound sending from the public action remains deferred to Sprint 93D.

## Safety invariants preserved

- RepoBrain-Action remains the thin public client
- TopoCore v6 remains the private hosted/server-side runtime
- no owner-generated onboarding token path
- no manual partner registration path
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
- no score math change
- no governance overclaim beyond current script truth
- no full partner self-service live claim

## Current status

- Sprint status target: `SPRINT_93C_HOSTED_API_TRUST_AND_AUTO_PROVISIONING_READY`
- Not claimed: `PARTNER_SELF_SERVICE_PUBLIC_ACTION_FULLY_LIVE`
- Next required sprint: Sprint 93D for end-to-end action send path and GitHub response rendering
- Final hardening sprint: Sprint 93E for trusted partner security hardening and live validation
