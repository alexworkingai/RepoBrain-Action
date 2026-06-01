# Public Visibility Approval Checklist

## 1. Purpose

This is the final checklist before making `RepoBrain-Action` public for selected partner testing.

## 2. Current State

- RepoBrain-Action is still private.
- Public visibility is not switched in Sprint 86, Sprint 87, Sprint 88, Sprint 89, or Sprint 90.
- Marketplace work is not started.
- Current product status: `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`.
- Historical Sprint 88 / Sprint 89 gate remains recorded as: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`.
- Historical Sprint 87 blocker remains recorded as: `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`.
- Historical Sprint 86 blocker remains recorded as: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`.
- Sprint 85 approval-pack state remains recorded as: `PUBLIC_VISIBILITY_APPROVAL_PACK_READY`.

## 3. Approval Decision

- explicit owner approval is required before any public visibility change, RC tag creation, or selected partner rollout
- owner approves public visibility: `no` / pending explicit decision
- owner approves selected partner testing: `no` / pending explicit decision
- owner approves RC tag creation: `no` / pending explicit decision
- owner approves partner runtime/token issuance: `no` / pending explicit decision

## 4. Technical Readiness

- command surface is complete
- audit live `v6`-enriched scoring passed on the normal controlled runtime path
- score live `v6`-enriched scoring passed on the normal controlled runtime path
- doctor and status live passed
- operational ask quality returns workflow/runtime/public-readiness status cleanly
- runtime mode is explicit
- `installed_private_package` is selected for selected partner testing
- `private_checkout` remains beta-only fallback
- validation is green
- enterprise P0 hardening adds SECURITY / CONTRIBUTING / CODEOWNERS, supply-chain workflows, governance documentation, and mutation-surface cleanup
- release, onboarding, command, and troubleshooting docs are updated
- external installed-package delivery path is now live-proven without private source checkout

## 5. Security Readiness

- TopoCore source remains private
- no TopoCore source license is granted
- no TopoCore source is present in RepoBrain-Action
- no private checkout evidence is surfaced in audit or score output
- no secrets are present in tracked docs or logs
- per-partner scoped credentials are required
- no shared broad PAT is permitted
- revocation plan is documented
- no `pull_request_target` in the external baseline
- read-mostly workflow permissions remain required

## 6. Legal and Licensing Readiness

- custom BYO-LLM source-available license exists
- users bring and pay for their own LLM/model access
- RepoBrain is not an LLM reseller
- commercial SaaS/resale restrictions remain documented
- no TopoCore source rights are granted

## 7. Partner Readiness

- partner setup pack is complete
- partner feedback template is complete
- partner troubleshooting path is complete
- runtime/token issuance runbook is complete
- Sprint 90 verified the owner-issued artifact credential path and completed decisive installed-package proof
- installed-package rollout is no longer blocked by runtime proof; the remaining gate is explicit owner approval for the public switch and selected partner pilot

## 8. Public Switch Procedure

Pre-switch checks:

1. confirm owner approval is explicit and recorded
2. confirm the repository is still private before the switch
3. confirm no secret, token-like, or private-path residue remains in tracked files
4. confirm partner runtime/token issuance process is ready for first testers
5. confirm selected partner docs point to the correct runtime distribution mode
6. confirm installed-package delivery remains scoped and source-checkout-free

Switch step:

- perform the GitHub visibility change manually in the repository settings or by an approved operator command
- do not run visibility switching automatically from RepoBrain

Immediate post-switch checks:

1. README renders correctly
2. LICENSE is visible
3. `action.yml` is visible
4. install docs are visible
5. partner docs are visible
6. no secret, token-like, or private-path residue is exposed
7. no private TopoCore source is present

Rollback note:

- public exposure cannot be fully undone if the repository is cloned before rollback
- verify carefully before switching visibility

## 9. Final Decision

- `APPROVAL_PENDING`
- technical runtime gate is closed
- remaining gate: explicit owner approval

Other allowed outcomes:

- `APPROVED_FOR_PUBLIC_PARTNER_TESTING`
- `APPROVAL_PENDING`
- `BLOCKED_BY_SECURITY`
- `BLOCKED_BY_DOCS`
- `BLOCKED_BY_RUNTIME`
- `BLOCKED_BY_LEGAL`
- `BLOCKED_BY_VALIDATION`
