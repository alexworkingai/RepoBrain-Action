# Readiness Matrix

| Surface | Readiness Level | What Is Stable | What Is Bounded | Evaluator Expectation |
|---|---|---|---|---|
| GitHub mode | Startup-evaluable (primary) | ask/review/fix flow, readiness contract, artifact truth | depends on setup quality and scope discipline | evaluate as primary product surface |
| External GitHub mode foundation | Startup-evaluable (bounded) | third-party GitHub-native doctor/help/ask plus bounded Review Candidate and Fix-Lite Candidate behavior | no patch application, file modification, commit creation, branch push, PR creation, security verdicts, safe-to-merge, approval/rejection, or autofix | evaluate as first installable third-party GitHub foundation and public community release candidate |
| External CLI mode | Startup-evaluable (bounded) | ask path on third-party checkout | review/fix unsupported | use for bounded external ask validation |
| MCP surface | Startup-evaluable (bounded) | ask request/response contract | non-ask capabilities unsupported | use for integration-style ask evaluation only |
| Marketplace-style distribution | Not ready | none | launch/admin/billing not provided | do not evaluate as launched distribution |

## Non-Claims

1. No full external GitHub-native review parity claim.
2. No patch application, file modification, commit creation, branch push, or PR creation claim in external GitHub foundation mode.
3. No MCP breadth claim beyond ask.
4. No GA/Marketplace claim.
5. No security verdict, safe-to-merge, approval/rejection, or autonomous repair claim.
