# RepoBrain Commands

## Product Command Matrix

Current external GitHub command surface is intentionally bounded.

| Command | Issue scope | PR scope | Mutation behavior | Backend expectation | Notes |
|---|---|---|---|---|---|
| `/repobrain help` | supported | supported | none | not applicable | lists supported commands |
| `/repobrain ask <query>` | supported | supported | none | resolved backend: `v6` | primary repo/PR question flow |
| `/repobrain audit` | supported | supported as repository audit with PR context | none | repository-static MVP; backend diagnostics stay explicit | 100-point repository quality/readiness scoring |
| `/repobrain locate <query>` | supported | supported when parser routes it | none | resolved backend: `v6` when invoked | returns likely files and evidence |
| `/repobrain explain <query>` | supported | supported when parser routes it | none | resolved backend: `v6` when invoked | explains setup or changed context |
| `/repobrain review` | scoped unsupported or safe guidance | supported | none | issue: not applicable; PR: `v6` | review is not approval |
| `/repobrain verify` | scoped unsupported or issue-safe guidance | supported | none | usually report-only / informational | verify is informational only |
| `/repobrain fix` | scoped unsupported or safe no-patch guidance | supported | no patch, no mutation | issue: not applicable; PR: `v6` | proposal/governance only |
| `/repobrain status` | unsupported | unsupported | none | not applicable | roadmap command spelling, not implemented |
| `/repobrain doctor` | unsupported | unsupported | none | not applicable | roadmap command spelling, not implemented |
| `/repobrain fix-lite` | unsupported | unsupported | none | not applicable | internal terminology, use `/repobrain fix` |

## Scope Rules

### Issue Scope

Supported in issues:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain audit`
- `/repobrain locate <query>`
- `/repobrain explain <query>`

Conservative in issues:

- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`

These commands do not pretend issue context is equivalent to PR context.

### PR Scope

Supported in PRs:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain audit`
- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`

Also supported when parser routes them:

- `/repobrain locate <query>`
- `/repobrain explain <query>`

## Verify Policy

`/repobrain verify` is informational only.

It can report:

- `PASS`
- `WARN`
- `FAIL`
- `PENDING`
- `NOT_RUN`
- `UNKNOWN`

It does not mean:

- safe to merge
- merge approval
- security approval

## Audit Policy

`/repobrain audit` is a repository-level, no-mutation audit MVP.

It provides:

- a 0-100 overall repository quality/readiness score
- all 10 scoring categories with bounded weights totaling 100
- critical blockers
- top improvements
- a 30/60/90-day roadmap
- evidence references
- confidence and limitations
- explicit runtime/safety diagnostics

`/repobrain audit` is informational only.
It does not certify merge safety, security approval, or production readiness.

## Fix Policy

`/repobrain fix` is safe proposal/governance only.

Possible fix product statuses:

- `PROPOSAL_READY`
- `NO_ACTION_NEEDED`
- `NEEDS_MORE_INFORMATION`
- `UNSUPPORTED_SCOPE`
- `BLOCKED_BY_SAFETY`
- `ERROR_SANITIZED`

Visible no-mutation expectations:

- `patch_authorized=false`
- `patch_applied=false`
- `files_modified=false`
- `branch_created=false`
- `commit_created=false`
- `pr_created=false`

`/repobrain fix` does not apply patches and does not mutate the repository.

## Roadmap Commands (Not Implemented Yet)

These command names are part of the documented roadmap, not the current supported external command surface:

- `/repobrain score`: planned compact score summary
- `/repobrain doctor`: planned installation/runtime diagnostic command
- `/repobrain status`: planned runtime status snapshot

`/repobrain fix-lite` is not a product command and should redirect users to `/repobrain fix`.
