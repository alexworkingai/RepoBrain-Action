# RepoBrain Commands

## Product Command Matrix

Current external GitHub command surface is intentionally bounded.

| Command | Issue scope | PR scope | Mutation behavior | Backend expectation | Notes |
|---|---|---|---|---|---|
| `/repobrain help` | supported | supported | none | not applicable | lists supported commands |
| `/repobrain ask <query>` | supported | supported | none | resolved backend: `v6` | primary repo/PR question flow |
| `/repobrain audit` | supported | supported as repository audit with PR context | none | static baseline plus contract-validated private `v6` enrichment when available; backend diagnostics stay explicit | full repository-level 100-point audit with evidence and roadmap |
| `/repobrain score` | supported | supported as compact repository score with PR context | none | same guarded audit engine as `/repobrain audit`; backend diagnostics stay explicit | compact summary view of the same audit engine |
| `/repobrain doctor` | supported | supported | none | report-only diagnostics; backend remains explicit | installation/runtime diagnostic command |
| `/repobrain locate <query>` | supported | supported when parser routes it | none | resolved backend: `v6` when invoked | returns likely files and evidence |
| `/repobrain explain <query>` | supported | supported when parser routes it | none | resolved backend: `v6` when invoked | explains setup or changed context |
| `/repobrain review` | scoped unsupported or safe guidance | supported | none | issue: not applicable; PR: `v6` | review is informational only and not approval |
| `/repobrain status` | supported | supported | none | report-only status snapshot; backend remains explicit | runtime/product policy snapshot |
| `/repobrain verify` | scoped unsupported or issue-safe guidance | supported | none | usually report-only / informational | verify is informational only |
| `/repobrain fix` | scoped unsupported or safe no-patch guidance | supported | no patch, no mutation | issue: not applicable; PR: `v6` | proposal/governance only; does not apply patches |
| `/repobrain fix-lite` | unsupported | unsupported | none | not applicable | internal terminology, use `/repobrain fix` |

## Scope Rules

### Issue Scope

Supported in issues:

- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain audit`
- `/repobrain score`
- `/repobrain doctor`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain status`

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
- `/repobrain score`
- `/repobrain doctor`
- `/repobrain review`
- `/repobrain status`
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
Sprint 81 adds a safe `topocore.audit_score.v1` contract boundary.
Sprint 82 adds a real private `run_audit_score_v1` provider behind that boundary.
Sprint 83 hardens v6-enriched UX so safe repo-relative evidence paths remain visible while private/local/token-like paths stay redacted.

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
It is the current informational 100-point repository scoring MVP.
Sprint 80 benchmark work validated that the scorer ranks sparse, risky, and mature repository shapes in a credible deterministic order.

## Score Policy

`/repobrain score` is a compact summary view of the same guarded audit engine.
It is not a separate scoring system.

It reuses:

- the same static baseline
- the same optional contract-validated private `v6` enrichment
- the same contract guard
- the same static fallback behavior
- the same no-mutation safety constraints

It provides:

- final score and readiness band
- static baseline and live mode truth
- all 10 categories in compact form
- top blockers and top improvements
- a pointer to `/repobrain audit` for the full evidence report

## Doctor Policy

`/repobrain doctor` is a report-only installation and runtime diagnostic.

It reports:

- workflow/action context
- permission baseline signals
- TopoCore v6 setup hints without exposing secret values
- v6-only/no-v5 policy
- score support and audit capability truth
- fork/private-boundary policy
- recommended fixes

`/repobrain doctor` does not rerun private checkout, does not dump the environment, and does not mutate the repository.

## Status Policy

`/repobrain status` is a lightweight runtime and product-policy snapshot.

It reports:

- RepoBrain version
- supported commands
- v6-only backend policy
- audit static baseline truth with optional contract-validated private `v6` enrichment
- score as a compact summary of the same guarded audit engine
- no-patch/no-mutation policy
- install hints for `/repobrain doctor`, `/repobrain score`, and `/repobrain audit`

`/repobrain status` is informational only and does not require expensive TopoCore import or repository mutation.

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

## Unsupported Command Spellings

- `/repobrain fix-lite`: `fix-lite is not a product command. Use /repobrain fix.`
