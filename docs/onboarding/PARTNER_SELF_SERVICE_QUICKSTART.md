# Partner Self-Service Quickstart

Purpose:
- explain the corrected beta onboarding direction after Sprint 94A
- preserve truthful status for experimental hosted foundations without sending partners to a fake hosted endpoint

Current truth:
- `RepoBrain-Action` is the public GitHub action surface
- TopoCore v6 remains private
- Sprints 93A-93E produced useful self-service identity, contract, hosted client, and public-safe rendering foundations
- the `hosted_api` path requires a real external runtime and is not the default GitHub-native beta path
- the near-term trusted beta target is a GitHub-native control plane
- GitHub Marketplace is not the immediate route
- trusted partners should wait for GitHub App and control-worker beta instructions from Sprints 94B-94E

Historical Phase 1 truth:
- this remains a Phase 1 foundation
- it is not a completed production path yet
- it is not yet fully live
- Sprint 93B implements the action-side OIDC identity envelope
- hosted API verification is implemented as a Sprint 93C boundary
- automatic tenant provisioning is implemented as a Sprint 93C boundary
- Sprint 93D now wires the end-to-end action-to-hosted flow for supported commands
- Sprint 93E provided the historical hardening and validation package

## Current Beta Path

Current beta path:
1. RepoBrain team prepares the GitHub App installation foundation.
2. Trusted partner installs the RepoBrain GitHub App when invited.
3. Partner adds the public `RepoBrain-Action` workflow.
4. Partner runs `/repobrain score`, `/repobrain audit`, or `/repobrain audit --profile premium`.
5. A private control worker processes the request through private TopoCore.
6. The result is posted back to GitHub as a public-safe comment.

This flow is being implemented in Sprints 94B-94E.

## What To Use Right Now

Use these documents as the current truthful entrypoints:
- architecture correction: `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`
- install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`

## Experimental Hosted Mode

Hosted self-service remains available only as an experimental and future external-runtime mode.

Current truth:
- it depends on a real external runtime
- it is useful for future production-compatible transport work
- it is not the default trusted beta path
- trusted beta partners must not be told to create fake `REPOBRAIN_HOSTED_API_URL` values
- placeholder `api_url` examples are for documentation shape only, not for live beta onboarding
- no RepoBrain owner-generated secret is required for the intended path
- no RepoBrain owner token is required for the intended path
- no RepoBrain-issued partner token is the intended model
- no manual partner registration is the intended model
- no manual partner metadata intake is the intended model
- do not install or download TopoCore
- TopoCore v6 remains private and server-side

## Why `id-token: write` Still Matters

`id-token: write` remains part of the foundation because Sprint 93B added GitHub OIDC acquisition and a sanitized identity envelope.

Those foundations still matter because they can be reused in:
- future hosted runtimes
- GitHub-native control-plane trust checks
- GitHub App or worker-side verification layers

## TopoCore Boundary

Always preserve these rules:
- TopoCore is a separate team and system
- RepoBrain does not implement TopoCore internals
- RepoBrain integrates TopoCore through stable contracts and capability responses
- partners must not receive TopoCore source rights from RepoBrain onboarding
- public RepoBrain output must remain public-safe

## What This Quickstart Does Not Claim

Do not claim from this quickstart alone:
- Phase 1 trusted-partner self-service ready
- partner self-service trusted pilot ready
- Marketplace ready
- public launch ready
- enterprise ready
- production approved
- security certified
- hosted beta readiness from only setting `REPOBRAIN_HOSTED_API_URL`

## Historical Sprint 93E Note

Sprint 93E hardened the hosted foundations and produced validation documents.
Those artifacts remain useful as historical implementation evidence, but the live hosted validation line is now superseded by Sprint 94A architecture correction because no real hosted runtime exists.
