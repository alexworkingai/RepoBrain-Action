# RepoBrain Release Notes - RC1

## Summary

This release-candidate draft reflects the current external RepoBrain product path after the v6-only closeout, external pilot hardening, public scrub, and release-readiness gate work.

## Highlights

- v6-only runtime policy
- direct external repository support through `RepoBrain-Action`
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
- audit benchmark report added to show credible ranking across sparse, risky, and mature repository shapes
- doctor implemented as a report-only installation/runtime diagnostic
- status implemented as a report-only runtime snapshot
- verify productionized as informational verification reporting
- fix productized as safe proposal/governance with explicit no-mutation markers
- security, permissions, token degradation, fork-safety, and TopoCore security hardening
- canonical onboarding, command, and troubleshooting docs
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

- consumer repository workflow calls `alexworkingai/RepoBrain-Action@main` in the current controlled pilot
- private TopoCore v6 is checked out separately
- `TOPOCORE_V6_REPO_TOKEN` is required
- current external workflow baseline is read-mostly
- users bring and pay for their own LLM or provider usage

Sprint 84 public-ready gate update:

- selected partner testing should prefer installed private package mode
- `private_checkout` remains beta-only
- plain Python package artifacts can still contain readable implementation files and are documented honestly
- live Elen-MCP smoke after Sprint 84 still passed with:
  - audit: `v6-enriched scoring`
  - score: compact `v6-enriched scoring`
  - doctor: `PASS`
  - status: `success`
  - explicit runtime mode truth for controlled `private_checkout`

Sprint 85 approval-pack update:

- public visibility approval checklist is prepared
- selected partner setup pack is prepared
- RC tag and pinning plan is prepared
- final pre-public live smoke passed on Elen-MCP for doctor, status, audit, score, and ask
- audit and score remained real `v6`-enriched scoring with truthful backend evidence
- public visibility remains approval-gated and is not executed in Sprint 85

Sprint 86 enterprise P0 hardening update:

- SECURITY / CONTRIBUTING / CODEOWNERS baseline added
- dependency review, CodeQL, SBOM, and provenance-prep workflows prepared
- governance verification model documented with `403 => UNKNOWN`, not false PASS
- dormant production mutation helpers were removed from `repobrain/github_flow.py`
- main RepoBrain execution workflow no longer requests `checks: write` or `pull-requests: write`
- installed-package live proof remains tracked as a hard gate until it is passed or blocked with exact evidence

## Current Limitations

- TopoCore v6 remains private permanently
- RepoBrain-Action remains private in the current pilot stage
- `/repobrain audit` is implemented as an MVP repository-level audit
- benchmark evidence now supports the current audit MVP demo narrative
- `/repobrain score` is now implemented as a compact summary of the same guarded audit engine
- `/repobrain fix-lite` is unsupported as a user-facing command spelling
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- this RC does not enable Marketplace or public release

## Distribution Note

This RC draft supports private beta decision-making.
It does not itself publish RepoBrain-Action publicly or to GitHub Marketplace.
TopoCore v6 source rights are not granted through this RC.

- score now ships as a compact summary of the same guarded audit engine
- v6-enriched audit UX now keeps safe repo-relative evidence visible while preserving private-path redaction
