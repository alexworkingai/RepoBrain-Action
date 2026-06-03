# Sprint 92D Final Issue/PR UX Polish

## 1. Purpose

Sprint 92D finishes partner-facing issue and PR UX polish while recording the protected-main governance baseline on the public RepoBrain repository.

## 2. Baseline after Sprint 92C

- RepoBrain-Action is public
- TopoCore remains private
- Elen-MCP remains private
- pre-merge product status: `PARTNER_PILOT_READY_AFTER_DIAGNOSTICS_AND_PERMISSION_CLASSIFICATION`

## 3. Protected-main governance baseline

- public `main` is protected by an active `Protect main` ruleset
- PR before merge: enabled
- required approvals: `1`
- dismiss stale approvals: enabled
- conversation resolution: enabled when available
- force pushes blocked: enabled
- deletions restricted: enabled
- required checks: deferred
- CODEOWNERS enforcement: deferred
- governance label: `PROTECTED_MAIN_BASELINE_ENABLED`
- interpretation: `GOVERNANCE_PARTIAL_REQUIRED_CHECKS_DEFERRED`

## 4. Final manual smoke findings

- pending post-merge live retest on Elen-MCP
- Sprint 92C remains the last merged live baseline while Sprint 92D awaits PR approval

## 5. Help output cleanup

- authoritative supported-commands block
- examples separated from command notes
- profiles and safety notes separated clearly

## 6. Issue ask synthesis policy and fallback

- issue ask may use LLM only when safe policy allows
- otherwise deterministic product-analysis or operational fallback is used
- no review-style placeholder envelope should replace a useful answer

## 7. Route/scope canonicalization

- visible route reflects the typed command
- internal analysis mode remains separate from the user-facing route
- PR ask renders as `PR ask`

## 8. Verify output cleanup

- verify remains checks/statuses report only
- no legacy TopoCore diagnostics header
- no mojibake diagnostics title

## 9. Review/fix compact output

- default review/fix comments stay compact
- deeper internals move to verbose/artifact diagnostics
- fix remains no-mutation proposal/governance only

## 10. Doctor PASS_WITH_NOTES semantics

- justified PR comment response permission should not surface as a generic partner-facing warning
- doctor now uses `PASS_WITH_NOTES` when that permission is constrained and monitored

## 11. Locate/explain rerank

- RepoBrain workflow queries should prefer `.github/workflows/repobrain.yml`
- unrelated deployment workflows should not outrank the actual RepoBrain workflow unless the query asks deployment

## 12. Status partner-friendly runtime wording

- default status wording is partner-friendly
- installed private package remains the preferred partner path
- raw runtime internals stay in verbose/artifact diagnostics

## 13. Governance script/ruleset verification

- governance script now understands rulesets
- `403` and missing visibility stay `UNKNOWN`, never `PASS`
- required checks deferred does not fail Sprint 92D by itself

## 14. Tests

- focused UX, governance, verify, doctor, rerank, and status tests were added for Sprint 92D

## 15. Live retest

- not yet executed on this branch
- protected main requires PR review/approval before merge

## 16. Product status

- current branch status: `SPRINT_92D_READY_PENDING_PROTECTED_MAIN_PR_APPROVAL`
- target merged status: `SELECTED_PARTNER_PILOT_READY_AFTER_FINAL_ISSUE_PR_UX_POLISH_AND_PROTECTED_MAIN`

## 17. Non-goals

- no Marketplace work
- no runtime architecture change
- no TopoCore source exposure
- no patch/autofix enablement
- no weakening of protected main
