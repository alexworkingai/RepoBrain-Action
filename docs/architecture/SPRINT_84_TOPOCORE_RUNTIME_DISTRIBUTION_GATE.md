# Sprint 84 - TopoCore Runtime Distribution Gate

## 1. Purpose

Sprint 84 resolves or narrows the TopoCore runtime distribution gate for public-ready partner testing.

## 2. Baseline

- latest main before Sprint 84: `d6474cd Record v6 audit score live evidence`
- Sprint 83 status: `V6_AUDIT_UX_SCORE_READY`
- current blocker before Sprint 84: private runtime distribution and public-ready gate

## 3. Runtime Distribution Discovery

Current discovery result:

- current external pilot path still uses `private_checkout`
- RepoBrain runtime now supports explicit mode selection through `RB_TOPOCORE_V6_RUNTIME_MODE`
- diagnostics can distinguish installed package, private checkout, local path, and disabled modes
- private package build is feasible from the existing private TopoCore repo
- installed package import is feasible in a clean environment
- package artifact excludes tests and docs from the installed wheel payload
- package artifact still contains readable Python implementation files, so it reduces exposure but does not equal strong source secrecy
- Node 20 warning source was traced to older action majors in workflow refs rather than RepoBrain Python runtime logic

## 4. Distribution Decision

- decision: `INSTALLED_PRIVATE_PACKAGE_SELECTED`

Rationale:
- safer than source checkout for selected partner testing
- compatible with the existing `run_audit_score_v1` public facade
- honest about wheel readability limitations
- sufficient for selected partner testing after owner approval

## 5. Runtime Mode Implementation

Implemented in Sprint 84:

- `RB_TOPOCORE_V6_RUNTIME_MODE`
- allowed values: `auto`, `installed_package`, `private_checkout`, `local_path`, `disabled`
- adapter import/runtime diagnostics distinguish requested mode from used mode
- validation scripts now report sanitized runtime mode, package availability, local-path presence, and audit capability presence
- doctor and status now report runtime mode truth without printing private paths

## 6. Private TopoCore Packaging Result

- private TopoCore changes: not required for Sprint 84
- private capability baseline from Sprint 82 was reused
- runtime artifact build test: passed locally
- installed artifact import and `run_audit_score_v1` capability check: passed locally
- artifact source exposure truth: plain wheel still contains readable Python implementation files
- no source details are recorded here

## 7. Partner Access Model

- per-partner token or equivalently scoped credential
- read-only access
- expiration required
- rotation required
- revocation on incident or offboarding
- no shared broad PAT
- no automatic source-repo access grant

## 8. Node 20 / Action Runtime Hygiene

- warning source: older `actions/*` major refs in workflows and example workflow
- Sprint 84 action-ref hygiene: updated to newer majors in RepoBrain workflows and example workflow
- no permission broadening was introduced

## 9. Public Readiness Decision

- `PUBLIC_READY_PENDING_OWNER_APPROVAL`

Meaning:
- Sprint 84 no longer depends on source checkout as the preferred partner path
- RepoBrain-Action still remains private until explicit owner approval
- Marketplace remains out of scope

## 10. Live Elen-MCP Result

Record live Sprint 84 evidence here after run:

- audit run: pending
- score run: pending
- doctor run: pending
- status run: pending
- mode: pending
- backend: pending
- safety: pending

## 11. Product Status

- `TOPOCORE_RUNTIME_DISTRIBUTION_GATE_PASSED`

## 12. Next Step

If owner approval is granted:
- Sprint 85 - Release Candidate Tag, Public Visibility Approval Checklist, and Partner Test Pack

## 13. Non-Goals

- no v5
- no repobrain-community
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no public TopoCore source distribution
- no Microsoft partnership claim
