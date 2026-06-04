# Partner Security Notes

## TopoCore Boundary

- no TopoCore source rights are granted
- no TopoCore source license is granted

## Mutation Policy

- no patch/autofix
- no branch/commit/PR creation by RepoBrain
- no branch creation by RepoBrain
- no commit creation by RepoBrain
- no PR creation by RepoBrain

## Approval Limits

- no safe-to-merge approval
- no security approval

## Secret Handling

- do not share owner credentials
- do not share broad PATs
- do not place token values in issues, docs, or logs

## Fork and Private Repository Restrictions

- keep private/runtime credentials away from untrusted fork code
- preserve read-mostly workflow permissions

## Workflow Permissions

- use read-mostly baseline permissions
- `RB_REPOBRAIN_ENABLE_ISSUE_LLM=1` enables controlled issue ask/explain and issue audit narrative LLM by default; `RB_REPOBRAIN_ENABLE_ISSUE_LLM=0` disables that path without weakening deterministic fallback
- `/repobrain audit --profile premium` stays explanation-only and implies a premium narrative layer without overriding the TopoCore score contract
- LLM narrative layers must not override canonical PR classifier facts in PR audit modes
- `pull-requests: write` is acceptable only for publishing RepoBrain PR command response comments
- keep that permission documented and monitored
- protected main baseline is enabled on the public RepoBrain repository
- current public-ruleset model is solo-owner rather than review-enforced
- force pushes, deletions, and non-linear history remain blocked
- required checks remain deferred for now
- CODEOWNERS review enforcement remains deferred for now
- do not introduce `pull_request_target`
- do not introduce `contents: write` for normal partner setup
- do not introduce `checks: write` unless a future check-publication feature is explicitly enabled and documented
- do not introduce broad write permissions without explicit review
- LLM narrative layers must not change TopoCore scores, category scores, blockers, or evidence truth

## BYO-LLM Cost Model

- partners use their own model/provider access
- partner cost ownership remains explicit

## Incident Reporting

- report suspected credential leakage immediately
- revoke affected credentials
- pause testing until scope is reviewed
