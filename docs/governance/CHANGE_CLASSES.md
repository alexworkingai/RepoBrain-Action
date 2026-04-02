# Change Classes and Governance Requirements

This matrix defines change classes, risk level, required review, and required validation.

| Change Class | Typical Risk | Review/Approval | Minimum Validation | Live Validation Required |
|---|---|---|---|---|
| Docs-only wording/clarity | Low | 1 maintainer review | Full local gate + docs consistency read | No (unless live behavior claims are changed) |
| Operator-surface docs/process change | Low-Medium | 1 maintainer + operator reviewer | Full local gate + operator walkthrough check | Yes, if procedure claims specific live behavior |
| MCP-surface contract/docs change (ask-only scope) | Medium | 1 maintainer + runtime reviewer | Full local gate + targeted MCP contract checks | Yes |
| Runtime behavior change (ask/review/fix semantics) | High | 2 maintainers (runtime + product) | Full local gate + regression evidence | Yes |
| Protected-kernel-adjacent outward text change | High | 1 maintainer + protected-kernel reviewer | Full local gate + disclosure review | Yes (human disclosure review) |
| Readiness/onboarding classification change | Medium-High | 1 maintainer + operator reviewer | Full local gate + readiness-path tests | Yes |
| Benchmark/artifact semantics change | High | 2 maintainers (runtime + quality) | Full local gate + benchmark regression tests | Yes |
| Unsupported-to-supported capability expansion | High | 2 maintainers + product approval | Full local gate + contract tests + risk review | Yes |

## Class Selection Rule

If a change spans multiple classes, use the highest-risk class requirements.

## Approval Boundary

No contributor self-accepts a high-risk class change without required reviewers and live evidence.

## Scope Discipline

If requested work crosses class boundaries not approved in sprint scope, stop and escalate via product issue.
