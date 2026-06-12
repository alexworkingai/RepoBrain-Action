# Sprint 93A Self-Service Partner Foundation

## Purpose

Sprint 93A prepared the first public self-service partner foundation for RepoBrain-Action while preserving all current safety and private-runtime boundaries.

This sprint did not make partner self-service fully live.
It established the public thin-client direction, reserved configuration surface, and partner-facing documentation that later sprints built on.

## Sprint 94A Correction Notice

After Sprint 93E live validation, the hosted path was reclassified as experimental and future external-runtime mode because it still requires a real deployed runtime.
The default trusted beta direction is now the GitHub-native control plane documented in `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`.

## Core Foundation Contract

- RepoBrain-Action is the public thin client.
- TopoCore remains a private external capability provider.
- TopoCore remains a private hosted and server-side runtime in the historical Phase 1 direction.
- Partners must not receive TopoCore source, package rights, or container rights as part of the intended GitHub-native beta direction.
- Partners must not receive TopoCore source, package, or container in the intended thin-client model.
- Partners must not install TopoCore in the intended thin-client model.
- Public RepoBrain workflows may collect only bounded repository evidence.
- Public RepoBrain output must remain public-safe and must not expose private runtime paths, raw traces, secrets, or private checkout internals.
- RepoBrain remains no-mutation:
  - no patch or autofix
  - no file changes in the target repo
  - no RepoBrain-created branch, commit, or PR behavior
- TopoCore remains score authority.
- LLM remains narrative-only.

## Authentication And Identity Direction

Sprint 93A direction only:
- future partner authentication should use GitHub-derived identity rather than owner-issued onboarding tokens
- future partner identity should be derived from verified GitHub claims and repository metadata
- future partner metadata should be auto-provisioned or auto-resolved on the control side

Sprint 93A itself did not claim that this identity envelope was already implemented.
Sprint 93B later implemented the action-side OIDC token acquisition and sanitized identity envelope.

## Reserved Public Action Surface

Sprint 93A prepared an optional public action surface for future rollout:
- `profile`
- `terms_accepted`
- `api_url`
- `oidc_audience`
- `self_service_mode`

Current truth:
- all reserved inputs are optional
- all reserved inputs are non-breaking
- none of them create a live trusted beta path by themselves

## Current Non-Goals

Still deferred after Sprint 94A correction:
- no dashboard in this phase
- no owner or admin panel in this phase
- no GitHub App in Phase 1
- no Marketplace packaging as the immediate route
- no TopoCore internal development in RepoBrain
- no enterprise self-hosted distribution in this phase
- no billing or subscription workflows in this phase

## Follow-Up Sprint Handoff

Useful follow-up path after 94A:
- Sprint 93B now provides the action-side OIDC identity envelope foundation.
- Sprint 93C should implement the hosted API contract, hosted verification, automatic tenant provisioning, quota profile, and public-safe response contract in the historical hosted line.
- Sprint 93D should implement the end-to-end partner self-service workflow in the historical hosted line.
- Sprint 93E should implement security hardening and trusted partner live validation in the historical hosted line.
- 94B: GitHub App installation foundation
- 94C: GitHub-native request queue
- 94D: private control worker plus TopoCore entrypoint execution
- 94E: trusted partner beta validation
- 94F: public developer beta without Marketplace
