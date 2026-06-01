# Public Visibility Approval Checklist

## 1. Purpose

This is the final checklist record for making `RepoBrain-Action` public for selected partner testing.

## 2. Current State

- RepoBrain-Action is now public.
- Public visibility was switched in Sprint 91 after validated pre-switch checks.
- TopoCore remains private.
- Elen-MCP remains private.
- Marketplace work is not started.
- Current product status: `PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY`.
- Historical Sprint 88 / Sprint 89 gate remains recorded as: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`.
- Historical Sprint 87 blocker remains recorded as: `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`.
- Historical Sprint 86 blocker remains recorded as: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`.
- Sprint 85 approval-pack state remains recorded as: `PUBLIC_VISIBILITY_APPROVAL_PACK_READY`.

## 3. Approval Decision

- explicit owner approval was required before public visibility change, RC tag creation, or selected partner rollout
- owner approves public visibility: `yes`
- owner approves selected partner testing: `yes`
- owner approves RC tag creation: `deferred` / not separately confirmed
- owner approves partner runtime/token issuance: `yes`

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
- external installed-package delivery path is live-proven without private source checkout
- post-switch smoke from a private external consumer passed after the public action source became visible

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
- installed-package rollout is preferred and remains proven
- selected partner pilot kickoff pack is aligned with the public action surface

## 8. Public Switch Procedure

Pre-switch checks completed in Sprint 91:

1. owner approval was explicit and recorded
2. the repository was private before the switch
3. no secret, token-like, or private-path residue remained in tracked files
4. partner runtime/token issuance process was ready for first testers
5. selected partner docs pointed to the correct runtime distribution mode
6. installed-package delivery remained scoped and source-checkout-free

Switch step executed in Sprint 91:

- GitHub visibility was changed only for `alexworkingai/RepoBrain-Action`
- RepoBrain itself did not perform the visibility switch automatically

Immediate post-switch checks completed:

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

- `APPROVED_FOR_PUBLIC_PARTNER_TESTING`
- technical runtime gate is closed
- owner approval was recorded and executed
- post-switch smoke passed
- Marketplace remains deferred

Other allowed outcomes retained for traceability:

- `APPROVED_FOR_PUBLIC_PARTNER_TESTING`
- `APPROVAL_PENDING`
- `BLOCKED_BY_SECURITY`
- `BLOCKED_BY_DOCS`
- `BLOCKED_BY_RUNTIME`
- `BLOCKED_BY_LEGAL`
- `BLOCKED_BY_VALIDATION`
