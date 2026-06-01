# RepoBrain Release Notes - RC1

## Summary

This release-candidate draft reflects the current external RepoBrain product path after the v6-only closeout, external pilot hardening, decisive installed-package proof, and the Sprint 91 public visibility switch.

## Highlights

- v6-only runtime policy
- public RepoBrain action surface through `alexworkingai/RepoBrain-Action`
- supported external command matrix:
  - help
  - ask
  - audit
  - score
  - locate
  - explain
  - review
  - verify
  - fix
- audit MVP implemented with 100-point repository quality/readiness scoring
- doctor implemented as a report-only installation/runtime diagnostic
- status implemented as a report-only runtime snapshot
- fix productized as safe proposal/governance with explicit no-mutation markers
- security, permissions, token degradation, fork-safety, and TopoCore security hardening
- canonical onboarding, command, troubleshooting, and partner-pilot docs
- source-available BYO-LLM license for RepoBrain-Action

## Product Positioning

RepoBrain is positioned as a GitHub-native Repository Intelligence and Quality Scoring Platform.
PR review is one surface, not the whole product.
The strategic differentiator is full repository intelligence, quality scoring, evidence-grounded recommendations, and safe governance workflow.

## Safety And Governance

- no patch/autofix
- no file modification by RepoBrain behavior
- no RepoBrain-created branch, commit, or PR behavior
- no safe-to-merge claim
- no security approval claim

## External Install Shape

- consumer repository workflow can now call `alexworkingai/RepoBrain-Action@main` from the public repo
- preferred partner runtime path is `installed_private_package`
- `private_checkout` remains beta-only fallback for controlled environments
- current external workflow baseline is read-mostly
- users bring and pay for their own LLM or provider usage
- TopoCore remains private and is not distributed as source

Sprint 84 public-ready gate update:

- selected partner testing should prefer installed private package mode
- `private_checkout` remains beta-only
- plain Python package artifacts can still contain readable implementation files and are documented honestly

Sprint 86-90 hardening update:

- SECURITY / CONTRIBUTING / CODEOWNERS baseline added
- dependency review, CodeQL, SBOM, and provenance-prep workflows prepared
- governance verification model documented with `403 => UNKNOWN`, not false PASS
- dormant production mutation helpers were removed from `repobrain/github_flow.py`
- main RepoBrain execution workflow no longer requests `checks: write` or `pull-requests: write`
- Sprint 90 closed the decisive installed-package runtime proof gate with real external `v6` evidence

Sprint 91 public-switch update:

- owner-approved public visibility switch executed for RepoBrain-Action
- RepoBrain-Action is now public
- TopoCore remains private
- Elen-MCP remains private
- post-switch smoke passed on Elen-MCP for doctor, status, audit, score, and ask
- audit and score remained real `v6-enriched scoring` with truthful backend evidence
- selected partner pilot kickoff pack is now aligned with the public action surface
- RC tag creation remains deferred

## Current Limitations

- TopoCore v6 remains private permanently
- `/repobrain audit` is implemented as an MVP repository-level audit
- `/repobrain score` is implemented as a compact summary of the same guarded audit engine
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- this RC does not enable Marketplace or a public TopoCore runtime distribution

## Distribution Note

This RC draft supports selected partner testing through the public RepoBrain action surface and a private runtime boundary.
It does not publish to GitHub Marketplace.
TopoCore v6 source rights are not granted through this RC.
