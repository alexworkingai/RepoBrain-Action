# RepoBrain Release Notes - RC1

## Summary

This release-candidate draft reflects the current external RepoBrain product path after the v6-only closeout and external pilot hardening work.

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
- security, permissions, token degradation, and fork-safety hardening
- canonical onboarding, command, and troubleshooting docs

## Safety And Governance

- no patch/autofix
- no file modification by RepoBrain behavior
- no RepoBrain-created branch/commit/PR behavior
- no safe-to-merge claim
- no security approval claim

## External Install Shape

- consumer repository workflow calls `alexworkingai/RepoBrain-Action@main`
- private TopoCore v6 is checked out separately
- `TOPOCORE_V6_REPO_TOKEN` is required
- current external workflow baseline is read-mostly

## Current Limitations

- TopoCore v6 remains private permanently
- RepoBrain-Action remains private in the current pilot stage
- `/repobrain status` is unsupported
- `/repobrain doctor` is unsupported
- `/repobrain fix-lite` is unsupported as a user-facing command spelling
- issue-scope `review`, `verify`, and `fix` remain scoped unsupported or safe guidance
- this RC does not enable Marketplace/public release

## Distribution Note

This RC draft supports private beta decision-making.
It does not itself publish RepoBrain-Action publicly or to GitHub Marketplace.
