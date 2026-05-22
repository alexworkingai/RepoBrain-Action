# Sprint 77 - Public Scrub, License, TopoCore Security, and Positioning Gate

## 1. Purpose

Sprint 77 resolves public scrub, license, support, TopoCore security, and strategic product positioning gates.
It does not change runtime policy.
It does not publish RepoBrain-Action, switch visibility, create a release tag, or publish to Marketplace.

## 2. Baseline

- latest main before Sprint 77: `f414ac4 Assess release candidate readiness`
- Sprint 76 status:
  - `PRIVATE_BETA_RC_READY`
  - `PUBLIC_BLOCKED_BY_SCRUB`
  - `MARKETPLACE_NOT_READY`

## 3. Owner Decisions Implemented

- Source-Available BYO-LLM License v0.2
- user-paid LLM model
- no LLM resale
- TopoCore v6 source permanently private
- RepoBrain v6 100-point scoring positioning
- `/repobrain audit` roadmap documented without implementation

## 4. Public Scrub Results

- local paths found in tracked historical and release docs
- local paths sanitized to public-safe placeholders
- secret and token scans found pattern guards and test fixtures, not real secret values
- private TopoCore source remains absent from RepoBrain-Action
- no active v5 runtime residue or `repobrain-community` dependency returned to the product path
- no active docs claim patch/autofix, safe-to-merge, or security approval

## 5. License And Service Model

- top-level `LICENSE` added
- license name: `RepoBrain Action Source-Available BYO-LLM License v0.2`
- BYO-LLM and user-paid provider model documented
- commercial, hosted, managed, and resale restrictions documented
- TopoCore v6 source exclusion documented
- service model documented as support, onboarding, scoring, enterprise integration, and private runtime access rather than token resale

## 6. TopoCore v6 Security

- high-security policy added
- token policy documented
- workstation policy documented
- GitHub Actions policy documented
- distribution policy documented
- incident response documented

## 7. Product Positioning And Scoring Model

- RepoBrain positioned as GitHub-native repository intelligence and quality scoring
- 100-point scoring model drafted
- category weights documented
- `/repobrain audit`, `/repobrain score`, `/repobrain doctor`, and `/repobrain status` roadmap documented
- `/repobrain fix-lite` remains unsupported and should redirect users to `/repobrain fix`

## 8. Support, Versioning, And Distribution

- support policy added
- versioning and pinning strategy added
- private TopoCore distribution strategy added
- controlled pilot may keep `@main`, but immutable SHA or future tag pinning is preferred for repeatability

## 9. Updated Public And Marketplace Decision

- public readiness decision: `PUBLIC_BLOCKED_BY_DISTRIBUTION_STRATEGY`
- Marketplace decision: `MARKETPLACE_NOT_READY`
- private beta decision: `PRIVATE_BETA_RC_CONFIRMED`
- security decision: `TOPOCORE_SECURITY_POLICY_ADOPTED`

## 10. Non-Goals

- no v5
- no repobrain-community
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no release tag
- no `/repobrain audit` implementation in this sprint

## 11. Next Step

Recommended next step:

- Sprint 78 - Implement `/repobrain audit` MVP with 100-point scoring

Rationale:

- full repository audit and scoring is the core differentiator
- it is the strongest proof point for Microsoft and GitHub strategic attention
- it can advance product value without forcing premature public distribution decisions
