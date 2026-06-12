# Sprint 93D End-to-End Partner Self-Service Workflow

Correction notice:
After Sprint 93E live validation, the `hosted_api` path was reclassified as experimental and future external-runtime mode because it requires a deployed hosted API.
The default trusted beta path is now the GitHub-native control plane documented in `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`.

Purpose:
- wire the public RepoBrain action to the Sprint 93C hosted trust and provisioning boundary
- keep the public action as a thin client
- preserve TopoCore as a private hosted or server-side runtime only

Historical truth after Sprint 93D:
- supported self-service commands are `ask`, `audit`, and `score`
- `self_service_mode: "true"` required:
  - `terms_accepted: "true"`
  - GitHub OIDC availability through `id-token: write`
  - explicit `api_url` for hosted routing
- the action sends `repobrain.github_action_audit_request.v1` to the hosted API path
- the action renders public-safe hosted success and error responses back into the existing GitHub comment flow
- existing non-self-service flow remains unchanged

Reusable foundations from Sprint 93D:
- action-side hosted API client
- versioned request sending for supported self-service commands
- bounded evidence packet construction
- hosted response rendering into issue comments, PR comments, and workflow-dispatch simulation output
- public-safe hosted error rendering

What Sprint 93D does not claim:
- unrestricted public self-service launch
- Marketplace readiness
- final trusted-partner validation
- final security hardening signoff
- TopoCore source or runtime distribution to partner runners

Current 94A framing:
- hosted transport remains useful for future production-compatible runtimes
- hosted transport is not the default trusted beta path anymore
- the next implementation stages move to GitHub App identity, GitHub-native queueing, and a private control worker
