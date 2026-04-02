# Release Discipline

## Merge Preconditions

Before merge, all of the following must be true:

1. Branch discipline followed (explicit sprint branch from current head).
2. Full local validation gate passed.
3. Change class and required reviewers satisfied.
4. Scope remains inside approved sprint boundaries.
5. Docs claims match implemented behavior.

## Acceptance Preconditions

Before calling a sprint accepted:

1. Relevant live validation completed.
2. Supported/unsupported behavior boundaries confirmed.
3. Artifacts are coherent with claimed outcomes.
4. Protected-kernel disclosure review passed for outward-facing changes.
5. Human acceptance review confirms usability and clarity.

## Documentation Update Discipline

External/operator-facing docs may be updated only when:

- behavior is implemented and validated, or
- docs explicitly state current unsupported boundary.

Never document speculative capability as available.

## Branch and Reporting Discipline

Every sprint/hotfix report must include:

- current branch,
- head commit,
- pushed branch,
- branch contains HEAD confirmation,
- local validation results,
- live validation status (performed vs pending).

## State Labels

Use explicit state labels:

- `implemented`
- `local_validated`
- `live_validated`
- `accepted`

Do not collapse these labels into a single "done" state.
