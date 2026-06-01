# Partner Testing Readiness

## 1. Purpose

This document prepares RepoBrain for selected partner testing after explicit owner approval and any future public visibility switch.

## 2. Current Status

- RepoBrain-Action remains private in Sprint 86, Sprint 87, Sprint 88, and Sprint 89.
- Public visibility has not been switched.
- Marketplace work has not started.
- final public visibility still requires explicit owner approval.
- final issue-comment smoke on Elen-MCP passed for doctor, status, audit, score, and ask.
- operational ask quality is materially improved for runtime/workflow/public-readiness questions.
- enterprise P0 hardening is complete enough to isolate the remaining blocker.
- current public-switch blocker: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`.
- historical Sprint 87 blocker remains recorded as: `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`.
- historical Sprint 86 blocker remains recorded as: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`.

## 3. Partner Prerequisites

- GitHub repository admin access for the consumer repository
- allowed GitHub Actions policy for external actions
- RepoBrain-Action public visibility only after explicit owner approval
- authorized TopoCore runtime access according to the chosen mode
- BYO-LLM or user-paid model/provider access when needed

## 4. Supported Commands

- `/repobrain help`
- `/repobrain ask`
- `/repobrain locate`
- `/repobrain explain`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`
- `/repobrain audit`
- `/repobrain score`
- `/repobrain doctor`
- `/repobrain status`

## 5. Runtime Distribution Mode

Chosen near-term mode:
- `installed_private_package`

Current truth:
- `private_checkout` remains beta-only for owner-controlled or tightly managed pilots
- selected partner testing should prefer installed private package mode
- stronger managed-runtime or compiled-artifact protection is future work
- Sprint 86 live-proof result:
  - local packaging/install proof: passed
  - external installed-package delivery proof: blocked
- Sprint 87 live-proof result:
  - private source checkout still avoided in the external proof branch
  - exact blocker moved from generic runtime-proof uncertainty to `TOKEN_SCOPE_NOT_READY`
- Sprint 88 authorization result:
  - selected GitHub-supported path is now `fine_grained_pat_actions_read_artifact_download`
  - partner rollout must not start on installed-package mode until the owner issues the minimum-scope artifact credential and external proof reaches real `v6`
- Sprint 89 owner-token result:
  - the owner-token gate was rechecked
  - `TOPOCORE_V6_ARTIFACT_TOKEN` was still absent in `alexworkingai/Elen-MCP-v.2.2.0`
  - no decisive installed-package proof rerun is claimed

Honest limitation:
- a normal Python package artifact can still contain readable implementation files
- selected partner testing therefore remains controlled and approval-based even when source checkout is avoided

## 6. Security Expectations

- no TopoCore source license is granted
- no mutation
- no patch/autofix
- no shared broad PAT
- no `pull_request_target`
- read-mostly workflow permissions only
- per-partner or equally scoped runtime access only
- token rotation and revocation required

## 7. Partner Access Model

- per-partner token or equivalent scoped credential
- read-only access
- expiration required
- no shared owner token
- no source-repo collaborator access unless explicitly approved
- package/artifact scope preferred over source-repo scope where feasible
- revocation and audit-log review on offboarding or incident

## 8. Feedback Requested From Partners

- install friction
- audit and score quality
- false positives and false negatives
- command UX
- docs clarity
- security concerns
- repository type coverage

## 9. Known Limitations

- no Marketplace
- no public TopoCore distribution
- no patch/autofix
- static fallback remains available when authorized `v6` runtime is absent
- `v6` enrichment requires authorized runtime access
- RC tag creation remains pending owner approval
- installed-package external delivery remains blocked until `TOPOCORE_V6_ARTIFACT_TOKEN` is issued with the selected minimum scope and the external artifact proof passes without source checkout
