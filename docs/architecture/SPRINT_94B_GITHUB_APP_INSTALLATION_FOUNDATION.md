# Sprint 94B GitHub App Installation Foundation

## Purpose

Sprint 94B establishes GitHub App installation identity for the GitHub-native beta control plane.

This sprint is:
- not GitHub Marketplace
- not billing
- not external hosted API deployment
- not the private TopoCore worker yet

## Target Model

Target flow:
- trusted partner installs the RepoBrain GitHub App
- the selected repository becomes visible to the RepoBrain control plane
- a private control repo workflow can mint an installation token
- a future request-queue worker can process requests
- TopoCore stays private
- results return to GitHub as public-safe Issue or PR responses

## Why GitHub App Is Needed

GitHub App is the correct identity layer for this stage because:
- GitHub App gives installation identity
- GitHub App enables scoped repository permissions
- GitHub App avoids owner-generated partner tokens
- GitHub App avoids manual per-repo metadata registration
- GitHub App allows future scale beyond internal and `private_checkout` mode
- GitHub App can be used without Marketplace at this stage

## No External Infrastructure In 94B

Sprint 94B does not require:
- custom domain
- paid or free-tier hosting
- no paid or free-tier hosting dependency
- webhook receiver
- external backend
- hosted API endpoint
- no hosted API endpoint dependency
- tunnel
- no tunnel dependency
- Marketplace listing

Webhook note:
- webhooks are disabled or deferred in 94B
- future production may use webhooks
- beta foundation currently assumes GitHub-native control workflow and later polling or queue logic

## GitHub App Manual Setup Checklist

Operator checklist:
- create the GitHub App under the owner or org account
- use a name such as `RepoBrain Beta` or `RepoBrain`
- use the existing GitHub repository URL or project page URL as homepage; no custom domain required
- disable webhooks for this beta-foundation stage
- set repository access to `Only select repositories`
- use these permissions:
  - Metadata: read
  - Contents: read
  - Issues: read and write
  - Pull requests: read and write
  - Actions: read only if later artifact or workflow discovery needs it
  - Checks: read or write only if later checks integration truly needs it
- generate the private key
- store the private key only in the private RepoBrain control repo secrets
- never store the private key in partner repos
- never store the private key in the public `RepoBrain-Action` repo
- record the App ID as a private control repo variable or secret
- let future control workflows discover installation IDs automatically where possible

## Private Control Repo Secret Model

Required private control repo configuration names:
- `REPOBRAIN_GITHUB_APP_ID`
- `REPOBRAIN_GITHUB_APP_PRIVATE_KEY`

Optional later names:
- `REPOBRAIN_GITHUB_APP_CLIENT_ID`
- `REPOBRAIN_GITHUB_APP_SLUG`

These names must not exist in:
- partner repos
- public `RepoBrain-Action`

## Partner Repo Model

Partner repos should only need to:
- install the RepoBrain GitHub App when invited
- add the public `RepoBrain-Action` workflow later
- run `/repobrain score`, `/repobrain audit`, or `/repobrain audit --profile premium`

Partner repos must not need:
- RepoBrain owner token
- TopoCore token
- TopoCore checkout
- GitHub App private key
- hosted API URL
- billing
- Marketplace install

## 94B Deliverables Vs Later Sprints

Sprint 94B provides:
- setup docs
- installation identity contracts
- control repo auth workflow template
- tests

Later sprints:
- 94C: request marker and GitHub-native queue
- 94D: private control worker plus TopoCore execution
- 94E: trusted partner beta validation

## TopoCore Boundary

RepoBrain uses TopoCore as a private entrypoint and capability provider.

Boundary rules:
- TopoCore is a separate team and system
- RepoBrain does not implement TopoCore internals
- RepoBrain does not develop TopoCore internals
- RepoBrain does not modify TopoCore internals
- future TopoCore improvements arrive through versioned contracts and capabilities
- commands remain stable for now:
  - `/repobrain score`
  - `/repobrain audit`
  - `/repobrain audit --profile premium`

## Reserved Action Inputs Decision

Sprint 94B intentionally does not add a new live action input such as `transport_mode`.

Reason:
- adding a queue-oriented input in 94B would imply a supported transport path before 94C exists
- current stable and internal behavior should remain unchanged
- `hosted_api` already remains available as experimental and future external-runtime mode
- queue transport reservation can be added when the first non-placeholder behavior exists

Historical follow-through note:
- Sprint 94C later adds `transport_mode: github_app_queue` once the public queue marker exists
- 94B should still be read as the installation foundation, not as the live queue layer

## Status

Expected status after Sprint 94B:
- `SPRINT_94B_GITHUB_APP_INSTALLATION_FOUNDATION_READY`

Not allowed:
- `TRUSTED_PARTNER_BETA_READY`
- `PUBLIC_DEVELOPER_BETA_READY`
- `MARKETPLACE_READY`
- `PRODUCTION_APPROVED`
- `SECURITY_CERTIFIED`
