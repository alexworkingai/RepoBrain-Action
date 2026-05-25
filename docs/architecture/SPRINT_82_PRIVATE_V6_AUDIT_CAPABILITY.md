# Sprint 82 Private v6 Audit Capability

## 1. Purpose

Sprint 82 implements and connects a real private TopoCore v6 audit scoring capability behind the Sprint 81 `topocore.audit_score.v1` contract.
It does not expose TopoCore source code.
It does not change public distribution strategy.

## 2. Baseline

- latest RepoBrain-Action `main` before Sprint 82:
  - `a59926f Record v6 audit contract live evidence`
- Sprint 81 status:
  - `V6_AUDIT_CONTRACT_READY_STATIC_RUNTIME`
- known limitation before Sprint 82:
  - the contract was present, but live audit remained static because a real private capability was not available

## 3. Private TopoCore Implementation

Safe private metadata only:

- private branch:
  - `codex/sprint-82-audit-score-v1-capability`
- private commit hash:
  - `4f5c58b`
- capability method:
  - `run_audit_score_v1`
- contract:
  - `topocore.audit_score.v1`
- private validation:
  - targeted public-facade and audit-capability tests passed
  - targeted lint checks passed
- source exposure:
  - none

No private source code is reproduced in RepoBrain-Action documentation.
No private local repository path is recorded here.

## 4. RepoBrain Adapter Integration

Files changed in RepoBrain-Action:

- `repobrain/audit_v6.py`
- `tests/test_audit_v6_backend_integration.py`

Integration behavior:

- detection path:
  - RepoBrain still uses the Sprint 81 optional capability seam through `repobrain/topocore_v6_adapter.py`
- invocation path:
  - RepoBrain now forwards `RB_TOPOCORE_V6_LOCAL_PATH` through the audit seam so local/private-checkout audit runs do not depend on ambient `PYTHONPATH`
- validation path:
  - all private responses still pass through the Sprint 81 response validator unchanged
- backend evidence semantics:
  - valid accepted private response -> `resolved_backend=v6`, `fallback_used=no`, `fallback_reason=none`
  - capability unavailable -> static contract-ready fallback
  - invalid or unsafe response -> rejected and downgraded to static

## 5. Contract Validation Result

- valid response accepted:
  - yes
- invalid response rejected:
  - yes
- unsafe response rejected:
  - yes
- missing capability behavior:
  - static scoring with v6 contract-ready guard remains intact

During Sprint 82, the private provider initially returned wording that the contract guard treated as unsafe approval language.
That was fixed in the private provider.
The RepoBrain guard was not weakened.

## 6. Live Elen-MCP Result

Pending live recording after RepoBrain-Action and the private provider are available on the runtime paths consumed by `alexworkingai/Elen-MCP-v.2.2.0`.

This section is updated after the live smoke run with:

- issue URL
- audit run URL
- audit mode
- static baseline
- v6-enriched score if available
- backend requested/resolved
- fallback used/reason
- contract guard result
- doctor and status runs
- safety result

## 7. Product Status

- `V6_AUDIT_CAPABILITY_IMPLEMENTED_LOCAL_ONLY`

## 8. Next Step

If live `v6` enrichment passes:

- Sprint 83 - v6 Audit UX Hardening and `/repobrain score` Decision

If runtime packaging or live wiring still blocks the provider:

- Sprint 83 - Live Wiring and Runtime Packaging for v6 Audit Capability

## 9. Non-Goals

- no v5
- no repobrain-community
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no public TopoCore distribution
- no TopoCore source exposure
- no `/repobrain score` unless explicitly approved
- no Microsoft partnership claim
