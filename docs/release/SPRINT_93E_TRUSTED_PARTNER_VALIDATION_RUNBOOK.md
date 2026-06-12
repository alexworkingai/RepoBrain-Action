# Sprint 93E Trusted Partner Validation Runbook

Purpose:
- execute the final Phase 1 trusted-partner validation sequence for RepoBrain self-service onboarding
- preserve public-safe output, no-mutation behavior, and the private TopoCore boundary

Current status:
- Sprint 93E hardening can complete independently of live validation
- final Phase 1 PASS requires live validation evidence on both target repositories
- if the hosted endpoint or repo workflow configuration is not ready, leave status at `SPRINT_93E_HARDENING_READY_LIVE_VALIDATION_PENDING`

Primary validation repository:
- `alexworkingai/Elen-MCP-v.2.2.0`
- suggested validation branch: `repobrain-93e-self-service-validation`
- suggested workflow file: `.github/workflows/repobrain-self-service-pilot.yml`

Secondary validation repository:
- `alexworkingai/repobrain-community`
- suggested validation branch: `repobrain-93e-community-self-service-validation`
- suggested workflow file: `.github/workflows/repobrain-self-service-pilot.yml`
- local validation worktree: operator-local path intentionally omitted from tracked docs

Validation prerequisites:
- RepoBrain-Action branch or merged ref selected for validation
- explicit hosted API URL assigned to the partner workflow
- `self_service_mode: "true"`
- `terms_accepted: "true"`
- `id-token: write`
- no owner-generated onboarding token
- no manual partner registration path
- no TopoCore install/download path in the partner self-service workflow

Primary repository workflow preparation:
1. inspect `.github/workflows/repobrain.yml`
2. create or update the validation-only branch `repobrain-93e-self-service-validation`
2. confirm `issues: write`, `pull-requests: write`, and `id-token: write`
3. replace any private TopoCore checkout path for self-service validation with:
   - `api_url: <trusted-partner-endpoint>`
   - `self_service_mode: "true"`
   - `terms_accepted: "true"`
4. prefer repository variable `REPOBRAIN_HOSTED_API_URL` instead of a secret if the endpoint itself is not secret
5. do not use `TOPOCORE_V6_ARTIFACT_TOKEN`
6. do not use `TOPOCORE_V6_REPO_TOKEN`
7. do not install TopoCore
8. keep repo product logic unchanged outside workflow-only validation wiring

Secondary repository duplicate-responder preparation:
1. inspect `.github/workflows/`
2. identify any existing workflow that responds to `/repobrain`
3. create or update the validation-only branch `repobrain-93e-community-self-service-validation`
4. ensure only one workflow responds during validation
5. prefer `workflow_dispatch` first if duplicate responder risk remains unclear
6. avoid enabling `issue_comment` on the validation branch until duplicate responder risk is controlled
7. do not rewrite history
8. do not force push
9. do not delete tags or releases

Issue validation commands for both repositories:
- `/repobrain score`
- `/repobrain audit`
- `/repobrain audit --profile premium`

PR validation commands for both repositories:
- `/repobrain score`
- `/repobrain audit`
- `/repobrain audit --profile premium`

Evidence collection checklist:
- repository name
- workflow file used
- RepoBrain-Action ref or SHA
- sanitized hosted API endpoint identity
- issue URL
- PR URL
- command results for score, audit, and premium audit
- OIDC status
- tenant status
- quota status
- token leakage check
- TopoCore boundary check
- manual token check
- manual registration check
- mutation/autofix check
- PR impact summary check
- repobrain-community duplicate responder check

PASS conditions:
- workflow runs
- OIDC acquired
- hosted request accepted
- tenant auto-provisioned or updated
- quota ok or expected bounded public-safe status
- output rendered into Issue/PR comments
- no raw token leakage
- no private runtime or source exposure
- no owner token wording
- no manual registration wording
- no TopoCore install/download wording
- no patch/autofix or mutation
- no Marketplace/public-launch/security-certification claim

PR-specific PASS:
- docs-only PR facts remain canonical
- complete PR impact summary preserved
- no Reviewer notes truncation
- executive summary follows deterministic PR sections

If validation is blocked:
- record the exact blocker in `docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md`
- do not claim final PASS
- keep status at `SPRINT_93E_HARDENING_READY_LIVE_VALIDATION_PENDING`

Current observed blockers:
- `alexworkingai/Elen-MCP-v.2.2.0` still uses the older `private_checkout` workflow and does not yet expose `self_service_mode`, `terms_accepted`, `api_url`, and `id-token: write`
- `alexworkingai/Elen-MCP-v.2.2.0` does not currently expose `REPOBRAIN_HOSTED_API_URL`
- `alexworkingai/repobrain-community` still has a legacy responder surface and needs isolated validation wiring before safe `issue_comment` validation

Phase 2-4 remain deferred:
- partner dashboard
- owner/admin panel
- GitHub App model
- enterprise tier
- billing/subscription
- additional cognitive core attached to TopoCore v6
- broader Marketplace/public launch track
