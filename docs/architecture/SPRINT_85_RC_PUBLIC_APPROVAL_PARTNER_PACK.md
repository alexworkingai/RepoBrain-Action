# Sprint 85 - RC Public Approval And Partner Pack

## 1. Purpose

Sprint 85 prepares the release-candidate, public approval package, and selected partner testing pack.
It does not make the repository public.

## 2. Baseline

- latest main before Sprint 85: `2cb2f6c Record runtime distribution gate live evidence`
- Sprint 84 status: `PUBLIC_READY_PENDING_OWNER_APPROVAL`

## 3. Approval Checklist

- doc path: `docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md`
- approval decisions: explicit owner approvals remain pending in Sprint 85
- technical, security, legal, and partner gates are compiled into one checklist

## 4. Partner Test Pack

Docs created:

- `docs/partner/PARTNER_TESTING_SETUP.md`
- `docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md`
- `docs/partner/PARTNER_FEEDBACK_TEMPLATE.md`
- `docs/partner/PARTNER_SECURITY_NOTES.md`

Runtime model:

- `installed_private_package` preferred
- `private_checkout` beta-only fallback

Token model:

- per-partner scoped credential
- read-only
- expiration, rotation, and revocation required

Feedback plan:

- partner feedback template included

## 5. RC Tag / Pinning

- plan: `docs/release/RC_TAG_AND_PINNING_PLAN.md`
- tag created: `no`
- approval status: explicit owner approval not present in Sprint 85
- recommended tag: `v0.5.0-rc.1`

## 6. Final Docs Audit

- public and Marketplace truth were rechecked
- selected partner docs now point to the preferred runtime mode explicitly
- no public visibility claim is made
- no Marketplace publication claim is made
- no unsafe approval claim is made

## 7. Public Switch Runbook

- doc path: `docs/release/PUBLIC_VISIBILITY_SWITCH_RUNBOOK.md`
- not executed in Sprint 85
- rollback caveat is explicit: public clones may persist

## 8. Live Pre-Public Smoke

- issue URL: pending live run
- PR URL: not required by default
- run URLs: pending live run
- command results: pending live run
- backend evidence: pending live run
- safety result: pending live run

## 9. Product Status

- `RC_TAG_READY_PENDING_OWNER_APPROVAL`

Possible final Sprint 85 outcomes:

- `PUBLIC_VISIBILITY_APPROVAL_PACK_READY`
- `PUBLIC_VISIBILITY_APPROVED_READY_TO_SWITCH`
- `RC_TAG_READY_PENDING_OWNER_APPROVAL`
- `RC_TAG_CREATED`
- `BLOCKED_ON_APPROVAL_CHECKLIST`
- `BLOCKED_ON_PARTNER_PACK`
- `BLOCKED_ON_LIVE_SMOKE`
- `BLOCKED_ON_VALIDATION`

## 10. Next Step

If the approval pack is ready:

- Sprint 86 - Owner-Approved Public Visibility Switch and Partner Pilot Kickoff

## 11. Non-Goals

- no v5
- no repobrain-community
- no runtime policy change
- no patch/autofix
- no Marketplace
- no public switch in Sprint 85
- no TopoCore source exposure
- no Microsoft partnership claim
