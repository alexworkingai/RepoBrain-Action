# Partner Testing Readiness

## 1. Purpose

This document defines the selected-partner testing state after the Sprint 91 public visibility switch.

## 2. Current Status

- RepoBrain-Action is public in Sprint 91.
- TopoCore remains private.
- Elen-MCP remains private.
- Marketplace work has not started.
- owner approval for the public visibility switch was recorded and executed.
- post-switch public-action smoke on Elen-MCP passed for doctor, status, audit, score, and ask.
- Sprint 92C live issue and PR retest on Elen-MCP passed for ask, locate, explain, review, verify, fix, audit, and score.
- operational ask quality is materially improved for runtime/workflow/public-readiness questions.
- issue ask may use an LLM only when safe policy allows.
- deterministic retrieval and TopoCore-backed synthesis remain valid when issue-mode LLM policy or provider availability prevents an LLM call.
- issue ask analyzes the current consumer repository and its visible product surface unless the target repository actually is RepoBrain-Action.
- PR ask is expected to stay scoped to the PR and summarize change impact rather than produce a generic product overview.
- route labels now reflect the typed command rather than internal analysis mode.
- enterprise P0 hardening remains in force after the switch.
- PR `#119` merged the protected-main UX polish without admin bypass.
- dependency graph enabled on the public RepoBrain repository.
- dependency review passed on PR `#119`.
- the public RepoBrain repository currently runs under a solo-owner protected-main baseline with force-push/deletion blocking and linear-history protection.
- required status checks and CODEOWNERS review enforcement remain intentionally deferred while stable check names are locked.
- current public readiness status on the Sprint 92E branch: `SPRINT_92D_IMPLEMENTATION_MERGED_LIVE_RETEST_FINDINGS_PENDING_FIX`.
- Sprint 92A manual issue smoke hotfix passed for help, doctor, status, ask, locate, explain, audit, score, and the deprecated lite-alias regression.
- historical Sprint 91 post-switch status remains recorded as: `PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY`.
- historical Sprint 90 readiness remains recorded as: `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`.
- historical Sprint 88 / Sprint 89 gate remains recorded as: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`.
- historical Sprint 87 blocker remains recorded as: `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`.
- historical Sprint 86 blocker remains recorded as: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`.

## 3. Partner Prerequisites

- GitHub repository admin access for the consumer repository
- allowed GitHub Actions policy for external actions
- public RepoBrain action reference: `alexworkingai/RepoBrain-Action@main` until a separately approved tag exists
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
- `private_checkout` remains controlled beta-only fallback for owner-controlled or tightly managed pilots
- selected partner testing should prefer installed private package mode
- stronger managed-runtime or compiled-artifact protection is future work
- Sprint 90 decisive result:
  - owner-issued artifact credential present
  - artifact preflight passed
  - private source checkout stayed avoided in the external proof branch
  - external proof reached real `v6` in `installed_package` mode
  - control smoke on the normal `private_checkout` path remained green
- Sprint 91 public-action smoke result:
  - RepoBrain-Action public action source remained usable from Elen-MCP
  - doctor/status/audit/score/ask all passed post-switch
- Sprint 92E fix target:
  - issue ask should analyze the consumer repository being tested, not RepoBrain-Action internals
  - PR ask should stay PR-scoped and assess change impact
  - doctor/status/review/fix defaults should remain compact and partner-facing

Honest limitation:
- a normal Python package artifact can still contain readable implementation files
- selected partner testing therefore remains controlled and approval-based even when source checkout is avoided
- Sprint 91 starts selected partner pilot kickoff but does not start Marketplace work

## 6. Security Expectations

- no TopoCore source license is granted
- no mutation
- no patch/autofix
- no shared broad PAT
- no `pull_request_target`
- read-mostly workflow permissions by default
- `pull-requests: write` is allowed only when it is narrowly scoped to RepoBrain PR command response comments
- the justified PR comment response permission is monitored and must not drift into mutation-capable workflow behavior
- protected main baseline is enabled on the public RepoBrain repository
- required status checks and CODEOWNERS enforcement remain deferred until stable check names are locked
- `contents: write` remains out of scope for normal partner setup
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

- ask and explain diagnostics must state whether the LLM was actually called; no-LLM answers can still come from deterministic retrieval, workflow inspection, and TopoCore v6 signals
- default GitHub comments intentionally hide raw TKY/TKYA internals; expanded sanitized diagnostics move to verbose/artifact mode
- Sprint 92C live retest confirmed compact default comments on both issue and PR paths while preserving verbose/artifact debug paths for deeper investigation
- no Marketplace
- no public TopoCore distribution
- no patch/autofix
- static fallback remains available when authorized `v6` runtime is absent
- `v6` enrichment requires authorized runtime access
- RC tag creation remains pending separate owner approval
- public visibility does not imply TopoCore source rights or broad public runtime distribution
