# Final Command Surface Matrix

| Command | Issue scope | PR scope | Backend behavior | Mutation behavior | Partner-testing status | Notes |
|---|---|---|---|---|---|---|
| `/repobrain help` | supported | supported | not applicable | none | ready | lists supported commands |
| `/repobrain ask` | supported | supported | `v6` when runtime is available | none | ready | bounded repository Q&A; route label stays `ASK`; balanced/premium may use controlled issue or PR LLM |
| `/repobrain locate` | supported | supported when routed | `v6` when runtime is available | none | ready | file/evidence locator |
| `/repobrain explain` | supported | supported when routed | `v6` when runtime is available | none | ready | explanation flow; balanced/premium may use controlled issue or PR LLM |
| `/repobrain review` | scoped unsupported or safe guidance | supported | issue: not applicable; PR: `v6` when runtime is available | none | ready with PR context | informational only |
| `/repobrain verify` | scoped unsupported or issue-safe guidance | supported | informational/report-only | none | ready with PR context | not merge approval |
| `/repobrain fix` | scoped unsupported or safe no-patch guidance | supported | issue: not applicable; PR: `v6` when runtime is available | no patch, no mutation | ready with PR context | proposal/governance only |
| `/repobrain audit` | supported | supported with PR context | full guarded audit engine; `v6`-enriched when runtime is available | none | ready | full repository audit; `--narrative` / `--executive` / `--profile premium` add optional LLM explanation only |
| `/repobrain score` | supported | supported with PR context | same guarded audit engine; `v6`-enriched when runtime is available | none | ready | compact summary of audit |
| `/repobrain doctor` | supported | supported | report-only diagnostics | none | ready | install/runtime diagnostic |
| `/repobrain status` | supported | supported | report-only runtime snapshot | none | ready | command/runtime status |

## Notes

- audit = full `v6`-enriched repository audit when runtime is available
- audit narrative flags do not change TopoCore score authority
- score = compact summary of the same guarded audit engine
- score = no LLM required in the current product surface
- fix = proposal/governance only
- verify = informational only
- doctor and status = report-only diagnostics
- default GitHub comments use compact diagnostics
- `RB_REPOBRAIN_VERBOSE_DIAGNOSTICS=1` enables expanded sanitized diagnostics
- full trace stays in artifacts/logs rather than default partner-facing comments
- visible route labels always reflect the typed command; internal reasoning mode is separate
- no patch/autofix
- no RepoBrain-created branch, commit, or PR
