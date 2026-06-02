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
- `pull-requests: write` is acceptable only for publishing RepoBrain PR command response comments
- keep that permission documented and monitored
- protected main baseline is enabled on the public RepoBrain repository, but required checks remain deferred for now
- do not introduce `pull_request_target`
- do not introduce `contents: write` for normal partner setup
- do not introduce `checks: write` unless a future check-publication feature is explicitly enabled and documented
- do not introduce broad write permissions without explicit review

## BYO-LLM Cost Model

- partners use their own model/provider access
- partner cost ownership remains explicit

## Incident Reporting

- report suspected credential leakage immediately
- revoke affected credentials
- pause testing until scope is reviewed
