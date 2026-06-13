# Sprint 94A GitHub-Native Beta Architecture Correction

## Correction Summary

Sprints 93B-93E produced useful foundations for:
- GitHub OIDC identity capture
- hosted request and response contracts
- hosted client routing
- public-safe rendering and redaction
- quota and tenant boundary concepts

Those foundations remain valuable.

Sprint 94A corrects the near-term beta architecture after live validation showed that the `hosted_api` path cannot serve as the default GitHub-native trusted beta path without a real external runtime.

RepoBrain will not use any of the following as the immediate beta route:
- external hosted API as the default path
- domain registration
- paid or free-tier external hosting
- temporary tunnel dependencies
- GitHub Marketplace

## Corrected Near-Term Target

The corrected intermediate target is a GitHub-native beta control plane.

Flow:
- partner repository
- public `RepoBrain-Action`
- GitHub-native request marker or queue item
- private RepoBrain control repository worker
- GitHub App installation token
- private TopoCore entrypoint
- public-safe GitHub Issue or PR comment

## Why This Satisfies The Updated Goal

This direction fits the current beta objective because it avoids the blockers that the hosted path still depends on.

Properties:
- no partner private token
- no owner-generated onboarding token
- no manual metadata registration
- no TopoCore on the partner runner
- no external domain
- no external hosting subscription
- no Marketplace requirement
- suitable for trusted and developer beta
- prepares a later production backend without forcing it now

## Hosted API Reclassification

`hosted_api` remains useful as a future production and backend-compatible transport.

Current Sprint 94A truth:
- `hosted_api` is experimental and future external-runtime mode
- it requires a real external runtime to be meaningful
- trusted beta docs must not tell partners to configure placeholder hosted API URLs
- `REPOBRAIN_HOSTED_API_URL` is not the default beta blocker anymore

## TopoCore Boundary Correction

TopoCore remains a separate team and system.

RepoBrain boundaries:
- RepoBrain does not implement TopoCore internals
- RepoBrain integrates private TopoCore entrypoints through stable contracts and capability responses
- future TopoCore capabilities may improve depth, quality, and coverage without changing user commands
- RepoBrain must support capability negotiation, compatibility handling, and public-safe rendering

Stable user command surface remains:
- `/repobrain score`
- `/repobrain audit`
- `/repobrain audit --profile premium`

## Next Sprint Roadmap

- 94A: architecture correction
- 94B: GitHub App installation foundation without Marketplace
- 94C: GitHub-native request queue
- 94D: private control worker plus TopoCore entrypoint execution
- 94E: trusted partner beta validation
- 94F: public developer beta without Marketplace
- 95A: BYOK and customer-funded LLM adapter foundation
- 95B: tenant policy, usage, and quota foundation
- 95C: TopoCore capability integration layer
- 95D: public showcase package for developer and Microsoft visibility

Follow-through note:
- Sprint 94C now materializes the request marker and queue layer described here
- final score and audit delivery still depends on the Sprint 94D private worker

## Explicit Non-Goals

Sprint 94A does not implement:
- Marketplace listing
- paid billing
- external hosted API deployment
- domain setup
- SaaS hosting
- permanent backend platform
- dashboard
- enterprise plan
- TopoCore internal modifications

## Sprint 94A Status

- `SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION_READY`
