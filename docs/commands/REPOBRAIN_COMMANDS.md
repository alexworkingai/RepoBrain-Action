# RepoBrain Commands

## Product Command Matrix

Current external GitHub command surface is intentionally bounded.

| Command | Issue scope | PR scope | Mutation behavior | Backend expectation | Notes |
|---|---|---|---|---|---|
| `/repobrain help` | supported | supported | none | not applicable | lists supported commands |
| `/repobrain ask <query>` | supported | supported | none | resolved backend: `v6` when available; compact runtime/LLM block by default | issue ask analyzes the target repository; PR ask stays PR-scoped; route label stays `ASK` |
| `/repobrain audit` | supported | supported as repository audit with PR context | none | static baseline plus contract-validated private `v6` enrichment when available; default comments stay compact | full repository-level 100-point audit with evidence and roadmap |
| `/repobrain score` | supported | supported as compact repository score with PR context | none | same guarded audit engine as `/repobrain audit`; default comments stay compact | compact summary view of the same audit engine |
| `/repobrain doctor` | supported | supported | none | report-only diagnostics; backend remains explicit | installation/runtime diagnostic command |
| `/repobrain locate <query>` | supported | supported when parser routes it | none | resolved backend: `v6` when invoked | returns likely files and evidence |
| `/repobrain explain <query>` | supported | supported when parser routes it | none | resolved backend: `v6` when invoked | explains setup or changed context |
| `/repobrain review` | scoped unsupported or safe guidance | supported | none | issue: not applicable; PR: `v6` | review is informational only and not approval |
| `/repobrain status` | supported | supported | none | report-only status snapshot; backend remains explicit | runtime/product policy snapshot |
| `/repobrain verify` | scoped unsupported or issue-safe guidance | supported | none | usually report-only / informational | verify is informational only |
| `/repobrain fix` | scoped unsupported or safe no-patch guidance | supported | no patch, no mutation | issue: not applicable; PR: `v6` | proposal/governance only; does not apply patches |

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

Issue ask behavior:

- product-analysis asks should describe the current consumer repository rather than RepoBrain-Action internals
- operational asks should answer workflow/runtime/readiness questions directly
- deterministic fallback remains valid when safe LLM policy blocks an LLM call

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

PR ask behavior:

- PR ask should stay scoped to the PR
- it should summarize change impact, touched areas, validation needs, and risk level rather than a generic repository overview

## Verify Policy

`/repobrain verify` is informational only.
It is a checks/statuses report only.

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

Default verify output stays compact:

- no legacy TopoCore diagnostics header
- no mojibake diagnostics title
- runtime/safety summary stays compact by default

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
- compact runtime/safety diagnostics by default
- expanded sanitized diagnostics only in verbose/artifact mode

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
- runtime mode truth (`installed_package`, `private_checkout`, `local_path`, or `disabled`) without printing private paths
- v6-only/no-v5 policy
- score support and audit capability truth
- fork/private-boundary policy
- recommended fixes

When workflow permissions are otherwise safe and `pull-requests: write` is present only for RepoBrain PR command response comments, doctor may report `PASS_WITH_NOTES` instead of `WARN`.

`/repobrain doctor` does not rerun private checkout, does not dump the environment, and does not mutate the repository.

## Status Policy

`/repobrain status` is a lightweight runtime and product-policy snapshot.

It reports:

- RepoBrain version
- supported commands
- v6-only backend policy
- runtime mode truth without exposing private paths
- audit static baseline truth with optional contract-validated private `v6` enrichment
- score as a compact summary of the same guarded audit engine
- no-patch/no-mutation policy
- install hints for `/repobrain doctor`, `/repobrain score`, and `/repobrain audit`
- partner-friendly runtime wording by default
- installed private package as the preferred partner path
- raw runtime mode fields only in verbose/artifact diagnostics

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

- no patch/autofix
- no file changes
- no RepoBrain-created branch/commit/PR

`/repobrain fix` does not apply patches and does not mutate the repository.

## Unsupported Commands

- Unsupported RepoBrain commands return a generic help-oriented response.

## LLM Execution Notes

- ask and explain do not require an LLM call to produce a bounded answer
- issue ask may use an LLM only when safe policy allows
- when policy or provider availability blocks the LLM path, RepoBrain can still answer from deterministic retrieval, workflow/runtime inspection, evidence extraction, and TopoCore v6 signals
- route labels always reflect the user command; internal analysis mode is separate from the visible route
- diagnostics must state whether the LLM was actually called
- default GitHub comments keep compact LLM/runtime/safety blocks
- raw TKY/TKYA internals belong to verbose diagnostics or artifacts, not default partner-facing comments
