# RepoBrain Release Notes - RC1

## Summary

This release-candidate draft reflects the current external RepoBrain product path after the v6-only closeout, external pilot hardening, public scrub, and release-readiness gate work.

## Highlights

- v6-only runtime policy
- direct external repository support through `RepoBrain-Action`
- supported external command matrix:
  - help
  - ask
  - locate
  - explain
  - review
  - verify
  - fix
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

## Current Limitations

- TopoCore v6 remains private permanently
- RepoBrain-Action remains private in the current pilot stage
- `/repobrain audit` and `/repobrain score` are roadmap commands, not implemented in RC1
- `/repobrain status` is unsupported today
- `/repobrain doctor` is unsupported today
- `/repobrain fix-lite` is unsupported as a user-facing command spelling
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- this RC does not enable Marketplace or public release

## Distribution Note

This RC draft supports private beta decision-making.
It does not itself publish RepoBrain-Action publicly or to GitHub Marketplace.
TopoCore v6 source rights are not granted through this RC.
