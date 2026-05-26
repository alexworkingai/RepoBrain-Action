# Final Command Surface Matrix

| Command | Issue scope | PR scope | Backend behavior | Mutation behavior | Partner-testing status | Notes |
|---|---|---|---|---|---|---|
| `/repobrain help` | supported | supported | not applicable | none | ready | lists supported commands |
| `/repobrain ask` | supported | supported | `v6` when runtime is available | none | ready | bounded repository Q&A |
| `/repobrain locate` | supported | supported when routed | `v6` when runtime is available | none | ready | file/evidence locator |
| `/repobrain explain` | supported | supported when routed | `v6` when runtime is available | none | ready | explanation flow |
| `/repobrain review` | scoped unsupported or safe guidance | supported | issue: not applicable; PR: `v6` when runtime is available | none | ready with PR context | informational only |
| `/repobrain verify` | scoped unsupported or issue-safe guidance | supported | informational/report-only | none | ready with PR context | not merge approval |
| `/repobrain fix` | scoped unsupported or safe no-patch guidance | supported | issue: not applicable; PR: `v6` when runtime is available | no patch, no mutation | ready with PR context | proposal/governance only |
| `/repobrain audit` | supported | supported with PR context | full guarded audit engine; `v6`-enriched when runtime is available | none | ready | full repository audit |
| `/repobrain score` | supported | supported with PR context | same guarded audit engine; `v6`-enriched when runtime is available | none | ready | compact summary of audit |
| `/repobrain doctor` | supported | supported | report-only diagnostics | none | ready | install/runtime diagnostic |
| `/repobrain status` | supported | supported | report-only runtime snapshot | none | ready | command/runtime status |
| `/repobrain fix-lite` | unsupported | unsupported | not applicable | none | not a product command | use `/repobrain fix` |

## Notes

- audit = full `v6`-enriched repository audit when runtime is available
- score = compact summary of the same guarded audit engine
- fix = proposal/governance only
- verify = informational only
- doctor and status = report-only diagnostics
- no patch/autofix
- no RepoBrain-created branch, commit, or PR
