# Sprint 93D End-to-End Partner Self-Service Workflow

Purpose:
- wire the public RepoBrain action to the Sprint 93C hosted trust/provisioning boundary
- keep the public action as a thin client
- preserve TopoCore v6 as a private hosted/server-side runtime only

Current truth after Sprint 93D:
- supported self-service commands are `ask`, `audit`, and `score`
- `self_service_mode: "true"` now requires:
  - `terms_accepted: "true"`
  - GitHub OIDC availability through `id-token: write`
  - explicit `api_url` for hosted routing
- the action now sends `repobrain.github_action_audit_request.v1` to the hosted API path
- the action now renders public-safe hosted success and error responses back into the existing GitHub comment flow
- existing non-self-service flow remains unchanged

What Sprint 93D wires:
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

What remains for Sprint 93E:
- final hardening review
- trusted-partner live validation
- no-overclaim final pass
- final Phase 1 readiness decision
