# RepoBrain 93E Self-Service Smoke

Target repository:
- `alexworkingai/Elen-MCP-v.2.2.0`

Goal:
- validate trusted-partner self-service onboarding on a realistic product repository

Issue commands:
```text
/repobrain score
/repobrain audit
/repobrain audit --profile premium
```

PR commands:
```text
/repobrain score
/repobrain audit
/repobrain audit --profile premium
```

Check during each run:
- OIDC acquired
- hosted request accepted
- tenant auto-provisioned or updated
- quota status public-safe
- no raw token leakage
- no private runtime/source exposure
- no owner token/manual registration wording
- no TopoCore install/download wording
- no patch/autofix/mutation
- no Marketplace/public-launch overclaim

PR-specific checks:
- docs-only PR facts canonical
- complete PR impact summary
- no Reviewer notes truncation
- executive summary follows deterministic PR sections
