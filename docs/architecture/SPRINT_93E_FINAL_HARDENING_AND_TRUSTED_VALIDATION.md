# Sprint 93E Final Hardening And Trusted Validation

Purpose:
- complete the final hardening pass for the Phase 1 self-service onboarding path
- prepare the trusted-partner live validation package without overclaiming public-launch readiness

Current status:
- `SPRINT_93E_HARDENING_READY_LIVE_VALIDATION_PENDING`

Sprint 93E hardening scope:
- preserve strict `self_service_mode` gating
- preserve OIDC-only identity acquisition for self-service
- preserve hosted API trust and quota boundaries
- strengthen public-safe request and error handling
- finalize trusted validation runbooks and evidence templates

Code-level hardening completed in Sprint 93E:
- hosted client rejects unexpected redirect responses
- public-safe non-JSON and invalid-response failures remain bounded
- requested command profile, including `premium`, is preserved in the hosted request payload
- the redacted hosted request preview now matches the actual requested command profile
- non-self-service behavior remains unchanged

Trusted validation repositories:
- primary: `alexworkingai/Elen-MCP-v.2.2.0`
- secondary: `alexworkingai/repobrain-community`

Validation artifacts:
- runbook: `docs/release/SPRINT_93E_TRUSTED_PARTNER_VALIDATION_RUNBOOK.md`
- evidence template: `docs/release/SPRINT_93E_PHASE1_VALIDATION_EVIDENCE.md`
- primary smoke checklist: `docs/repobrain_93e_self_service_smoke.md`
- secondary smoke checklist: `docs/repobrain_93e_community_self_service_smoke.md`

Truth boundary:
- do not claim unrestricted public launch
- do not claim Marketplace readiness
- do not claim enterprise readiness
- do not claim production, security, legal, or merge approval
- do not introduce owner-generated onboarding tokens or manual partner registration

Live-validation gate:
- final Phase 1 PASS requires Issue and PR validation on both selected repositories
- `repobrain-community` validation must explicitly prevent duplicate responders
- if hosted endpoint or workflow readiness is missing, keep the pending status and document the exact blocker

Current observed blockers at Sprint 93E hardening close:
- `alexworkingai/Elen-MCP-v.2.2.0` still uses the older private-checkout runtime workflow and does not yet expose the self-service `api_url`, `terms_accepted`, `self_service_mode`, and `id-token: write` combination needed for live trusted-partner proof
- `alexworkingai/repobrain-community` still exposes a legacy community responder surface, so duplicate-responder isolation must be solved before safe self-service validation

Allowed ready wording after live PASS:
- `PHASE_1_TRUSTED_PARTNER_SELF_SERVICE_READY`
- `PARTNER_SELF_SERVICE_TRUSTED_PILOT_READY`

Deferred after Sprint 93E:
- partner dashboard
- owner or admin panel
- GitHub App onboarding
- enterprise tier
- billing or subscription flows
- broader Marketplace track
