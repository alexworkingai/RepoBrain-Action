# RepoBrain Sprint 93E Community Self-Service Smoke

Target repository:
- `alexworkingai/repobrain-community`

Local validation path:
- operator-local worktree path intentionally omitted from tracked docs

Purpose:
- validate the public standalone or migration-style self-service path on a secondary repository
- ensure no duplicate `/repobrain` responders remain active during validation

Preflight:
- inspect `.github/workflows/`
- identify every workflow that reacts to `/repobrain`
- ensure only one validation workflow responds during Sprint 93E smoke
- prefer a validation branch or dedicated validation workflow
- do not delete legacy community workflow files unless separately approved

Issue commands:
- `/repobrain score`
- `/repobrain audit`
- `/repobrain audit --profile premium`

PR commands:
- `/repobrain score`
- `/repobrain audit`
- `/repobrain audit --profile premium`

Validation checks:
- OIDC acquired
- hosted API request accepted
- tenant auto-provisioned or updated
- quota status is bounded and public-safe
- no owner-generated onboarding token
- no manual partner registration
- no TopoCore install or download wording
- no raw token leakage
- no private runtime or source leakage
- no duplicate responders
- no accidental legacy `/repobrain doctor`, `/repobrain review`, or `/repobrain fix` activation

PR-specific checks:
- docs-only PR facts remain canonical when applicable
- PR impact summary remains complete
- Reviewer notes do not regress
- no mutation or patch/autofix behavior appears
