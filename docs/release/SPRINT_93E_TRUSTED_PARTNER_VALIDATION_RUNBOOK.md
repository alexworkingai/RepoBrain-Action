# Sprint 93E Trusted Partner Validation Runbook

Purpose:
- preserve the historical Sprint 93E hosted validation runbook
- record why the hosted validation line stopped before final PASS
- redirect future beta validation to the GitHub-native control-plane path defined by Sprint 94A

Current historical status:
- `SPRINT_93E_HARDENING_MERGED`
- `HOSTED_API_RUNTIME_GAP_IDENTIFIED`
- `GITHUB_NATIVE_ARCHITECTURE_CORRECTION_REQUIRED`
- `PHASE_1_TRUSTED_PARTNER_SELF_SERVICE_READY_NOT_CLAIMED`

Historical context:
- Sprint 93E successfully hardened hosted request and response handling
- external workflow fixes later proved that the action can reach the hosted path when configured
- live validation then stopped because no real hosted runtime existed behind the configured endpoint shape
- this was a runtime availability gap, not an MCP output-format failure

Primary historical validation repository:
- `alexworkingai/Elen-MCP-v.2.2.0`

Secondary historical validation repository:
- `alexworkingai/repobrain-community`

Historical hosted validation prerequisites:
- RepoBrain-Action branch or merged ref selected for validation
- explicit hosted API URL assigned to the partner workflow
- `self_service_mode: "true"`
- `terms_accepted: "true"`
- `id-token: write`
- no owner-generated onboarding token
- no manual partner registration path
- no TopoCore install or download path in the partner self-service workflow

What Sprint 93E did validate usefully:
- public-safe hosted request preview behavior
- public-safe hosted error behavior
- redirect rejection hardening
- profile preservation for `/repobrain audit --profile premium`
- no mutation and no TopoCore source exposure in the public action surface

Why the hosted line stopped:
- no actual hosted runtime existed to satisfy the configured endpoint path
- MCP and community workflow fixes should not be treated as final trusted beta validation by themselves
- final Phase 1 PASS was never claimed

Current correction guidance:
- do not treat `REPOBRAIN_HOSTED_API_URL` as the default trusted beta requirement
- do not tell partners to configure placeholder hosted endpoint values
- redirect future trusted beta validation to Sprint 94E GitHub-native control-plane validation

Future beta validation direction:
- public `RepoBrain-Action`
- GitHub-native request marker or queue item
- private control worker
- GitHub App installation token
- private TopoCore entrypoint
- public-safe Issue or PR response

Deferred after this historical runbook:
- GitHub-native queue implementation
- GitHub App installation flow
- private control worker execution path
- trusted partner beta validation on the corrected architecture
- Marketplace track
