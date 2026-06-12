# Sprint 93B OIDC Identity Envelope

## Purpose

Sprint 93B implemented the public action side of the GitHub OIDC identity flow.

This sprint did not make partner self-service fully live.
It added action-side token acquisition, a sanitized identity envelope, and safe gating while preserving the private TopoCore boundary.

## Sprint 94A Correction Notice

After Sprint 93E live validation, the hosted path was reclassified as experimental and future external-runtime mode because it still requires a real deployed runtime.
The default trusted beta direction is now the GitHub-native control plane documented in `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`.

## Implemented In Sprint 93B

- GitHub Actions OIDC token acquisition through the action runtime when `id-token: write` is available
- default OIDC audience handling with `repobrain-api`
- optional custom audience through `oidc_audience`
- sanitized `repobrain.github_oidc_identity.v1` envelope construction
- safe `self_service_mode` gating for:
  - `terms_accepted: "true"`
  - GitHub OIDC availability
- backward-compatible non-self-service behavior when `self_service_mode` is disabled

## Foundation Value After 94A

These identity foundations remain reusable for:
- future hosted runtimes
- GitHub-native control-plane verification
- GitHub App and worker-side trust checks
- hosted verification and tenant provisioning boundaries defined later in Sprint 93C

## Current Status

- Sprint status: `SPRINT_93B_OIDC_IDENTITY_ENVELOPE_READY`
- Not claimed: `PARTNER_SELF_SERVICE_PUBLIC_ACTION_FULLY_LIVE`
- Hosted runtime path is now experimental and future-facing
- Next architecture stage: Sprint 94B for GitHub App installation foundation
