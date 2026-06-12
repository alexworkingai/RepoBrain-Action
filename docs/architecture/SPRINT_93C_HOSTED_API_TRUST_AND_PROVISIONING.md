# Sprint 93C Hosted API Trust And Provisioning

## Purpose

Sprint 93C implemented the hosted RepoBrain API trust boundary for the earlier self-service line.

This sprint did not make partner self-service fully live.
It defined and validated the hosted request and response contract, server-side GitHub OIDC verification, claim consistency checks, automatic tenant provisioning concepts, quota enforcement, and the private hosted TopoCore adapter boundary.

## Sprint 94A Correction Notice

After Sprint 93E live validation, the hosted path was reclassified as experimental and future external-runtime mode because it still requires a real deployed runtime.
The default trusted beta direction is now the GitHub-native control plane documented in `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`.

## Hosted API Contract Value Preserved

The hosted contract remains useful for future backend-compatible transport work:
- `POST /v1/github/actions/audit`
- server-side GitHub OIDC verification
- automatic tenant provisioning
- default partner-pilot quota boundary
- private hosted TopoCore boundary
- endpoint contract shape
- identity versioning
- tenant and quota versioning
- public-safe response handling
- private runtime boundary definitions

## Current Status

- Sprint status target remains historical: `SPRINT_93C_HOSTED_API_TRUST_AND_AUTO_PROVISIONING_READY`
- Not claimed: `PARTNER_SELF_SERVICE_PUBLIC_ACTION_FULLY_LIVE`
- Hosted runtime remains experimental and future-facing until a real external runtime exists
- Next architecture stage after correction: Sprint 94B and Sprint 94C for GitHub-native control-plane work
