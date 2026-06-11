# Sprint 93A Self-Service Partner Foundation

## Purpose

Sprint 93A prepares the first public self-service partner foundation for RepoBrain-Action while preserving all current safety and private-runtime boundaries.

This sprint does not make partner self-service fully live.
It establishes the public thin-client direction, reserved configuration surface, and partner-facing documentation that Sprint 93B-Sprint 93E will build on.

## Core Phase 1 architecture contract

- RepoBrain-Action is the public thin client.
- TopoCore v6 remains a private hosted and server-side runtime.
- Partners must not receive TopoCore source, package, or container as part of the intended self-service public action direction.
- Partner runners must not install TopoCore in the intended Phase 1 thin-client model.
- Public RepoBrain workflows may collect only bounded repository evidence.
- Public RepoBrain output must remain public-safe and must not expose private runtime paths, raw traces, secrets, or private checkout internals.
- RepoBrain remains no-mutation:
  - no patch/autofix
  - no file changes in the target repo
  - no RepoBrain-created branch/commit/PR behavior
- TopoCore remains score authority.
- LLM remains narrative-only.

## Authentication and identity direction

Sprint 93A direction only:
- future partner authentication should use GitHub OIDC rather than owner-issued onboarding tokens
- future partner identity should be derived from verified GitHub claims and repository metadata
- future partner metadata should be auto-provisioned server-side

Sprint 93A itself did not claim that this identity envelope was already implemented.
Sprint 93B now implements the public action-side OIDC token acquisition and sanitized identity envelope.

## Reserved public action surface

Sprint 93A prepares an optional public action surface for future self-service rollout:
- `profile`
- `terms_accepted`
- `api_url`
- `oidc_audience`
- `self_service_mode`

Current truth:
- all reserved inputs are optional
- all reserved inputs are non-breaking
- none of them create a live self-service production path in this sprint by themselves

## Partner-facing workflow shape

The intended Phase 1 workflow shape includes:
- `contents: read`
- `issues: write`
- `pull-requests: write`
- `id-token: write`
- no RepoBrain owner-generated secret
- no TopoCore install step
- no TopoCore source checkout step

`id-token: write` is included now so Sprint 93B can activate OIDC identity acquisition without forcing a future workflow redesign.

## Data boundary

Intended later Phase 1 hosted request envelope:
- verified GitHub repository identity
- requested RepoBrain command
- bounded repository evidence
- workflow and run metadata needed for request validation and reporting

Not sent by default:
- full repository archive
- secrets
- private tokens
- TopoCore runtime files
- private backend traces
- manually collected partner metadata from the RepoBrain owner

## Reviewer notes output polish

Sprint 93A also closes the remaining partner-facing cosmetic defect on the PR premium audit path.

Direction taken:
- the deterministic canonical `PR impact summary` remains the authoritative PR facts block
- partner-facing `Reviewer notes` are removed from the final PR audit markdown path because they duplicate or partially repeat PR facts and create unnecessary truncation risk
- `Executive summary` now follows the complete deterministic PR sections without a broken reviewer fragment in between

## Current non-goals

Still deferred after trusted partner testing:
- no dashboard in Phase 1
- no owner/admin panel in Phase 1
- no GitHub App in Phase 1
- no additional cognitive core in Phase 1
- no enterprise self-hosted distribution in Phase 1
- no billing or subscription workflows in Phase 1

## Follow-up sprint handoff

Sprint 93B now provides:
- GitHub OIDC identity acquisition in the public action
- default OIDC audience behavior
- sanitized identity envelope construction
- clear failure path when `id-token: write` is missing in `self_service_mode`

Sprint 93C should implement:
- hosted API contract
- OIDC verification requirements
- automatic tenant provisioning
- quota profile
- public-safe response contract

Sprint 93C is now the implemented trust/provisioning boundary.

Sprint 93D should implement:
- end-to-end partner self-service workflow

Sprint 93E should implement:
- security hardening and trusted partner live validation
