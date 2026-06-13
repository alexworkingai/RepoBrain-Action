# Sprint 94C GitHub-Native Request Queue

## Purpose

Sprint 94C adds the public-side GitHub-native request queue for trusted beta.

## Flow

partner comment
-> public RepoBrain-Action
-> queue marker comment
-> future private control worker
-> future TopoCore execution
-> future final result comment

## What 94C implements

- `transport_mode: github_app_queue`
- deterministic `request_id`
- GitHub-native queue contract
- public-safe queue marker renderer
- queued acknowledgement output
- tests

## What 94C does not implement

- private control worker
- GitHub App installation token minting
- scanning installed repos
- TopoCore execution
- final audit or score response
- dashboard
- Marketplace
- external backend

## Partner beta preview

Partner will:
- install GitHub App when invited
- add workflow
- run `/repobrain score`, `/repobrain audit`, or `/repobrain audit --profile premium`
- receive queued acknowledgement in 94C
- receive final reports only after the Sprint 94D private control worker exists

## Safety

- no TopoCore in partner runner
- no owner token
- no manual registration
- no external hosted API
- no domain
- no Marketplace
- no mutation or autofix

## Status

After 94C:
- `SPRINT_94C_GITHUB_NATIVE_REQUEST_QUEUE_READY`

Not:
- `TRUSTED_PARTNER_BETA_READY`
- `PUBLIC_DEVELOPER_BETA_READY`
- `PHASE_1_TRUSTED_PARTNER_SELF_SERVICE_READY`
- `MARKETPLACE_READY`
